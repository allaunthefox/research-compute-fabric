use super::features::{FeatureVector, WorkloadClass};
use super::config::AnalysisConfig;
use realfft::{RealFftPlanner, RealToComplex};
use smallvec::SmallVec;
use std::collections::VecDeque;

pub struct DSPSurface {
    config: AnalysisConfig,
    fft: std::sync::Arc<dyn RealToComplex<f32>>,
    fft_scratch: Vec<std::num::Complex<f32>>,
    fft_buffer: Vec<f32>,
    window: Vec<f32>,
    history: VecDeque<SmallVec<[f32; 512]>>,
    spectral_buf: Vec<f32>,
    last_features: Option<FeatureVector>,
    compression_threshold: f32,
}

impl DSPSurface {
    pub fn new(config: AnalysisConfig) -> Self {
        let mut planner = RealFftPlanner::<f32>::new();
        let fft = planner.plan_fft_forward(config.fft_size);
        let fft_scratch = fft.make_scratch_vec();
        let fft_buffer = fft.make_input_vec();

        // Hann window for spectral leakage reduction
        let window: Vec<f32> = (0..config.fft_size)
            .map(|i| {
                0.5 * (1.0 - (2.0 * std::f32::consts::PI * i as f32 
                    / config.fft_size as f32).cos())
            })
            .collect();

        let compression_threshold = config.compression_threshold.unwrap_or(0.0);

        Self {
            config,
            fft,
            fft_scratch,
            fft_buffer,
            window,
            history: VecDeque::with_capacity(config.history_depth),
            spectral_buf: vec![0.0f32; config.fft_size / 2],
            last_features: None,
            compression_threshold,
        }
    }

    /// Process audio chunk, return features and workload classification
    pub fn process(&mut self, input: &[f32], timestamp_us: u64) -> FeatureVector {
        let n = input.len().min(self.config.fft_size);

        // Windowed FFT input
        self.fft_buffer.fill(0.0);
        for i in 0..n {
            self.fft_buffer[i] = input[i] * self.window[i];
        }

        // Execute FFT
        let mut spectrum = self.fft.make_output_vec();
        self.fft.process_with_scratch(&mut self.fft_buffer, &mut spectrum, &mut self.fft_scratch)
            .expect("FFT processing failed");

        // Extract spectral features (first N bins aggregated)
        let bin_width = spectrum.len() / self.config.spectral_bins;
        let mut spectral = SmallVec::with_capacity(self.config.spectral_bins);

        for i in 0..self.config.spectral_bins {
            let start = i * bin_width;
            let end = (i + 1) * bin_width;
            let energy: f32 = spectrum[start..end].iter().map(|c| c.norm()).sum();
            spectral.push(energy / bin_width as f32);
        }

        // Normalize spectral vector
        let max_val = spectral.iter().fold(0.0f32, |a, &b| a.max(b));
        if max_val > 0.0 {
            spectral.iter_mut().for_each(|v| *v /= max_val);
        }

        // Transient analysis
        let transient = if self.config.enable_transient {
            self.extract_transient(input)
        } else {
            SmallVec::new()
        };

        // Information metrics
        let information = if self.config.enable_information {
            self.extract_information(input)
        } else {
            SmallVec::new()
        };

        // Classification
        let _workload = self.classify(&spectral, &transient, &information);

        // Update history for predictability calculation
        if self.history.len() >= self.config.history_depth {
            self.history.pop_front();
        }
        let mut hist_copy: SmallVec<[f32; 512]> = SmallVec::new();
        hist_copy.extend_from_slice(&input[..n.min(512)]);
        self.history.push_back(hist_copy);

        // Optional binary mask for sparse representation
        let mask: Option<SmallVec<[bool; 16]>> = if self.compression_threshold > 0.0 {
            Some(spectral.iter().map(|&v| v > self.compression_threshold).collect())
        } else {
            None
        };

        FeatureVector {
            timestamp_us,
            spectral,
            transient,
            information,
            mask,
        }
    }

    fn extract_transient(&self, samples: &[f32]) -> SmallVec<[f32; 4]> {
        if samples.len() < 2 { return SmallVec::new(); }

        let mut attack = 0.0f32;
        let mut decay = 0.0f32;
        let mut zcr = 0usize;
        let mut peak = 0.0f32;
        let mut sum_sq = 0.0f32;

        for i in 0..samples.len()-1 {
            let curr = samples[i];
            let next = samples[i+1];
            let delta = next - curr;

            if delta > attack { attack = delta; }
            if -delta > decay { decay = -delta; }
            if (curr >= 0.0) != (next >= 0.0) { zcr += 1; }

            let abs = curr.abs();
            if abs > peak { peak = abs; }
            sum_sq += curr * curr;
        }

        let rms = (sum_sq / samples.len() as f32).sqrt().max(1e-10);
        let crest = peak / rms;

        let mut tv = SmallVec::new();
        tv.push(attack);
        tv.push(decay);
        tv.push(zcr as f32 / samples.len() as f32);
        tv.push(crest);
        tv
    }

    fn extract_information(&self, samples: &[f32]) -> SmallVec<[f32; 3]> {
        // Spectral entropy approximation
        let mean = self.spectral_buf.iter().sum::<f32>() / self.spectral_buf.len().max(1) as f32;
        let variance = if mean > 0.0 {
            self.spectral_buf.iter()
                .map(|&x| (x - mean).powi(2))
                .sum::<f32>() / self.spectral_buf.len() as f32
        } else { 0.0 };

        // Temporal variance
        let temp_var = samples.windows(2)
            .map(|w| (w[1] - w[0]).powi(2))
            .sum::<f32>() / samples.len().max(1) as f32;

        // Predictability via autocorrelation
        let predictability = if let Some(prev) = self.history.back() {
            let len = samples.len().min(prev.len()).min(256);
            let mut num = 0.0f32;
            let mut den_x = 0.0f32;
            let mut den_y = 0.0f32;

            let mean_x = samples[..len].iter().sum::<f32>() / len as f32;
            let mean_y = prev[..len].iter().sum::<f32>() / len as f32;

            for i in 0..len {
                let dx = samples[i] - mean_x;
                let dy = prev[i] - mean_y;
                num += dx * dy;
                den_x += dx * dx;
                den_y += dy * dy;
            }

            let den = (den_x * den_y).sqrt();
            if den > 0.0 { (num / den + 1.0) * 0.5 } else { 0.5 }
        } else {
            0.5
        };

        let mut info = SmallVec::new();
        info.push(variance.sqrt().min(1.0));
        info.push(temp_var.sqrt());
        info.push(predictability);
        info
    }

    fn classify(&self, spectral: &[f32], transient: &SmallVec<[f32; 4]>, 
                info: &SmallVec<[f32; 3]>) -> WorkloadClass {
        if spectral.is_empty() { return WorkloadClass::Silent; }

        let spectral_energy: f32 = spectral.iter().sum();
        let transient_peak = if transient.len() >= 2 {
            transient[0].max(transient[1])
        } else { 0.0 };

        let entropy = info.get(0).copied().unwrap_or(0.0);

        if spectral_energy < 0.001 {
            WorkloadClass::Silent
        } else if transient_peak > 0.3 && spectral_energy > 0.1 {
            WorkloadClass::TransientEdge
        } else if entropy > 0.7 {
            WorkloadClass::Raw
        } else if spectral_energy > transient_peak * 2.0 {
            WorkloadClass::SpectralFocus
        } else {
            WorkloadClass::Hybrid
        }
    }

    /// Check if current features are similar to last (for compression)
    pub fn is_similar(&self, current: &FeatureVector) -> bool {
        if let Some(ref last) = self.last_features {
            // Cosine similarity on spectral vector
            let dot: f32 = current.spectral.iter().zip(last.spectral.iter())
                .map(|(a, b)| a * b).sum();
            let norm_a: f32 = current.spectral.iter().map(|v| v*v).sum::<f32>().sqrt();
            let norm_b: f32 = last.spectral.iter().map(|v| v*v).sum::<f32>().sqrt();

            if norm_a > 0.0 && norm_b > 0.0 {
                let similarity = dot / (norm_a * norm_b);
                return similarity > self.compression_threshold;
            }
        }
        false
    }
}

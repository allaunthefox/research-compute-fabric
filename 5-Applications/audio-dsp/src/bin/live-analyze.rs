use clap::Parser;
use chunked_audio_dsp::core::{Config, DSPSurface, StreamingConfig};
use chunked_audio_dsp::io::{PipeWireInput, JsonlSink};
use chunked_audio_dsp::pipeline::StreamingPipeline;
use std::path::PathBuf;

#[derive(Parser)]
struct Args {
    #[arg(short, long)]
    config: Option<PathBuf>,

    #[arg(short, long, default_value = "signal-surface")]
    name: String,
}

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    let args = Args::parse();

    let config = Config::load(args.config.as_ref())?;

    println!("Starting real-time analysis: {}", args.name);
    println!("Sample rate: {} Hz", config.streaming.sample_rate);
    println!("Chunk size: {} samples", config.streaming.chunk_size);

    let input = PipeWireInput::new(&args.name, &config)?;
    let sink = JsonlSink;
    let dsp = DSPSurface::new(config.analysis.clone());

    let pipeline = StreamingPipeline::new(input, sink, dsp, config.streaming);
    pipeline.run()?;

    Ok(())
}

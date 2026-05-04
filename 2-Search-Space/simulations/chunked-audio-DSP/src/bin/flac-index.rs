use clap::Parser;
use chunked_audio_dsp::core::{Config, DSPSurface};
use chunked_audio_dsp::io::{FlacInput, BinarySink};
use chunked_audio_dsp::pipeline::ChunkedPipeline;
use std::path::PathBuf;

#[derive(Parser)]
struct Args {
    /// Input FLAC file
    input: PathBuf,

    /// Output binary file
    #[arg(short, long)]
    output: PathBuf,

    /// Config file
    #[arg(short, long)]
    config: Option<PathBuf>,

    /// Output format
    #[arg(short, long, default_value = "binary")]
    format: String,
}

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    let args = Args::parse();

    let config = Config::load(args.config.as_ref())?;

    println!("Indexing: {:?} -> {:?}", args.input, args.output);

    let mut input = FlacInput::open(&args.input)?;
    let mut sink = BinarySink::new(&args.output)?;
    let mut dsp = DSPSurface::new(config.analysis.clone());

    ChunkedPipeline::process_file(
        &mut input,
        &mut sink,
        &mut dsp,
        &config.streaming,
        None,
    )?;

    println!("Analysis complete");
    Ok(())
}

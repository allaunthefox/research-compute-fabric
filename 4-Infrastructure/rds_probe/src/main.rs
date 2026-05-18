mod commands;
mod db;
mod models;

use clap::Parser;

#[derive(Parser, Debug)]
#[command(name = "rds_probe")]
#[command(about = "RDS ENE database inspection tool", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: commands::Command,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenv::dotenv().ok();
    
    match commands::run_command(Cli::parse().command).await {
        Ok(output) => {
            println!("{}", output);
            Ok(())
        }
        Err(e) => {
            eprintln!("Error: {}", e);
            Err(e.into())
        }
    }
}

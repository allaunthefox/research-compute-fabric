// Notion Native — Tauri wrapper for Notion Web
// Multi-threaded tokio runtime + GPU-accelerated WebView

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, WebviewUrl};

#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Compression backend health check (runs on thread pool)
            tokio::spawn(async {
                let compressor = compression_core::default_compressor();
                let test = b"notion-native-tauri warmup";
                let compressed = compressor.compress(test);
                let _ = compressor.decompress(&compressed);
            });

            // Background prefetch on thread pool
            tokio::spawn(async {
                let _ = reqwest::get("https://www.notion.so").await;
            });

            let window = app.get_webview_window("main").unwrap();
            window.navigate(WebviewUrl::External(
                "https://www.notion.so".parse().unwrap(),
            ));
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

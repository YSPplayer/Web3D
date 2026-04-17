use serde::Serialize;

#[derive(Serialize)]
struct PingPayload {
    app: &'static str,
    message: String,
}

#[tauri::command]
fn ping_rust() -> PingPayload {
    PingPayload {
        app: "Rust bridge online",
        message: "Tauri command channel is ready. You can keep Filament rendering in the frontend and move heavy logic into Rust later.".to_string(),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![ping_rust])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

mod commands;
mod config;
mod sidecar;
mod state;

fn main() {
    tauri::Builder::default()
        .manage(state::AppState::default())
        .invoke_handler(tauri::generate_handler![
            commands::get_bootstrap_config,
            commands::get_sidecar_process_state
        ])
        .run(tauri::generate_context!())
        .expect("error while running driver app");
}

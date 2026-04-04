#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod config;
mod sidecar;
mod debug_dump;

use crate::config::{load_config, AppConfig};
use crate::sidecar::SidecarManager;
use std::sync::Mutex;
use tauri::{Manager, RunEvent};

fn main() {
    let app = tauri::Builder::default()
        .manage(Mutex::new(AppConfig::default()))
        .manage(Mutex::new(SidecarManager::new()))
        .invoke_handler(tauri::generate_handler![
            commands::get_bootstrap_config,
            commands::update_app_config,
            commands::get_app_config,
            commands::get_sidecar_process_state,
            commands::start_sidecar,
            commands::stop_sidecar,
            commands::restart_sidecar
        ])
        .build(tauri::generate_context!())
        .expect("error while building driver app");


    let app_handle = app.handle().clone();
    let loaded = load_config(&app_handle);

    {
        let state = app_handle.state::<Mutex<AppConfig>>();
        let mut config = state.lock().unwrap();
        *config = loaded;
    }


    app.run(|app_handle, event| {
        if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
            let sidecar_state = app_handle.state::<Mutex<SidecarManager>>();

            {
                let mut manager = sidecar_state.lock().unwrap();
                let _ = manager.stop();
            }
        }
    });
}
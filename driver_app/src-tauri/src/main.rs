#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod config;
mod sidecar;

use crate::sidecar::SidecarManager;
use std::sync::Mutex;

fn main() {
    tauri::Builder::default()
        .manage(Mutex::new(SidecarManager::new()))
        .invoke_handler(tauri::generate_handler![
            commands::get_bootstrap_config,
            commands::get_sidecar_process_state,
            commands::start_sidecar,
            commands::stop_sidecar,
            commands::restart_sidecar
        ])
        .run(tauri::generate_context!())
        .expect("error while running driver app");
}

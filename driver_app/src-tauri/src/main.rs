#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod config;
mod driver_logging;
mod sidecar;

use crate::config::{load_config, AppConfig};
use crate::sidecar::{sync_manager_config, SidecarManager};
use std::sync::Mutex;
use tauri::{Manager, RunEvent};

fn main() {
    eprintln!("Driver app starting.");

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
    let _ = crate::driver_logging::init_logging(&app_handle);
    crate::driver_logging::log_info("Driver app built successfully.");

    let loaded = load_config(&app_handle);
    crate::driver_logging::log_info(&format!(
        "Loaded app config. sidecar_executable_path={} backend_port={}",
        loaded.sidecar_executable_path, loaded.backend_port
    ));

    {
        let state = app_handle.state::<Mutex<AppConfig>>();
        let mut config = state.lock().unwrap();
        *config = loaded;
    }

    {
        let sidecar_state = app_handle.state::<Mutex<SidecarManager>>();
        let config_state = app_handle.state::<Mutex<AppConfig>>();

        let mut manager = sidecar_state.lock().unwrap();
        if let Err(err) = sync_manager_config(&mut manager, &config_state) {
            crate::driver_logging::log_error(&format!(
                "Failed to sync sidecar manager config: {err}"
            ));
        } else {
            crate::driver_logging::log_info("Synchronized sidecar manager config.");
        }

        match manager.start() {
            Ok(()) => {
                crate::driver_logging::log_info("Sidecar autostart requested successfully.");
            }
            Err(err) => {
                crate::driver_logging::log_error(&format!(
                    "Sidecar autostart failed: {err}"
                ));
            }
        }
    }

    app.run(|app_handle, event| {
        if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
            crate::driver_logging::log_info("Driver app exit requested. Stopping sidecar.");

            let sidecar_state = app_handle.state::<Mutex<SidecarManager>>();

            {
                let mut manager = sidecar_state.lock().unwrap();
                match manager.stop() {
                    Ok(()) => {
                        crate::driver_logging::log_info("Sidecar stopped during app shutdown.");
                    }
                    Err(err) => {
                        crate::driver_logging::log_error(&format!(
                            "Failed to stop sidecar during shutdown: {err}"
                        ));
                    }
                }
            }
        }
    });
}
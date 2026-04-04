use crate::driver_logging::{log_error, log_info};
use crate::config::{save_config, AppConfig, AppConfigUpdate, BootstrapConfig};
use crate::sidecar::{SidecarManager, SidecarProcessState};
use std::sync::Mutex;
use tauri::{AppHandle, State};


#[tauri::command]
pub fn get_bootstrap_config(
    config: State<'_, Mutex<AppConfig>>,
) -> Result<BootstrapConfig, String> {
    let config = config.lock().map_err(|e| e.to_string())?;

    Ok(BootstrapConfig {
        backend_base_url: format!("http://127.0.0.1:{}", config.backend_port),
        backend_websocket_url: format!("ws://127.0.0.1:{}/ws", config.backend_port),
        mode: "tauri".to_string(),
    })
}

#[tauri::command]
pub fn get_sidecar_process_state(
    sidecar: State<'_, Mutex<SidecarManager>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    manager.get_state()
}

#[tauri::command]
pub fn start_sidecar(
    sidecar: State<'_, Mutex<SidecarManager>>,
    config: State<'_, Mutex<AppConfig>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    crate::sidecar::sync_manager_config(&mut manager, &config)?;
    log_info("Start sidecar command received.");
    manager.start()?;
    manager.get_state()
}

#[tauri::command]
pub fn stop_sidecar(
    sidecar: State<'_, Mutex<SidecarManager>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    log_info("Stop sidecar command received.");
    manager.stop()?;
    manager.get_state()
}

#[tauri::command]
pub fn restart_sidecar(
    sidecar: State<'_, Mutex<SidecarManager>>,
    config: State<'_, Mutex<AppConfig>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    crate::sidecar::sync_manager_config(&mut manager, &config)?;
    log_info("Restart sidecar command received.");
    manager.restart()?;
    manager.get_state()
}

#[tauri::command]
pub fn update_app_config(
    update: AppConfigUpdate,
    app: AppHandle,
    config: State<'_, Mutex<AppConfig>>,
) -> Result<AppConfig, String> {
    let mut config = config.lock().map_err(|e| e.to_string())?;
    config.sidecar_executable_path = "sidecars/live_telemetry_sidecar/dist/live-telemetry-sidecar.exe".to_string();
    config.backend_port = update.backend_port;

    let updated = config.clone();
    if let Err(err) = save_config(&app, &updated) {
        log_error(&format!("Failed to save updated app config: {err}"));
        return Err(err);
    }

    log_info("Updated app config via command.");
    Ok(updated)
}

#[tauri::command]
pub fn get_app_config(
    config: State<'_, Mutex<AppConfig>>,
) -> Result<AppConfig, String> {
    let config = config.lock().map_err(|e| e.to_string())?;
    Ok(config.clone())
}

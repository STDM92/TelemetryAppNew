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
    manager.start()?;
    manager.get_state()
}

#[tauri::command]
pub fn stop_sidecar(
    sidecar: State<'_, Mutex<SidecarManager>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
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
    config.python_command = update.python_command;
    config.backend_port = update.backend_port;
    config.backend_mode = update.backend_mode;
    config.backend_file_path = update.backend_file_path;

    let updated = config.clone();
    save_config(&app, &updated)?;

    Ok(updated)
}

#[tauri::command]
pub fn get_app_config(
    config: State<'_, Mutex<AppConfig>>,
) -> Result<AppConfig, String> {
    let config = config.lock().map_err(|e| e.to_string())?;
    Ok(config.clone())
}

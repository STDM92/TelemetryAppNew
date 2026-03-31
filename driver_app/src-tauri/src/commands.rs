use crate::config::BootstrapConfig;
use crate::sidecar::{SidecarManager, SidecarProcessState};
use std::sync::Mutex;
use tauri::State;

#[tauri::command]
pub fn get_bootstrap_config() -> BootstrapConfig {
    BootstrapConfig {
        backend_base_url: "http://127.0.0.1:8000".to_string(),
        backend_websocket_url: "ws://127.0.0.1:8000/ws".to_string(),
        mode: "tauri".to_string(),
    }
}

#[tauri::command]
pub fn get_sidecar_process_state(
    sidecar: State<'_, Mutex<SidecarManager>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    Ok(manager.get_state())
}

#[tauri::command]
pub fn start_sidecar(
    sidecar: State<'_, Mutex<SidecarManager>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    manager.start()?;
    Ok(manager.get_state())
}

#[tauri::command]
pub fn stop_sidecar(
    sidecar: State<'_, Mutex<SidecarManager>>,
) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    manager.stop()?;
    Ok(manager.get_state())
}

#[tauri::command]
pub fn restart_sidecar(sidecar: State<'_, Mutex<SidecarManager>>) -> Result<SidecarProcessState, String> {
    let mut manager = sidecar.lock().map_err(|e| e.to_string())?;
    manager.restart()?;
    Ok(manager.get_state())
}

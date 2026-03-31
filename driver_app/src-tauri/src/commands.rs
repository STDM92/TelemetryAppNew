use crate::config::BootstrapConfig;
use crate::state::{AppState, SidecarProcessState};
use tauri::State;

#[tauri::command]
pub fn get_bootstrap_config() -> BootstrapConfig {
    BootstrapConfig::default()
}

#[tauri::command]
pub fn get_sidecar_process_state(state: State<'_, AppState>) -> SidecarProcessState {
    state.sidecar_process_state.clone()
}

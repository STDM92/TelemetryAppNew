use serde::Serialize;
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct SidecarProcessState {
    pub is_running: bool,
    pub pid: Option<u32>,
    pub exit_code: Option<i32>,
}

#[derive(Default)]
pub struct AppState {
    pub sidecar_process_state: SidecarProcessState,
    pub _lock: Mutex<()>,
}

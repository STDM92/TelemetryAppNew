use serde::Serialize;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SidecarProcessStatus {
    NotRunning,
    Running,
    Exited,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SidecarProcessState {
    pub status: SidecarProcessStatus,
    pub pid: Option<u32>,
    pub exit_code: Option<i32>,
    pub last_error: Option<String>,
}

pub struct SidecarManager {
    child: Option<Child>,
    last_exit_code: Option<i32>,
    last_error: Option<String>,
}

impl SidecarManager {
    pub fn new() -> Self {
        Self {
            child: None,
            last_exit_code: None,
            last_error: None,
        }
    }

    pub fn get_state(&mut self) -> SidecarProcessState {
        self.refresh_child_state();

        match self.child.as_mut() {
            Some(child) => SidecarProcessState {
                status: SidecarProcessStatus::Running,
                pid: Some(child.id()),
                exit_code: None,
                last_error: self.last_error.clone(),
            },
            None => {
                let status = if self.last_exit_code.is_some() {
                    SidecarProcessStatus::Exited
                } else {
                    SidecarProcessStatus::NotRunning
                };

                SidecarProcessState {
                    status,
                    pid: None,
                    exit_code: self.last_exit_code,
                    last_error: self.last_error.clone(),
                }
            }
        }
    }

    pub fn start(&mut self) -> Result<(), String> {
        self.refresh_child_state();

        if self.child.is_some() {
            return Ok(());
        }

        let repo_root = resolve_repo_root()?;

        let mut command = Command::new("python");
        command
            .current_dir(&repo_root)
            .arg("-m")
            .arg("sidecar.backend.engine")
            .arg("--mode")
            .arg("live")
            .arg("--port")
            .arg("8000")
            .stdout(Stdio::null())
            .stderr(Stdio::null());

        let child = command
            .spawn()
            .map_err(|e| format!("Failed to start sidecar: {e}"))?;

        self.last_exit_code = None;
        self.last_error = None;
        self.child = Some(child);
        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), String> {
        self.refresh_child_state();

        let Some(mut child) = self.child.take() else {
            return Ok(());
        };

        child
            .kill()
            .map_err(|e| format!("Failed to stop sidecar: {e}"))?;

        let status = child
            .wait()
            .map_err(|e| format!("Failed to wait for sidecar exit: {e}"))?;

        self.last_exit_code = status.code();
        Ok(())
    }

    pub fn restart(&mut self) -> Result<(), String> {
        self.stop()?;
        self.start()
    }

    fn refresh_child_state(&mut self) {
        let Some(child) = self.child.as_mut() else {
            return;
        };

        match child.try_wait() {
            Ok(Some(status)) => {
                self.last_exit_code = status.code();
                self.child = None;
            }
            Ok(None) => {}
            Err(e) => {
                self.last_error = Some(format!("Failed to query sidecar state: {e}"));
            }
        }
    }
}

fn resolve_repo_root() -> Result<PathBuf, String> {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest_dir
        .parent()
        .and_then(|p| p.parent())
        .map(PathBuf::from)
        .ok_or_else(|| "Failed to resolve repository root from src-tauri.".to_string())
}

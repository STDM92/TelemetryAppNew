use crate::driver_logging::{log_error, log_info, log_warn};
use crate::config::AppConfig;
use serde::Serialize;
use std::collections::VecDeque;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;

//activate the venv via "source .venv/bin/activate"

const OUTPUT_TAIL_CAPACITY: usize = 200;


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
    pub last_exit_reason: Option<String>,
    pub stdout_tail: Vec<String>,
    pub stderr_tail: Vec<String>,
}



pub struct SidecarManager {
    config: AppConfig,
    child: Option<Child>,
    last_exit_code: Option<i32>,
    last_exit_reason: Option<String>,
    last_error: Option<String>,
    stop_requested: bool,
    stdout_tail: Arc<Mutex<VecDeque<String>>>,
    stderr_tail: Arc<Mutex<VecDeque<String>>>,
}

impl SidecarManager {
    pub fn new() -> Self {
        Self {
            config: AppConfig::default(),
            child: None,
            last_exit_code: None,
            last_exit_reason: None,
            last_error: None,
            stop_requested: false,
            stdout_tail: Arc::new(Mutex::new(VecDeque::with_capacity(OUTPUT_TAIL_CAPACITY))),
            stderr_tail: Arc::new(Mutex::new(VecDeque::with_capacity(OUTPUT_TAIL_CAPACITY))),
        }
    }

    pub fn get_state(&mut self) -> Result<SidecarProcessState, String> {
        self.refresh_child_state();

        let state = match self.child.as_mut() {
            Some(child) => SidecarProcessState {
                status: SidecarProcessStatus::Running,
                pid: Some(child.id()),
                exit_code: None,
                last_error: self.last_error.clone(),
                last_exit_reason: self.last_exit_reason.clone(),
                stdout_tail: clone_tail(&self.stdout_tail),
                stderr_tail: clone_tail(&self.stderr_tail),
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
                    last_exit_reason: self.last_exit_reason.clone(),
                    stdout_tail: clone_tail(&self.stdout_tail),
                    stderr_tail: clone_tail(&self.stderr_tail),
                }
            }
        };

        Ok(state)
    }

    pub fn start(&mut self) -> Result<(), String> {
        self.refresh_child_state();

        if self.child.is_some() {
            return Ok(());
        }

        let repo_root = resolve_repo_root()?;
        let executable_path =
            resolve_sidecar_executable_path(&repo_root, &self.config.sidecar_executable_path)?;
        log_info(&format!(
            "Starting sidecar executable. path={} port={}",
            executable_path.display(), self.config.backend_port
        ));

        let mut command = Command::new(&executable_path);
        command
            .current_dir(&repo_root)
            .arg("--port")
            .arg(self.config.backend_port.to_string())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        clear_tail(&self.stdout_tail);
        clear_tail(&self.stderr_tail);

        let mut child = command
            .spawn()
            .map_err(|e| {
                let message = format!("Failed to start sidecar: {e}");
                self.last_error = Some(message.clone());
                log_error(&message);
                message
            })?;

        if let Some(stdout) = child.stdout.take() {
            spawn_output_reader(stdout, Arc::clone(&self.stdout_tail));
        }

        if let Some(stderr) = child.stderr.take() {
            spawn_output_reader(stderr, Arc::clone(&self.stderr_tail));
        }

        log_info(&format!("Sidecar process spawned successfully. pid={}", child.id()));

        self.last_exit_code = None;
        self.last_exit_reason = None;
        self.last_error = None;
        self.stop_requested = false;
        self.child = Some(child);
        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), String> {
        self.refresh_child_state();

        let Some(mut child) = self.child.take() else {
            return Ok(());
        };

        self.stop_requested = true;
        log_info("Stopping sidecar process.");

        child
            .kill()
            .map_err(|e| format!("Failed to stop sidecar: {e}"))?;

        let status = child
            .wait()
            .map_err(|e| format!("Failed to wait for sidecar exit: {e}"))?;

        self.last_exit_code = status.code();
        self.last_exit_reason = Some("stopped_by_driver_app".to_string());
        log_info(&format!(
            "Sidecar process stopped. exit_code={:?} reason=stopped_by_driver_app",
            self.last_exit_code
        ));
        Ok(())
    }

    pub fn restart(&mut self) -> Result<(), String> {
        self.stop()?;
        self.start()
    }

    pub fn update_config(&mut self, config: AppConfig) {
        self.config = config;
    }

    fn refresh_child_state(&mut self) {
        let Some(child) = self.child.as_mut() else {
            return;
        };

        match child.try_wait() {
            Ok(Some(status)) => {
                self.last_exit_code = status.code();
                self.last_exit_reason = Some(if self.stop_requested {
                    "stopped_by_driver_app".to_string()
                } else {
                    "sidecar_exited_unexpectedly".to_string()
                });
                if self.stop_requested {
                    log_info(&format!("Observed sidecar exit after stop request. exit_code={:?}", self.last_exit_code));
                } else {
                    log_warn(&format!(
                        "Observed unexpected sidecar exit. exit_code={:?}",
                        self.last_exit_code
                    ));
                }
                self.stop_requested = false;
                self.child = None;
            }
            Ok(None) => {}
            Err(e) => {
                self.last_error = Some(format!("Failed to query sidecar state: {e}"));
            }
        }
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        let _ = self.stop();
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

fn resolve_sidecar_executable_path(repo_root: &PathBuf, configured_path: &str) -> Result<PathBuf, String> {
    let candidate = PathBuf::from(configured_path);

    let resolved = if candidate.is_absolute() {
        candidate
    } else {
        repo_root.join(candidate)
    };

    if !resolved.is_file() {
        return Err(format!("Configured sidecar executable does not exist: {}", resolved.display()));
    }

    Ok(resolved)
}



pub fn sync_manager_config(
    manager: &mut SidecarManager,
    config: &Mutex<AppConfig>,
) -> Result<(), String> {
    let config = config.lock().map_err(|e| e.to_string())?;
    manager.update_config(config.clone());
    Ok(())
}

fn spawn_output_reader<R>(reader: R, tail: Arc<Mutex<VecDeque<String>>>)
where
    R: std::io::Read + Send + 'static,
{
    thread::spawn(move || {
        let buffered = BufReader::new(reader);

        for line in buffered.lines() {
            match line {
                Ok(line) => {
                    if should_capture_tail_line(&line) {
                        push_tail_line(&tail, line);
                    }
                }
                Err(err) => {
                    push_tail_line(&tail, format!("<output read error: {err}>"));
                    break;
                }
            }
        }
    });
}

fn should_capture_tail_line(line: &str) -> bool {
    let trimmed = line.trim();

    if trimmed.is_empty() {
        return false;
    }

    if trimmed.contains("uvicorn.access")
        && (trimmed.contains("GET /status")
            || trimmed.contains("GET /api/state")
            || trimmed.contains("GET /health"))
    {
        return false;
    }

    true
}

fn push_tail_line(tail: &Arc<Mutex<VecDeque<String>>>, line: String) {
    let mut guard = tail.lock().unwrap_or_else(|poisoned| poisoned.into_inner());

    if guard.len() >= OUTPUT_TAIL_CAPACITY {
        guard.pop_front();
    }

    guard.push_back(line);
}

fn clear_tail(tail: &Arc<Mutex<VecDeque<String>>>) {
    let mut guard = tail.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
    guard.clear();
}

fn clone_tail(tail: &Arc<Mutex<VecDeque<String>>>) -> Vec<String> {
    let guard = tail.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
    guard.iter().cloned().collect()
}

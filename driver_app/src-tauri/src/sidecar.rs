use std::path::PathBuf;
use std::process::{Child, Command, Stdio};

pub fn launch_sidecar(python_exe: &str, repo_root: PathBuf) -> std::io::Result<Child> {
    let backend_path = repo_root.join("backend").join("engine.py");

    Command::new(python_exe)
        .arg(backend_path)
        .arg("--mode")
        .arg("live")
        .arg("--port")
        .arg("8000")
        .current_dir(repo_root)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
}

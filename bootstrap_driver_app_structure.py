#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

FILES = {
    "driver_app/.gitignore": "node_modules/\ndist/\nsrc-tauri/target/\n",
    "driver_app/README.md": '''# Driver App

Minimal Tauri-based driver companion app.

Responsibilities:
- start/stop/restart the local Python sidecar
- show sidecar/runtime/session status
- host the local dashboard UI in a webview
- later: driver confirmation overlays for remote proposals

This app should remain a thin shell, not the telemetry authority.
''',
    "driver_app/package.json": '''{
  "name": "driver-app",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  }
}
''',
    "driver_app/vite.config.ts": '''import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 1420,
    strictPort: true
  }
});
''',
    "driver_app/tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "react-jsx",
    "types": []
  },
  "include": ["src"]
}
''',
    "driver_app/src/main.ts": '''import { getBootstrapConfig } from "./app/api/bootstrap";

async function main() {
  const app = document.getElementById("app");
  if (!app) return;

  const config = await getBootstrapConfig();

  app.innerHTML = `
    <main style="font-family: system-ui, sans-serif; padding: 24px; color: white; background: #111; min-height: 100vh;">
      <h1 style="margin-top: 0;">Driver App</h1>
      <p>Minimal driver shell placeholder.</p>
      <pre style="padding: 12px; background: #1b1b1b; border-radius: 8px;">${JSON.stringify(config, null, 2)}</pre>
    </main>
  `;
}

main().catch((err) => {
  console.error("Driver app startup failed:", err);
});
''',
    "driver_app/src/app/api/bootstrap.ts": '''export type BootstrapConfig = {
  localBackendBaseUrl: string;
  localBackendWebSocketUrl: string;
  environment: "development" | "production";
};

export async function getBootstrapConfig(): Promise<BootstrapConfig> {
  return {
    localBackendBaseUrl: "http://127.0.0.1:8000",
    localBackendWebSocketUrl: "ws://127.0.0.1:8000/ws",
    environment: "development"
  };
}
''',
    "driver_app/src/app/shell/.gitkeep": "",
    "driver_app/src/app/dashboard/.gitkeep": "",
    "driver_app/src/app/diagnostics/.gitkeep": "",
    "driver_app/src/app/api/.gitkeep": "",
    "driver_app/src/types/.gitkeep": "",
    "driver_app/src/styles/.gitkeep": "",
    "driver_app/src/index.html": '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Driver App</title>
    <script type="module" src="/main.ts"></script>
  </head>
  <body style="margin: 0;">
    <div id="app"></div>
  </body>
</html>
''',
    "driver_app/src-tauri/Cargo.toml": '''[package]
name = "driver_app"
version = "0.1.0"
edition = "2021"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tauri = { version = "2", features = [] }
''',
    "driver_app/src-tauri/build.rs": '''fn main() {
    tauri_build::build()
}
''',
    "driver_app/src-tauri/tauri.conf.json": '''{
  "$schema": "../node_modules/@tauri-apps/cli/config.schema.json",
  "productName": "Driver App",
  "version": "0.1.0",
  "identifier": "com.example.driverapp",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:1420"
  },
  "app": {
    "windows": [
      {
        "title": "Driver App",
        "width": 1200,
        "height": 800,
        "resizable": true
      }
    ]
  },
  "bundle": {
    "active": false
  }
}
''',
    "driver_app/src-tauri/src/main.rs": '''mod commands;
mod config;
mod sidecar;
mod state;

fn main() {
    tauri::Builder::default()
        .manage(state::AppState::default())
        .invoke_handler(tauri::generate_handler![
            commands::get_bootstrap_config,
            commands::get_sidecar_process_state
        ])
        .run(tauri::generate_context!())
        .expect("error while running driver app");
}
''',
    "driver_app/src-tauri/src/commands.rs": '''use crate::config::BootstrapConfig;
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
''',
    "driver_app/src-tauri/src/config.rs": '''use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BootstrapConfig {
    pub local_backend_base_url: String,
    pub local_backend_web_socket_url: String,
    pub environment: String,
}

impl Default for BootstrapConfig {
    fn default() -> Self {
        Self {
            local_backend_base_url: "http://127.0.0.1:8000".to_string(),
            local_backend_web_socket_url: "ws://127.0.0.1:8000/ws".to_string(),
            environment: "development".to_string(),
        }
    }
}
''',
    "driver_app/src-tauri/src/sidecar.rs": '''use std::path::PathBuf;
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
''',
    "driver_app/src-tauri/src/state.rs": '''use serde::Serialize;
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
''',
    "shared_frontend/README.md": '''Optional future shared frontend package.

Do not move code here until you actually have:
- a real engineer web app
- enough duplication to justify extraction
''',
    "shared_frontend/src/.gitkeep": "",
    "shared_frontend/package.json": '''{
  "name": "shared-frontend",
  "private": true,
  "version": "0.1.0"
}
''',
}

def write_file(path: Path, content: str, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        print(f"SKIP  {path} (already exists)")
        return
    path.write_text(content, encoding="utf-8")
    print(f"WRITE {path}")

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bootstrap driver app structure.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repo root. Defaults to current directory.")
    parser.add_argument("--include-shared-frontend", action="store_true", help="Also create the optional shared_frontend folder.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files created by this script.")
    return parser.parse_args(argv)

def main(argv=None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()

    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 1

    selected = dict(FILES)
    if not args.include_shared_frontend:
        selected = {k: v for k, v in selected.items() if not k.startswith("shared_frontend/")}

    for relative_path, content in selected.items():
        write_file(root / relative_path, content, force=args.force)

    print("\nDone.")
    print(f"Repo root: {root}")
    print("Next steps:")
    print("  1. Open the repo in RustRover.")
    print("  2. Run `npm install` inside driver_app/.")
    print("  3. Initialize Tauri CLI if needed and align tauri.conf.json.")
    print("  4. Wire the frontend bootstrap config to real Tauri commands.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

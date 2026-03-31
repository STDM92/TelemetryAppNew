use serde::Serialize;

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

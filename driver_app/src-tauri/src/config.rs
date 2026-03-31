use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BootstrapConfig {
    pub backend_base_url: String,
    pub backend_websocket_url: String,
    pub mode: String,
}

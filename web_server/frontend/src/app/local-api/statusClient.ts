export type BackendStatus = {
  status: "created" | "running" | "stopped" | "failed" | string;
  last_error?: string | null;
  source_attachment_state?: "none" | "waiting" | "attached" | string | null;
  stream_state?: "failed" | "idle" | "stale" | "streaming" | string | null;
  has_received_snapshot?: boolean;
  last_snapshot_at?: number | null;
  sim?: string | null;
  source_kind?: string | null;
  source_display_name?: string | null;
};

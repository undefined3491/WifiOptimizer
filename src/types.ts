export interface PluginSettings {
  model: string;
  driver: string;
  device_family: string;
  device_label: string;
  chip_label: string;
  supports_6ghz: boolean;
  power_save_disabled: boolean;
  auto_fix_on_wake: boolean;
  bssid_lock_enabled: boolean;
  bssid_lock_value: string;
  bssid_lock_connection_uuid: string;
  band_preference: string;
  band_preference_enabled: boolean;
  dns_provider: string;
  dns_servers: string;
  dns_enabled: boolean;
  ipv6_disabled: boolean;
  buffer_tuning_enabled: boolean;
  cake_enabled: boolean;
  distro_id: string;
  distro_name: string;
  last_connection_uuid: string;
  priority_set: boolean;
  last_applied: number;
}

export interface BackendServiceState {
  active: string;
  enabled: string;
}

export interface LiveStatus {
  power_save_off?: boolean;
  signal_dbm?: string;
  tx_bitrate?: string;
  frequency?: string;
  channel?: string;
  connected_bssid?: string;
  bssid_lock?: string;
  ip_address?: string;
  dns?: string;
  ipv6_method?: string;
  band?: string;
  buffer_tuning_applied?: boolean;
  cake_applied?: boolean;
  dispatcher_installed?: boolean;
  last_enforced?: number;
  wifi_backend?: string;
  backend_tool_available?: boolean;
  // ST0-009 D6: configured (desired) vs services-ground-truth (effective)
  // backend. "unknown" on the wire when unreadable. backend_services maps
  // each backend to its {active, enabled} systemctl states.
  backend_desired?: string;
  backend_effective?: string;
  backend_services?: Record<string, BackendServiceState>;
}

export interface PluginStatus {
  success: boolean;
  connected: boolean;
  support_tier: number;
  version?: string;
  settings: PluginSettings;
  live: LiveStatus;
  drift: Record<string, boolean>;
  unknown_owners?: string[];
  // D2: read-only single-job update summary (observation only, no writes).
  update_job?: UpdateJobSummary;
  last_applied?: number;
  error?: string;
  message?: string;
}

export interface ReconnectStage {
  ok: boolean;
  stderr: string;
}

export interface ReconnectDetail {
  attempted: boolean;
  skipped?: "offline" | "foreign_owner";
  stages?: Record<string, ReconnectStage | null>;
  verified?: boolean;
  active_uuid_after?: string | null;
  radio_off_without_on?: boolean;
}

export interface RelockDetail {
  attempted: boolean;
  ok: boolean;
  bssid?: string;
  detail?: string;
}

export interface MethodResult {
  success: boolean;
  error?: string;
  message?: string;
  detail?: string;
  reconnected?: boolean;
  reconnect?: ReconnectDetail;
  relock?: RelockDetail;
  errors?: string[];
  transfer_warnings?: string[];
  [key: string]: unknown;
}

export interface OptimizeSafeResult extends MethodResult {
  total: number;
  applied: number;
  results: Record<string, MethodResult>;
  did_reconnect?: boolean;
}

export type BackendSwitchPhase =
  | "idle"
  | "switching"
  | "reconnecting"
  | "done"
  | "failed";

export interface BackendSwitchResult {
  success: boolean;
  backend?: string | null;
  target: string;
  recovery_performed?: boolean;
  needs_reboot?: boolean;
  reconnect_timed_out?: boolean;
  message?: string;
  detail?: string;
  // ST0-009 D5: same-target retry context (null when not a repair),
  // whether a failed repair rolled back to the previous backend, and
  // additive step codes (backend_stop/disable/enable/start_failed,
  // nm_restart_failed, effective_mismatch).
  repair_of?: string | null;
  rolled_back?: boolean;
  errors?: string[];
}

export interface BackendSwitchStatus {
  success: boolean;
  in_progress: boolean;
  phase: BackendSwitchPhase;
  target: string | null;
  started_at: number;
  result: BackendSwitchResult | null;
  message?: string;
  error?: string;
}

export interface BackendSwitchStartResult {
  accepted: boolean;
  reason?: string;
  message?: string;
  target?: string;
  from?: string | null;
  backend?: string;
  // ST0-009 D2: true when the same-target start was accepted as repair of
  // a diverged backend (rather than a fresh switch).
  repair?: boolean;
}

export interface UpdateCheckResult {
  success: boolean;
  current_version?: string;
  latest_version?: string;
  update_available?: boolean;
  missing_files?: string[];
  release_url?: string;
  errors?: string[];
  error?: string;
  message?: string;
}

export interface UpdateFileCommit {
  committed: boolean;
  version: string;
  channel: string;
  files: string;
}

export interface UpdateRestartReport {
  requested: boolean;
  rc: number | null;
  stderr: string;
}

export interface UpdateJobResult {
  target: string;
  errors: string[];
  file_commit: UpdateFileCommit;
  restart: UpdateRestartReport;
  health: string;
}

export interface UpdateJobSummary {
  in_progress: boolean;
  phase: string;
  target: string | null;
  started_at: number;
  result: UpdateJobResult | null;
}

export interface UpdateStartResult {
  accepted: boolean;
  target?: string;
  reason?: string;
  job_id?: number;
}

export type BadgeStatus = "active" | "locked" | "set" | "drifted" | "off" | "error" | "unknown";

export const ERROR_MESSAGES: Record<string, string> = {
  no_wifi: "Not connected to WiFi. Connect first, then optimize.",
  iw_failed: "Couldn't change WiFi setting. Try toggling WiFi off/on.",
  nmcli_failed: "Couldn't update connection. Forget and reconnect to this network.",
  dns_partial: "DNS was only partly applied. The previous DNS was restored; try again.",
  relock_failed: "Band changed but the AP lock couldn't be re-applied. Try again on this network.",
  unknown_owner: "Setting is enabled but its network profile is unknown. Re-apply on the desired network.",
  sysctl_failed: "Couldn't apply kernel network settings. Try again.",
  txqueuelen_failed: "Couldn't set transmit queue length. Try again.",
  qdisc_failed: "Couldn't configure traffic shaping. Try again.",
  dispatcher_failed: "Couldn't install the auto-fix script. The filesystem may be locked.",
  modprobe_failed: "Couldn't write driver configuration. Try again.",
  sysfs_failed: "Couldn't apply driver power settings. Try again.",
  pcie_failed: "Couldn't configure PCIe power management. Try again.",
  nm_conf_failed: "Couldn't write NetworkManager configuration. Try again.",
  timeout: "Command timed out. The system may be busy. Try again.",
  backend_stop_failed: "Couldn't stop the current WiFi backend. Try again.",
  backend_disable_failed: "Couldn't disable the current WiFi backend. Try again.",
  backend_enable_failed: "Couldn't enable the new WiFi backend. Try again.",
  backend_start_failed: "The new WiFi backend failed to start. Try again, or reboot if it keeps failing.",
  nm_restart_failed: "Couldn't restart NetworkManager after the switch. Try again.",
  effective_mismatch: "The backend switch didn't take effect. Try again, or reboot if it keeps failing.",
  write_failed: "Couldn't install auto-fix script. The filesystem may be locked.",
  parse_error: "Settings were reset to defaults.",
  unexpected: "Something went wrong. Check the Decky log for details.",
};

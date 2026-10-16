const manifest = {"name":"WiFi Optimizer TMS"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const callable = api.callable;
const definePlugin = (fn) => {
    return (...args) => {
        return fn(...args);
    };
};

var DefaultContext = {
  color: undefined,
  size: undefined,
  className: undefined,
  style: undefined,
  attr: undefined
};
var IconContext = SP_REACT.createContext && /*#__PURE__*/SP_REACT.createContext(DefaultContext);

var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(e, t) { if (null == e) return {}; var o, r, i = _objectWithoutPropertiesLoose(e, t); if (Object.getOwnPropertySymbols) { var n = Object.getOwnPropertySymbols(e); for (r = 0; r < n.length; r++) o = n[r], -1 === t.indexOf(o) && {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]); } return i; }
function _objectWithoutPropertiesLoose(r, e) { if (null == r) return {}; var t = {}; for (var n in r) if ({}.hasOwnProperty.call(r, n)) { if (-1 !== e.indexOf(n)) continue; t[n] = r[n]; } return t; }
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), true).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: true, configurable: true, writable: true }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /*#__PURE__*/SP_REACT.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return props => /*#__PURE__*/SP_REACT.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = conf => {
    var {
        attr,
        size,
        title
      } = props,
      svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /*#__PURE__*/SP_REACT.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className: className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /*#__PURE__*/SP_REACT.createElement("title", null, title), props.children);
  };
  return IconContext !== undefined ? /*#__PURE__*/SP_REACT.createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
}

// THIS FILE IS AUTO GENERATED
function FaWifi (props) {
  return GenIcon({"attr":{"viewBox":"0 0 640 512"},"child":[{"tag":"path","attr":{"d":"M634.91 154.88C457.74-8.99 182.19-8.93 5.09 154.88c-6.66 6.16-6.79 16.59-.35 22.98l34.24 33.97c6.14 6.1 16.02 6.23 22.4.38 145.92-133.68 371.3-133.71 517.25 0 6.38 5.85 16.26 5.71 22.4-.38l34.24-33.97c6.43-6.39 6.3-16.82-.36-22.98zM320 352c-35.35 0-64 28.65-64 64s28.65 64 64 64 64-28.65 64-64-28.65-64-64-64zm202.67-83.59c-115.26-101.93-290.21-101.82-405.34 0-6.9 6.1-7.12 16.69-.57 23.15l34.44 33.99c6 5.92 15.66 6.32 22.05.8 83.95-72.57 209.74-72.41 293.49 0 6.39 5.52 16.05 5.13 22.05-.8l34.44-33.99c6.56-6.46 6.33-17.06-.56-23.15z"},"child":[]}]})(props);
}

const getStatus = callable("get_status");
const setPowerSave = callable("set_power_save");
const setAutoFix = callable("set_auto_fix");
const setBssidLock = callable("set_bssid_lock");
const setBandPreference = callable("set_band_preference");
const setDns = callable("set_dns");
const setIpv6 = callable("set_ipv6");
const setBufferTuning = callable("set_buffer_tuning");
const setCake = callable("set_cake");
const optimizeSafe = callable("optimize_safe");
const reapplyAll = callable("reapply_all");
const reapplyVolatile = callable("reapply_volatile");
const resetSettings = callable("reset_settings");
const setUpdateChannel = callable("set_update_channel");
const checkForUpdate = callable("check_for_update");
const applyUpdate = callable("apply_update");
const startBackendSwitch = callable("start_backend_switch");
const getBackendSwitchStatus = callable("get_backend_switch_status");
const getDiagnosticInfo = callable("get_diagnostic_info");
const saveDiagnosticInfo = callable("save_diagnostic_info");

const ERROR_MESSAGES = {
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

// Design tokens for the WiFi Optimizer TMS panel. Keep this in sync with the
// palette used in the README mockup and the four semantic banner colors
// (success/warning/error/info) that Decky's Quick Access Menu supports well
// against its dark background.
const theme = {
    // Status colors - used for banners, badges, and text callouts.
    // Each family has text (solid), bg (panel background at ~8% alpha),
    // badgeBg (chip/pill background at ~15% alpha), and border (~20% alpha).
    success: {
        text: "#3fc56e",
        bg: "rgba(29,158,117,0.08)",
        badgeBg: "rgba(29,158,117,0.15)",
        border: "rgba(29,158,117,0.2)",
    },
    warning: {
        text: "#ffc669",
        bg: "rgba(223,138,0,0.08)",
        badgeBg: "rgba(223,138,0,0.15)",
        border: "rgba(223,138,0,0.2)",
    },
    error: {
        text: "#ff878c",
        bg: "rgba(211,36,43,0.08)",
        badgeBg: "rgba(211,36,43,0.15)",
        border: "rgba(211,36,43,0.2)",
    },
    info: {
        text: "#60baff",
        bg: "rgba(55,138,221,0.08)",
        border: "rgba(55,138,221,0.2)",
        accentBg: "rgba(55,138,221,0.2)",
    },
    // Neutral text scale, lightest to darkest.
    text: {
        primary: "#e0e0e0",
        secondary: "#9a9aaa",
        tertiary: "#8a8a9a",
        subtitle: "#7a7a8a",
        muted: "#6a6a7a",
        dim: "#4a4a5a",
    },
    // White-alpha surfaces used for layered backgrounds.
    surface: {
        xs: "rgba(255,255,255,0.02)",
        sm: "rgba(255,255,255,0.04)",
        md: "rgba(255,255,255,0.06)",
        lg: "rgba(255,255,255,0.08)",
    },
    // Consistent sizing tokens reused across the panel.
    radius: {
        sm: "4px",
        md: "6px",
        lg: "8px",
        pill: "10px",
    },
    fontSize: {
        label: "9px",
        tiny: "10px",
        small: "11px",
        body: "12px",
        heading: "13px",
        icon: "14px",
    },
};

const BADGE_STYLES = {
    active: { background: theme.success.badgeBg, color: theme.success.text },
    locked: { background: theme.success.badgeBg, color: theme.success.text },
    set: { background: theme.success.badgeBg, color: theme.success.text },
    drifted: { background: theme.warning.badgeBg, color: theme.warning.text },
    off: { background: theme.surface.md, color: theme.text.muted },
    error: { background: theme.error.badgeBg, color: theme.error.text },
    unknown: { background: theme.surface.md, color: theme.text.tertiary },
};
function StatusBadge({ badge, text }) {
    const style = BADGE_STYLES[badge];
    return (SP_JSX.jsx("span", { style: {
            fontSize: theme.fontSize.small,
            padding: "2px 6px",
            borderRadius: theme.radius.sm,
            whiteSpace: "nowrap",
            background: style.background,
            color: style.color,
        }, children: text }));
}

function InfoRow({ label, subtitle, explanation, badge, text, checked, disabled = false, error, onChange, children, }) {
    const showBadge = badge !== undefined && text !== undefined;
    const [expanded, setExpanded] = SP_REACT.useState(false);
    return (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ToggleField, { label: SP_JSX.jsxs("span", { style: { display: "flex", alignItems: "center", gap: "4px" }, children: [SP_JSX.jsx("span", { onClick: (e) => {
                                    e.stopPropagation();
                                    setExpanded(!expanded);
                                }, style: {
                                    display: "inline-flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    width: "16px",
                                    height: "16px",
                                    borderRadius: "50%",
                                    background: expanded ? theme.info.accentBg : theme.surface.lg,
                                    color: expanded ? theme.info.text : theme.text.tertiary,
                                    fontSize: theme.fontSize.tiny,
                                    fontWeight: 700,
                                    cursor: "pointer",
                                    flexShrink: 0,
                                }, children: "i" }), SP_JSX.jsx("span", { children: label })] }), description: SP_JSX.jsxs("span", { style: { display: "block" }, children: [showBadge && (SP_JSX.jsx("span", { style: {
                                    display: "flex",
                                    justifyContent: "flex-end",
                                    marginBottom: "4px",
                                }, children: SP_JSX.jsx(StatusBadge, { badge: badge, text: text }) })), error ? (SP_JSX.jsx("span", { style: { color: theme.error.text }, children: error })) : (SP_JSX.jsx("span", { style: { color: theme.text.subtitle, fontSize: theme.fontSize.small }, children: subtitle }))] }), checked: checked, disabled: disabled, onChange: onChange }) }), expanded && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: {
                        padding: "8px 12px",
                        background: theme.surface.xs,
                        borderRadius: theme.radius.md,
                        fontSize: theme.fontSize.small,
                        lineHeight: "1.5",
                        color: theme.text.secondary,
                    }, children: explanation }) })), children] }));
}

function signalColor(dbm) {
    if (!dbm)
        return theme.text.muted;
    const val = parseInt(dbm);
    if (isNaN(val))
        return theme.text.muted;
    if (val > -50)
        return theme.success.text;
    if (val > -70)
        return theme.text.primary;
    if (val > -80)
        return theme.warning.text;
    return theme.error.text;
}
function bandLabel(freqStr) {
    if (!freqStr)
        return "--";
    const mhz = parseInt(freqStr);
    if (isNaN(mhz))
        return freqStr;
    if (mhz < 3000)
        return "2.4 GHz";
    if (mhz < 5925)
        return "5 GHz";
    return "6 GHz";
}
function bandColor(freqStr) {
    if (!freqStr)
        return theme.text.muted;
    const mhz = parseInt(freqStr);
    if (isNaN(mhz))
        return theme.text.primary;
    if (mhz < 3000)
        return theme.warning.text; // 2.4 GHz (suboptimal)
    return theme.success.text; // 5/6 GHz (good)
}
function StatsGrid({ live, connected }) {
    const na = "--";
    const signal = connected ? live.signal_dbm ?? na : na;
    const speed = connected ? live.tx_bitrate ?? na : na;
    const band = connected ? bandLabel(live.frequency) : na;
    const freq = connected ? live.frequency ?? "" : "";
    const channel = connected ? live.channel ?? na : na;
    const cell = {
        background: theme.surface.sm,
        borderRadius: theme.radius.sm,
        padding: "4px 8px",
    };
    const lbl = {
        fontSize: theme.fontSize.label,
        color: theme.text.muted,
        textTransform: "uppercase",
        letterSpacing: "0.5px",
    };
    const val = (color) => ({
        fontSize: theme.fontSize.heading,
        fontWeight: 500,
        color: connected ? color : theme.text.muted,
    });
    return (SP_JSX.jsxs(DFL.Focusable, { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px" }, children: [SP_JSX.jsxs("div", { style: cell, children: [SP_JSX.jsx("div", { style: lbl, children: "Signal" }), SP_JSX.jsx("div", { style: val(signalColor(live.signal_dbm)), children: signal })] }), SP_JSX.jsxs("div", { style: cell, children: [SP_JSX.jsx("div", { style: lbl, children: "Speed" }), SP_JSX.jsx("div", { style: val(theme.text.primary), children: speed })] }), SP_JSX.jsxs("div", { style: cell, children: [SP_JSX.jsx("div", { style: lbl, children: "Band" }), SP_JSX.jsx("div", { style: val(bandColor(live.frequency)), children: band }), freq && (SP_JSX.jsxs("div", { style: { fontSize: theme.fontSize.label, color: theme.text.muted }, children: [freq, " MHz"] }))] }), SP_JSX.jsxs("div", { style: cell, children: [SP_JSX.jsx("div", { style: lbl, children: "Channel" }), SP_JSX.jsx("div", { style: val(theme.text.primary), children: channel })] })] }));
}

// Shared banner styling for the panel's many inline notifications
// (unknown hardware, drift alert, optimize result, backend switch
// result, update errors, etc.). Each banner sits in its own
// PanelSection so Decky's QAM can focus it with gamepad navigation.
function Banner({ variant, icon, children }) {
    const palette = theme[variant];
    return (SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: {
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "8px 12px",
                    background: palette.bg,
                    border: `0.5px solid ${palette.border}`,
                    borderRadius: theme.radius.lg,
                    fontSize: theme.fontSize.body,
                    color: palette.text,
                    width: "100%",
                    boxSizing: "border-box",
                }, children: [icon !== undefined && (SP_JSX.jsx("span", { style: { fontSize: theme.fontSize.icon }, children: icon })), SP_JSX.jsx("span", { children: children })] }) }) }));
}

const PHASE_TEXT = {
    idle: "",
    switching: "Switching backend…",
    reconnecting: "Reconnecting…",
    done: "",
    failed: "",
};
const EXPLANATION = "Your system defaults to iwd for WiFi management. Some devices see " +
    "disconnects after sleep, 5 GHz dropouts, or 'invalid password' errors " +
    "with iwd. Switching to wpa_supplicant trades slightly slower reconnect " +
    "(about 5s vs 1-2s) for broader compatibility and better stability on " +
    "certain routers. The setting survives reboots and OS updates. On some " +
    "devices, the switch may briefly disrupt the WiFi interface - the plugin " +
    "handles recovery automatically, but a reboot is needed as a last resort. " +
    "Note: some networks (WPA3-only, certain enterprise setups) behave " +
    "differently between backends - if your WiFi stops connecting after a " +
    "switch, try switching back.";
function BackendToggleRow({ status, backendSwitch, error, isBusy, onToggle, onRetry, }) {
    // Desired vs effective (ST0-009 D7): config and reality are never
    // conflated, and "" never silently defaults to iwd — unknown is an
    // explicit branch (including when the backend tool is unavailable).
    const toolAvailable = status.live?.backend_tool_available !== false;
    const wiredDesired = status.live?.backend_desired;
    const desired = toolAvailable && wiredDesired && wiredDesired !== "unknown"
        ? wiredDesired
        : toolAvailable && status.live?.wifi_backend
            ? status.live.wifi_backend
            : null;
    const wiredEffective = status.live?.backend_effective;
    const effective = toolAvailable && wiredEffective && wiredEffective !== "unknown"
        ? wiredEffective
        : null;
    const diverged = desired !== null && effective !== null && desired !== effective;
    const unknownEffective = desired !== null && effective === null;
    const retryTarget = desired === "wpa_supplicant"
        ? "wpa_supplicant"
        : desired === "iwd"
            ? "iwd"
            : null;
    const isWpa = desired === "wpa_supplicant";
    const switching = backendSwitch?.in_progress ?? false;
    // Optimistic: during a switch, reflect the target so the toggle matches
    // the user's click until the operation completes. On failure, it snaps
    // back to the actual backend. A same-target retry never takes the
    // optimistic position: the toggle already sits at the desired value, so
    // the row stays put until effective confirms the repair.
    const retryInFlight = switching &&
        backendSwitch?.target != null &&
        backendSwitch.target === desired;
    const checked = !retryInFlight && switching && backendSwitch?.target
        ? backendSwitch.target === "wpa_supplicant"
        : isWpa;
    const phaseText = switching
        ? PHASE_TEXT[backendSwitch.phase] || "Working…"
        : null;
    const baseSubtitle = diverged
        ? `Configured ${desired} · effective ${effective} — switch didn't take effect`
        : unknownEffective
            ? `Configured ${desired} · effective unknown`
            : "Alternate WiFi backend - can fix sleep/wake and stability issues";
    const badge = error
        ? { badge: "error", text: "failed" }
        : switching
            ? { badge: "unknown", text: "…" }
            : desired === null
                ? { badge: "unknown", text: "unknown" }
                : isWpa
                    ? { badge: "active", text: "wpa_supplicant" }
                    : { badge: "off", text: "iwd" };
    // Inline result shown right under the toggle so it's visible where the
    // user clicked - the top-of-panel banner is often off-screen when the
    // user is scrolled down to the Advanced section.
    const lastResult = !switching && !error && backendSwitch?.result && !backendSwitch.result.needs_reboot
        ? backendSwitch.result
        : null;
    return (SP_JSX.jsxs(InfoRow, { label: "Use wpa_supplicant backend", subtitle: phaseText ?? baseSubtitle, explanation: EXPLANATION, badge: badge.badge, text: badge.text, checked: checked, disabled: switching || isBusy, error: error, onChange: onToggle, children: [retryTarget !== null && (diverged || unknownEffective) && !switching && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: isBusy, onClick: () => onRetry(retryTarget), children: `Retry switch to ${retryTarget}` }) })), lastResult?.success && (() => {
                const timedOut = lastResult.reconnect_timed_out;
                const parts = [`Switched to ${lastResult.backend}`];
                if (lastResult.recovery_performed)
                    parts.push("wlan0 interface recreated");
                if (timedOut)
                    parts.push("WiFi didn't reconnect");
                return (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: {
                            fontSize: theme.fontSize.small,
                            color: timedOut ? theme.warning.text : theme.success.text,
                            padding: "2px 0",
                        }, children: [timedOut ? "⚠" : "✓", " ", parts.join(" · ")] }) }));
            })()] }));
}

const CHANNEL_OPTIONS = [
    { data: "stable", label: "Stable" },
    { data: "beta", label: "Beta" },
];
// The Updates panel section: channel selector, optional warning text for a
// stuck / failed update, and a button that context-switches between
// "Updating...", "Update Now", "Up to date", and "Check for Updates"
// depending on state.
function UpdatesSection({ channel, updating, checkingUpdate, updateInfo, updateError, onChannelChange, onApply, onCheck, }) {
    return (SP_JSX.jsxs(DFL.PanelSection, { title: "Updates", children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.DropdownItem, { label: "Update channel", rgOptions: CHANNEL_OPTIONS, selectedOption: channel, onChange: (option) => onChannelChange(option.data) }) }), updateError && !updating && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { fontSize: theme.fontSize.body, color: theme.warning.text }, children: ["\u26A0 ", updateError] }) })), updating ? (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { fontSize: theme.fontSize.body, color: theme.info.text }, children: "Updating... plugin will restart momentarily." }) })) : updateInfo?.update_available ? (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { fontSize: theme.fontSize.body, color: theme.success.text }, children: ["v", updateInfo.latest_version, " available (you have v", updateInfo.current_version, ")"] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: onApply, children: "Update Now" }) })] })) : (SP_JSX.jsxs(SP_JSX.Fragment, { children: [updateInfo && updateInfo.success === false && updateInfo.message && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { fontSize: theme.fontSize.tiny, color: theme.error.text }, children: updateInfo.message }) })), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: checkingUpdate, onClick: onCheck, children: checkingUpdate
                                ? "Checking..."
                                : updateInfo?.success && !updateInfo?.update_available
                                    ? "Up to date"
                                    : "Check for Updates" }) })] }))] }));
}

// Format a Unix-seconds timestamp as a relative-time string for display in
// the panel header ("just now", "5 min ago", "2 hr ago", "3d ago"). Returns
// "never" for the sentinel value 0 (settings not yet applied).
function timeAgo(ts) {
    if (!ts)
        return "never";
    const diff = Math.floor(Date.now() / 1000) - ts;
    if (diff < 60)
        return "just now";
    if (diff < 3600)
        return `${Math.floor(diff / 60)} min ago`;
    if (diff < 86400)
        return `${Math.floor(diff / 3600)} hr ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

function PanelHeader({ driver, version, lastApplied, lastEnforced, deviceLabel, }) {
    const modelLabel = deviceLabel && deviceLabel !== "unknown"
        ? deviceLabel
        : driver && driver !== "unknown"
            ? driver
            : "Unrecognized hardware";
    const rowStyle = {
        fontSize: theme.fontSize.tiny,
        color: theme.text.muted,
    };
    return (SP_JSX.jsxs(DFL.PanelSection, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("span", { style: {
                        fontSize: theme.fontSize.tiny,
                        background: theme.surface.md,
                        padding: "2px 8px",
                        borderRadius: theme.radius.pill,
                        color: theme.text.tertiary,
                    }, children: ["Device: ", modelLabel] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: rowStyle, children: ["Version: ", version] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: rowStyle, children: "Tap (i) on any toggle for details" }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: rowStyle, children: ["Last changed: ", timeAgo(lastApplied), lastEnforced ? (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx("br", {}), "Auto-applied: ", timeAgo(lastEnforced)] })) : ("")] }) })] }));
}

function PanelFooter({ version }) {
    const [diagState, setDiagState] = SP_REACT.useState("idle");
    const rowStyle = {
        fontSize: theme.fontSize.tiny,
        color: theme.text.dim,
    };
    const handleCopyDiagnostics = async () => {
        setDiagState("copying");
        try {
            const info = await getDiagnosticInfo();
            // Check the collection success flag before reporting done/saved.
            if (!info || info.success === false) {
                throw new Error("diagnostic collection failed");
            }
            const text = JSON.stringify(info, null, 2);
            try {
                await navigator.clipboard.writeText(text);
                setDiagState("done");
            }
            catch {
                const saved = await saveDiagnosticInfo();
                // Check the save success flag before reporting saved.
                if (!saved || saved.success === false) {
                    throw new Error("diagnostic save failed");
                }
                setDiagState("saved");
            }
            setTimeout(() => setDiagState("idle"), 5000);
        }
        catch {
            setDiagState("error");
            setTimeout(() => setDiagState("idle"), 3000);
        }
    };
    const label = diagState === "done"
        ? "Copied to clipboard"
        : diagState === "saved"
            ? "Saved to plugin settings folder"
            : diagState === "error"
                ? "Failed to collect diagnostics"
                : diagState === "copying"
                    ? "Collecting..."
                    : "Copy diagnostics";
    return (SP_JSX.jsxs(DFL.PanelSection, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: rowStyle, children: ["v", version, " - by jasonridesabike"] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: rowStyle, children: ["If WiFi won't reconnect, a reboot usually fixes it.", SP_JSX.jsx("br", {}), "Bugs? Report at github.com/undefined3491/wifi-optimizer-tms"] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: diagState === "copying", onClick: handleCopyDiagnostics, children: label }) })] }));
}

function ActionsSection({ connected, isBusy, onForceReapply, onReset, }) {
    return (SP_JSX.jsxs(DFL.PanelSection, { title: "Actions", children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: !connected || isBusy, onClick: onForceReapply, children: "Force Reapply All" }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: isBusy, onClick: onReset, children: "Reset Settings" }) })] }));
}

const REFRESH_INTERVAL = 3000;
const RECONNECT_DELAY = 4000;
const BACKEND_POLL_INTERVAL = 750;
const UPDATE_CHECK_INTERVAL = 5 * 60 * 1000;
const UPDATE_CHECK_DEDUPE_MS = 60 * 1000;
const UPDATE_TIMEOUT_MS = 60 * 1000;
function getBadge(driftKey, status, errorKey) {
    // Only surface a badge when it tells the user something the toggle position
    // doesn't - failure or drift between our setting and the system state.
    // Binary on/off badges are redundant with the toggle itself and are hidden.
    if (errorKey)
        return { badge: "error", text: "failed" };
    if (driftKey && status?.drift?.[driftKey])
        return { badge: "drifted", text: "drifted" };
    return null;
}
const DNS_OPTIONS = [
    { data: "cloudflare", label: "Cloudflare (1.1.1.1)" },
    { data: "google", label: "Google (8.8.8.8)" },
    { data: "quad9", label: "Quad9 (9.9.9.9)" },
    { data: "custom", label: "Custom" },
];
// Catches render-time exceptions in the panel tree so a bad status shape or
// other unexpected error surfaces a recoverable message instead of Decky
// blanking the panel. The child tree is re-entered on next mount (panel
// reopen), so users can recover without a plugin restart.
class ErrorBoundary extends SP_REACT.Component {
    constructor() {
        super(...arguments);
        this.state = { err: null };
    }
    static getDerivedStateFromError(err) {
        return { err };
    }
    componentDidCatch(err, info) {
        console.error("WiFi Optimizer TMS render error:", err, info);
    }
    render() {
        if (this.state.err) {
            return (SP_JSX.jsx(Banner, { variant: "error", children: "WiFi Optimizer TMS hit an unexpected error. Close and reopen the panel to recover. If it keeps happening, please report at github.com/undefined3491/wifi-optimizer-tms." }));
        }
        return this.props.children;
    }
}
// The single component that owns all panel state. It's intentionally flat:
// every section reads from shared state and state setters are passed down to
// leaf components. Organized top-to-bottom as:
//   1. State and refs
//   2. Stable callbacks (setBusy, runUpdateCheck, refreshStatus, poll helpers)
//   3. Lifecycle effects (main refresh, init, connectivity retry, update timeout,
//      update heartbeat)
//   4. User action handlers (toggles, optimize, reset, backend switch, updates)
//   5. Derived render state (connected, supportTier, allSafeActive, etc.)
//   6. JSX for the panel sections in top-to-bottom screen order
function Content() {
    // --- General status and toggle state ---
    const [status, setStatus] = SP_REACT.useState(null);
    const [errors, setErrors] = SP_REACT.useState({});
    const [isBusy, setIsBusy] = SP_REACT.useState(false);
    const [applyingAll, setApplyingAll] = SP_REACT.useState(false);
    const [optimizeResult, setOptimizeResult] = SP_REACT.useState(null);
    const [customDnsInput, setCustomDnsInput] = SP_REACT.useState("");
    // Visible action outcomes: rejections land in actionError; transfer
    // warnings, setter errors[] and reset errors[] land in actionWarnings.
    const [actionError, setActionError] = SP_REACT.useState(null);
    const [actionWarnings, setActionWarnings] = SP_REACT.useState(null);
    // Status fetch health: last known status is kept and labeled stale
    // instead of being poisoned or presented as fresh.
    const [statusError, setStatusError] = SP_REACT.useState(null);
    const [isStale, setIsStale] = SP_REACT.useState(false);
    const [statusAt, setStatusAt] = SP_REACT.useState(0);
    // --- Update flow state ---
    const [updateInfo, setUpdateInfo] = SP_REACT.useState(null);
    const [checkingUpdate, setCheckingUpdate] = SP_REACT.useState(false);
    const [updating, setUpdating] = SP_REACT.useState(false);
    const [updateError, setUpdateError] = SP_REACT.useState(null);
    // --- Backend switch state ---
    const [backendSwitch, setBackendSwitch] = SP_REACT.useState(null);
    // --- Refs ---
    // busyRef is the synchronous re-entrancy guard; isBusy (above) is the React
    // state mirror so UI can respond. setBusy below writes both together.
    const busyRef = SP_REACT.useRef(false);
    const backendPollRef = SP_REACT.useRef(null);
    const prevConnectedRef = SP_REACT.useRef(null);
    const statusRef = SP_REACT.useRef(null);
    const lastUpdateCheckAtRef = SP_REACT.useRef(0);
    const setBusy = SP_REACT.useCallback((val) => {
        busyRef.current = val;
        setIsBusy(val);
    }, []);
    // Runs checkForUpdate with dedupe - skips if a check was issued within the
    // dedupe window. Lowers GitHub API pressure in CGNAT/dorm scenarios where
    // many devices share an IP. Manual button bypasses this (force=true).
    const runUpdateCheck = SP_REACT.useCallback((force = false) => {
        const now = Date.now();
        if (!force && now - lastUpdateCheckAtRef.current < UPDATE_CHECK_DEDUPE_MS) {
            return;
        }
        lastUpdateCheckAtRef.current = now;
        checkForUpdate().then((r) => {
            setUpdateInfo(r);
            if (r && !r.success) {
                setUpdateError(r.message ?? "Couldn't check for updates.");
            }
            else {
                setUpdateError(null);
            }
        }).catch(() => {
            setUpdateError("Couldn't check for updates.");
        });
    }, []);
    const refreshStatus = SP_REACT.useCallback(async (force = false) => {
        // Background interval ticks defer while a user operation is in flight;
        // handler-driven refreshes (at the end of an op) force through so the UI
        // catches up immediately instead of waiting for the next interval tick.
        if (!force && busyRef.current)
            return;
        try {
            const s = await getStatus();
            if (s && s.success !== false) {
                statusRef.current = s;
                setStatus(s);
                setStatusError(null);
                setIsStale(false);
                setStatusAt(Date.now());
                if (s.settings) {
                    if (s.settings.dns_provider === "custom") {
                        setCustomDnsInput(s.settings.dns_servers || "");
                    }
                }
            }
            else {
                // Resolved failure: keep last known status, label it stale.
                setStatusError(s?.message ?? "Couldn't load status.");
                if (statusRef.current)
                    setIsStale(true);
            }
        }
        catch (e) {
            console.error("WiFi Optimizer TMS: failed to get status", e);
            setStatusError("Couldn't reach the plugin. It may still be loading.");
            if (statusRef.current)
                setIsStale(true);
        }
    }, []);
    const stopBackendPoll = () => {
        if (backendPollRef.current) {
            clearInterval(backendPollRef.current);
            backendPollRef.current = null;
        }
    };
    const beginBackendPoll = SP_REACT.useCallback(() => {
        stopBackendPoll();
        backendPollRef.current = setInterval(async () => {
            try {
                const s = await getBackendSwitchStatus();
                if (s.in_progress) {
                    // Mid-switch: update so the subtitle can show the current phase.
                    setBackendSwitch(s);
                    return;
                }
                // Terminal. Stop polling, then refresh status BEFORE flipping backend
                // state and clearing busy - this keeps the optimistic toggle position
                // steady until live.wifi_backend has caught up AND keeps other toggles
                // disabled until the whole UI has consistent state, avoiding any
                // toggle/untoggle flicker at the end of the switch.
                stopBackendPoll();
                if (s.result && !s.result.success && s.result.message) {
                    const detail = s.result.detail ? ` (${s.result.detail})` : "";
                    setErrors((prev) => ({
                        ...prev,
                        wifi_backend: s.result.message + detail,
                    }));
                }
                await refreshStatus(true);
                setBackendSwitch(s);
                setBusy(false);
            }
            catch (e) {
                stopBackendPoll();
                setBusy(false);
                console.error("backend switch poll error", e);
                // Poll rejection: clear in-flight state but keep mutation controls
                // locked via an additive error until the next successful
                // getBackendSwitchStatus reconciles (no retry timers).
                setBackendSwitch((prev) => ({
                    success: false,
                    in_progress: false,
                    phase: "failed",
                    target: prev?.target ?? null,
                    started_at: prev?.started_at ?? 0,
                    result: prev?.result ?? null,
                    error: "Lost contact with the backend switch. Reopen the panel or start a new switch.",
                }));
            }
        }, BACKEND_POLL_INTERVAL);
    }, [refreshStatus, setBusy]);
    // Main refresh interval, paused when the panel is hidden so we don't burn
    // CPU/battery on ~12 subprocess calls every 3s in the background. On return
    // to visible, run one refresh immediately to catch anything that changed
    // while hidden, then resume the interval.
    SP_REACT.useEffect(() => {
        let id = null;
        const start = () => {
            if (id)
                return;
            refreshStatus();
            id = setInterval(refreshStatus, REFRESH_INTERVAL);
        };
        const stop = () => {
            if (id) {
                clearInterval(id);
                id = null;
            }
        };
        const onVis = () => {
            if (document.hidden)
                stop();
            else
                start();
        };
        if (!document.hidden)
            start();
        document.addEventListener("visibilitychange", onVis);
        return () => {
            document.removeEventListener("visibilitychange", onVis);
            stop();
        };
    }, [refreshStatus]);
    // One-time init: initial update check and resume backend polling if a switch
    // was already in flight when the panel opened.
    SP_REACT.useEffect(() => {
        // Initial update check. If it fails (e.g., no network yet), the effect
        // below retries on connectivity recovery. QAM tends to cache the panel
        // across close/open, so we can't rely on remount to retry.
        runUpdateCheck();
        // Resume backend-switch polling if one is in flight (panel was reopened mid-switch)
        getBackendSwitchStatus()
            .then((s) => {
            if (s.in_progress) {
                setBackendSwitch(s);
                setBusy(true);
                beginBackendPoll();
            }
            else {
                // Reconcile a prior poll-reject lock once the backend answers.
                setBackendSwitch((prev) => (prev?.error ? s : prev));
            }
        })
            .catch(() => { });
        return () => {
            if (backendPollRef.current)
                clearInterval(backendPollRef.current);
        };
    }, [beginBackendPoll, runUpdateCheck, setBusy]);
    // Retry update check when connectivity recovers. The initial one-shot check
    // in the mount effect misses the case where the panel was already open when
    // the network came back. Skip until status has loaded to avoid a spurious
    // null-to-true transition firing an extra check on every mount.
    SP_REACT.useEffect(() => {
        if (!status)
            return;
        const connected = status.connected;
        const prev = prevConnectedRef.current;
        prevConnectedRef.current = connected;
        if (prev === false && connected === true) {
            runUpdateCheck();
        }
    }, [status?.connected, runUpdateCheck]);
    // Safety timeout: if an update was initiated but plugin_loader hasn't killed
    // us within 60s, the detached update script probably failed (network drop,
    // tarball corruption, etc.). Revert the UI so the user isn't stuck staring
    // at "Updating..." forever, and surface a message they can act on.
    SP_REACT.useEffect(() => {
        if (!updating)
            return;
        const id = setTimeout(() => {
            console.error("WiFi Optimizer TMS: update didn't complete within 60s");
            setUpdating(false);
            setUpdateError("Update didn't complete. Try again, or reinstall manually from Konsole.");
        }, UPDATE_TIMEOUT_MS);
        return () => clearTimeout(id);
    }, [updating]);
    // Periodic update re-check - QAM often caches the panel across close/reopen,
    // so the mount-effect check doesn't re-fire. This heartbeat catches new
    // releases when the panel has been left open for a while. Paused when the
    // panel/tab is hidden to avoid pointless GitHub calls accumulating while the
    // user isn't looking; re-fires one check immediately on visibility return.
    SP_REACT.useEffect(() => {
        let id = null;
        const start = () => {
            if (id)
                return;
            id = setInterval(() => runUpdateCheck(), UPDATE_CHECK_INTERVAL);
        };
        const stop = () => {
            if (id) {
                clearInterval(id);
                id = null;
            }
        };
        const onVis = () => {
            if (document.hidden) {
                stop();
            }
            else {
                runUpdateCheck();
                start();
            }
        };
        if (!document.hidden)
            start();
        document.addEventListener("visibilitychange", onVis);
        return () => {
            document.removeEventListener("visibilitychange", onVis);
            stop();
        };
    }, [runUpdateCheck]);
    // ---- User action handlers ----
    //
    // Generic toggle handler used by every setter toggle (power_save, BSSID,
    // auto_fix, buffer_tuning, band_preference, DNS, IPv6) and by the Force
    // Reapply All button. Takes a key for error tracking and a backend fn.
    const handleToggle = async (key, fn) => {
        if (busyRef.current)
            return;
        setBusy(true);
        setActionError(null);
        setActionWarnings(null);
        setErrors((prev) => {
            const next = { ...prev };
            delete next[key];
            return next;
        });
        setOptimizeResult(null);
        try {
            const result = await fn();
            if (!result.success) {
                const detail = result.detail ? ` (${result.detail})` : "";
                const msg = (result.message ?? ERROR_MESSAGES[result.error ?? ""] ?? "Unknown error") + detail;
                setErrors((prev) => ({ ...prev, [key]: msg }));
            }
            // Lossless results: transfer warnings, per-setter errors[] and an
            // unverified reconnect are bannered, never dropped.
            const warnings = [];
            if (result.transfer_warnings)
                warnings.push(...result.transfer_warnings);
            if (result.errors)
                warnings.push(...result.errors);
            const rc = result.reconnect;
            if (rc?.attempted && !rc.verified) {
                const failed = Object.entries(rc.stages ?? {})
                    .filter(([, st]) => st && !st.ok)
                    .map(([name]) => name);
                warnings.push(`WiFi reconnect not verified${failed.length ? ` (${failed.join(", ")})` : ""}. Settings were saved; toggle WiFi off/on if needed.`);
            }
            if (warnings.length)
                setActionWarnings(warnings);
            // Wait for WiFi to reconnect before refreshing status
            if (result.reconnected) {
                await new Promise((r) => setTimeout(r, RECONNECT_DELAY));
            }
        }
        catch (e) {
            console.error(`WiFi Optimizer TMS: toggle ${key} failed`, e);
            setErrors((prev) => ({ ...prev, [key]: "Request failed. Please try again." }));
        }
        finally {
            // Refresh before clearing busy so toggles/badges don't briefly flip to
            // stale pre-operation values in the interim render. Refresh runs even on
            // unexpected errors to keep UI consistent with backend state.
            await refreshStatus(true);
            setBusy(false);
        }
    };
    const handleOptimize = async () => {
        if (busyRef.current)
            return;
        setBusy(true);
        setApplyingAll(true);
        setErrors({});
        setActionError(null);
        setActionWarnings(null);
        setOptimizeResult(null);
        try {
            const result = await optimizeSafe();
            setOptimizeResult(result);
            if (result.results) {
                const newErrors = {};
                for (const [k, v] of Object.entries(result.results)) {
                    if (!v.success) {
                        const det = v.detail ? ` (${v.detail})` : "";
                        newErrors[k] = (v.message ?? ERROR_MESSAGES[v.error ?? ""] ?? "Failed") + det;
                    }
                }
                setErrors(newErrors);
            }
            // Lossless results (mirrors handleToggle/handleForceReapply):
            // transfer warnings, per-setter errors[] and an unverified
            // reconnect are bannered, never dropped.
            const optWarnings = [];
            for (const v of Object.values(result.results ?? {})) {
                if (v.transfer_warnings)
                    optWarnings.push(...v.transfer_warnings);
                if (v.errors)
                    optWarnings.push(...v.errors);
            }
            const optFailedStages = [];
            let optUnverified = false;
            for (const v of Object.values(result.results ?? {})) {
                const rc = v.reconnect;
                if (rc?.attempted && !rc.verified) {
                    optUnverified = true;
                    for (const [name, st] of Object.entries(rc.stages ?? {})) {
                        if (st && !st.ok)
                            optFailedStages.push(name);
                    }
                }
            }
            if (optUnverified) {
                optWarnings.push(`WiFi reconnect not verified${optFailedStages.length ? ` (${optFailedStages.join(", ")})` : ""}. Settings were saved; toggle WiFi off/on if needed.`);
            }
            if (optWarnings.length)
                setActionWarnings(optWarnings);
            // optimize_safe contains BSSID lock which reconnects
            if (result.reconnected) {
                await new Promise((r) => setTimeout(r, RECONNECT_DELAY));
            }
        }
        catch (e) {
            console.error("optimize error", e);
            setActionError("Couldn't apply optimizations. Please try again.");
        }
        finally {
            // Refresh before clearing applyingAll so button doesn't briefly flip to
            // "All good" from stale status. Refresh runs on errors too.
            await refreshStatus(true);
            setBusy(false);
            setApplyingAll(false);
        }
    };
    // Force Reapply has its own handler (not handleToggle): each failed
    // child maps to its existing errors[child] key, the shared banner shows
    // applied/total/failed, and total==0 renders as info. The old "reapply"
    // error key is retired since no row renders it.
    const handleForceReapply = async () => {
        if (busyRef.current)
            return;
        setBusy(true);
        setActionError(null);
        setActionWarnings(null);
        setOptimizeResult(null);
        try {
            const result = await reapplyAll();
            setOptimizeResult(result);
            const childKeys = Object.keys(result.results ?? {});
            const newErrors = {};
            for (const [k, v] of Object.entries(result.results ?? {})) {
                if (!v.success) {
                    const det = v.detail ? ` (${v.detail})` : "";
                    newErrors[k] = (v.message ?? ERROR_MESSAGES[v.error ?? ""] ?? "Failed") + det;
                }
            }
            setErrors((prev) => {
                const next = { ...prev };
                for (const k of childKeys)
                    delete next[k];
                return { ...next, ...newErrors };
            });
            const warnings = [];
            for (const v of Object.values(result.results ?? {})) {
                if (v.transfer_warnings)
                    warnings.push(...v.transfer_warnings);
                if (v.errors)
                    warnings.push(...v.errors);
            }
            const failedStages = [];
            let anyUnverified = false;
            for (const v of Object.values(result.results ?? {})) {
                const rc = v.reconnect;
                if (rc?.attempted && !rc.verified) {
                    anyUnverified = true;
                    for (const [name, st] of Object.entries(rc.stages ?? {})) {
                        if (st && !st.ok)
                            failedStages.push(name);
                    }
                }
            }
            if (anyUnverified) {
                warnings.push(`WiFi reconnect not verified${failedStages.length ? ` (${failedStages.join(", ")})` : ""}. Settings were saved; toggle WiFi off/on if needed.`);
            }
            if (warnings.length)
                setActionWarnings(warnings);
            if (result.reconnected) {
                await new Promise((r) => setTimeout(r, RECONNECT_DELAY));
            }
        }
        catch (e) {
            console.error("force reapply error", e);
            setActionError("Force reapply failed. Please try again.");
        }
        finally {
            await refreshStatus(true);
            setBusy(false);
        }
    };
    const handleResetSettings = async () => {
        if (busyRef.current)
            return;
        setBusy(true);
        setOptimizeResult(null);
        setErrors({});
        setActionError(null);
        setActionWarnings(null);
        try {
            const result = await resetSettings();
            const errs = result.errors ?? [];
            if (errs.length) {
                // Non-empty errors[] (possibly with success False) is a warning,
                // not a rejection: defaults were applied with known gaps.
                setActionWarnings([...errs]);
            }
            else if (!result.success) {
                setActionError(result.message ?? "Reset failed. Please try again.");
            }
        }
        catch (e) {
            console.error("reset error", e);
            setActionError("Reset failed. Please try again.");
        }
        finally {
            await refreshStatus(true);
            setBusy(false);
        }
    };
    const handleBackendToggle = async (on) => {
        // Re-entrancy guard: drop rapid clicks or clicks that land while another
        // operation is already running. Protects against duplicate backend calls
        // and the Force-Reapply/backend-switch overlap case.
        if (busyRef.current)
            return;
        const target = on ? "wpa_supplicant" : "iwd";
        setBusy(true);
        setErrors((prev) => {
            const next = { ...prev };
            delete next.wifi_backend;
            return next;
        });
        setOptimizeResult(null);
        try {
            const res = await startBackendSwitch(target);
            if (!res.accepted) {
                setErrors((prev) => ({
                    ...prev,
                    wifi_backend: res.message ?? "Could not start backend switch",
                }));
                // Clear any stale result banner/inline from a prior switch so we don't
                // render old success + new error side-by-side.
                setBackendSwitch(null);
                setBusy(false);
                return;
            }
            setBackendSwitch({
                success: true,
                in_progress: true,
                phase: "switching",
                target,
                started_at: Math.floor(Date.now() / 1000),
                result: null,
            });
            beginBackendPoll();
        }
        catch (e) {
            setBusy(false);
            setErrors((prev) => ({
                ...prev,
                wifi_backend: "Failed to start backend switch",
            }));
            console.error("startBackendSwitch error", e);
        }
    };
    // Divergence retry (ST0-009 D7): re-run the switch toward the configured
    // backend; the gate accepts the same-target start as repair. Blocked
    // while a switch is in progress. Pre-start clearing of
    // wifi_backend/backendSwitch.error is shared with handleBackendToggle
    // (stale error cleared, fresh in-progress state replaces the lock).
    const handleBackendRetry = async (target) => {
        if (backendSwitch?.in_progress)
            return;
        await handleBackendToggle(target === "wpa_supplicant");
    };
    // Update-flow handlers, used by the top update banner and the Updates
    // section. Share the updating/updateError state so either surface can
    // initiate a check or apply an update.
    const handleApplyUpdate = async () => {
        setUpdateError(null);
        setUpdating(true);
        try {
            const r = await applyUpdate();
            if (r && !r.success) {
                setUpdating(false);
                setUpdateError(r.message ?? "Update failed. Please try again.");
            }
            // On success plugin_loader restarts and kills the connection, which
            // lands in the catch below; the safety-timeout effect covers a stall.
        }
        catch {
            // A genuine pre-launch failure surfaces here. A restart-kill after a
            // successful launch clears when the panel reloads.
            setUpdating(false);
            setUpdateError("Update failed. Try again, or reinstall manually from Konsole.");
        }
    };
    const handleCheckForUpdate = async () => {
        setCheckingUpdate(true);
        setUpdateError(null);
        lastUpdateCheckAtRef.current = Date.now();
        try {
            const result = await checkForUpdate();
            setUpdateInfo(result);
            if (result && !result.success) {
                setUpdateError(result.message ?? "Couldn't check for updates.");
            }
        }
        catch {
            setUpdateError("Couldn't check for updates.");
        }
        setCheckingUpdate(false);
    };
    const handleChannelChange = async (nextChannel) => {
        try {
            const r = await setUpdateChannel(nextChannel);
            if (r && !r.success) {
                setUpdateError(r.message ?? "Couldn't change update channel.");
            }
            else {
                setUpdateError(null);
            }
        }
        catch {
            setUpdateError("Couldn't change update channel.");
        }
        setUpdateInfo(null);
        await refreshStatus();
    };
    // Don't render content until first status arrives (prevents disconnect flash).
    // A failed first load renders an error with retry instead of hanging blank.
    if (!status) {
        return (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSection, { title: "WiFi Optimizer TMS" }), statusError && (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(Banner, { variant: "error", icon: "\u2715", children: statusError }), SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => refreshStatus(true), children: "Retry" }) }) })] }))] }));
    }
    const s = status?.settings;
    const connected = status?.connected ?? false;
    const supportTier = status?.support_tier ?? 1;
    const driftCount = status?.drift ? Object.keys(status.drift).length : 0;
    const unknownOwners = status?.unknown_owners ?? [];
    const supports6GHz = s?.supports_6ghz ?? false;
    const isDeckLcd = s?.device_family === "deck_lcd";
    // Mutation lock: normal busy state plus a stuck backend-switch poll
    // failure (backendSwitch.error), which holds controls until the next
    // successful getBackendSwitchStatus reconciles. No retry timers.
    const mutationLocked = isBusy || backendSwitch?.error != null;
    // Check if all safe optimizations are already active
    const allSafeActive = connected &&
        status?.live?.power_save_off &&
        !status?.drift?.power_save &&
        s?.bssid_lock_enabled &&
        !status?.drift?.bssid_lock &&
        status?.live?.dispatcher_installed &&
        status?.live?.buffer_tuning_applied &&
        !status?.drift?.buffer_tuning;
    return (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(PanelHeader, { driver: s?.driver ?? "", version: status?.version ?? "?", lastApplied: s?.last_applied ?? 0, lastEnforced: status?.live?.last_enforced, deviceLabel: s?.device_label !== "Unknown Device"
                    ? `${s?.device_label} - ${s?.chip_label}`
                    : s?.chip_label && s.chip_label !== "unknown"
                        ? s.chip_label
                        : undefined }), supportTier === 3 && (SP_JSX.jsx(Banner, { variant: "info", children: "Unknown WiFi hardware detected. Some optimizations may not apply." })), updateInfo?.update_available && !updating && (SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs(DFL.ButtonItem, { layout: "below", onClick: handleApplyUpdate, children: ["Update to v", updateInfo.latest_version] }) }) })), updating && (SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { fontSize: theme.fontSize.body, color: theme.info.text }, children: "Updating... plugin will restart momentarily." }) }) })), connected && !s?.last_applied && (SP_JSX.jsxs(Banner, { variant: "info", children: ["Tap ", SP_JSX.jsx("strong", { children: "Optimize Safe" }), " to get started."] })), connected && !!s?.last_applied && driftCount > 0 && (SP_JSX.jsxs(Banner, { variant: "warning", icon: "\u26A0", children: [driftCount, " setting", driftCount > 1 ? "s" : "", " drifted after wake.", " ", SP_JSX.jsx("span", { style: { textDecoration: "underline", cursor: "pointer" }, onClick: handleOptimize, children: "Fix now" })] })), !connected && (SP_JSX.jsx(Banner, { variant: "error", icon: "\u2715", children: "Not connected to WiFi. Connect first, then optimize." })), actionError && (SP_JSX.jsx(Banner, { variant: "error", icon: "\u2715", children: actionError })), actionWarnings && actionWarnings.length > 0 && (SP_JSX.jsx(Banner, { variant: "warning", icon: "\u26A0", children: actionWarnings.map((w, i) => (SP_JSX.jsxs("span", { children: [w, i < actionWarnings.length - 1 && SP_JSX.jsx("br", {})] }, i))) })), unknownOwners.length > 0 && (SP_JSX.jsxs(Banner, { variant: "warning", icon: "\u26A0", children: [unknownOwners.length, " setting", unknownOwners.length > 1 ? "s" : "", " ", "lost track of ", unknownOwners.length > 1 ? "their" : "its", " network (", unknownOwners.join(", "), "). Re-apply on the desired network."] })), isStale && (SP_JSX.jsxs(Banner, { variant: "warning", icon: "\u26A0", children: ["Showing last known status", statusAt ? ` from ${new Date(statusAt).toLocaleTimeString()}` : "", " ", "\u2014 refresh failed", statusError ? `: ${statusError}` : "", ".", " ", SP_JSX.jsx("span", { style: { textDecoration: "underline", cursor: "pointer" }, onClick: () => refreshStatus(true), children: "Retry now" })] })), backendSwitch && !backendSwitch.in_progress && backendSwitch.result && (() => {
                const r = backendSwitch.result;
                // Treat reconnect timeout as a warning even when the backend-level
                // switch succeeded - the system is switched but WiFi didn't come back.
                const isWarning = !r.success || r.needs_reboot || r.reconnect_timed_out;
                let text;
                if (r.needs_reboot) {
                    text = `Backend switched to ${r.target}, but wlan0 didn't come back - reboot required`;
                }
                else if (!r.success) {
                    text = r.message ?? "Backend switch failed";
                }
                else {
                    const parts = [`Switched to ${r.backend}`];
                    if (r.recovery_performed)
                        parts.push("recreated wlan0 interface");
                    if (r.reconnect_timed_out)
                        parts.push("WiFi didn't reconnect");
                    text = parts.join(" · ");
                }
                return (SP_JSX.jsx(Banner, { variant: isWarning ? "warning" : "success", icon: isWarning ? "⚠" : "✓", children: text }));
            })(), optimizeResult && (() => {
                const failed = optimizeResult.total - optimizeResult.applied;
                const variant = optimizeResult.total === 0
                    ? "info"
                    : failed > 0
                        ? "warning"
                        : "success";
                const text = optimizeResult.total === 0
                    ? "No optimizations enabled"
                    : failed > 0
                        ? `${optimizeResult.applied}/${optimizeResult.total} applied (${failed} failed)`
                        : "All applied";
                return SP_JSX.jsx(Banner, { variant: variant, children: text });
            })(), SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", disabled: !connected || applyingAll || mutationLocked, onClick: handleOptimize, children: applyingAll
                            ? "Applying..."
                            : allSafeActive
                                ? "All good"
                                : "Optimize Safe" }) }) }), SP_JSX.jsxs(DFL.PanelSection, { title: "Power & stability", children: [SP_JSX.jsx(InfoRow, { label: "Prevent lag spikes", subtitle: "Disables WiFi power save and PCIe power states", explanation: "The OS enables WiFi power saving at multiple levels - the wireless chip, the PCIe bus connecting it to the CPU, and driver-level low power modes. These cause latency spikes, packet batching, and throughput degradation during sustained streaming. This toggle disables all of them, keeping the WiFi hardware fully awake. Battery impact is minimal.", ...getBadge("power_save", status, errors.power_save ?? null), checked: s?.power_save_disabled ?? false, disabled: mutationLocked, error: errors.power_save, onChange: (val) => handleToggle("power_save", () => setPowerSave(val)) }), SP_JSX.jsx(InfoRow, { label: "Stop background scanning", subtitle: "Locks to current AP - disable to switch networks or roam", explanation: "Your device scans for other WiFi networks every few minutes even while connected. Each scan causes a brief interruption that can drop packets and stutter game streaming. Locking to your current access point stops these scans entirely. You'll need to disable this before switching to a different network or access point.", ...getBadge("bssid_lock", status, errors.bssid_lock ?? null), checked: s?.bssid_lock_enabled ?? false, disabled: mutationLocked || (!connected && !s?.bssid_lock_enabled), error: errors.bssid_lock, onChange: (val) => handleToggle("bssid_lock", () => setBssidLock(val)) }), SP_JSX.jsx(InfoRow, { label: "Auto-fix on wake", subtitle: "Reapplies settings after sleep (NM dispatcher)", explanation: "The OS often resets WiFi settings after sleep or updates. This installs a small script that automatically re-applies your optimizations every time the WiFi reconnects. It runs outside of Decky, so it works even if Decky has issues. Removing the plugin will also remove this script.", ...getBadge(undefined, status, errors.auto_fix ?? null), checked: s?.auto_fix_on_wake ?? false, disabled: mutationLocked, error: errors.auto_fix, onChange: (val) => handleToggle("auto_fix", () => setAutoFix(val)) }), SP_JSX.jsx(InfoRow, { label: "Network buffer tuning", subtitle: "Optimize UDP buffers and TX queue for streaming", explanation: "Increases kernel network buffer sizes and transmit queue length to handle the bursty UDP traffic that game streaming produces. Without this, packets can be dropped during high-bitrate moments, causing frame drops or brief quality dips. These settings benefit all network interfaces, including ethernet. They reset on every reboot.", ...getBadge("buffer_tuning", status, errors.buffer_tuning ?? null), checked: s?.buffer_tuning_enabled ?? false, disabled: mutationLocked, error: errors.buffer_tuning, onChange: (val) => handleToggle("buffer_tuning", () => setBufferTuning(val)) })] }), SP_JSX.jsxs(DFL.PanelSection, { title: "Advanced", children: [SP_JSX.jsx(InfoRow, { label: supports6GHz ? "Force 5 GHz / 6 GHz" : "Force 5 GHz band", subtitle: "Avoid 2.4 GHz Bluetooth interference", explanation: `Bluetooth operates on the 2.4 GHz band${isDeckLcd ? ", and on the Steam Deck LCD the antennas are shared" : ""}. Using 5 GHz${supports6GHz ? " or 6 GHz" : ""} for WiFi avoids this interference entirely, giving you a cleaner, faster connection. Only enable this if your router supports 5 GHz. If your network is 2.4 GHz only, this will prevent you from connecting.`, ...getBadge("band_preference", status, errors.band_preference ?? null), checked: s?.band_preference_enabled ?? false, disabled: mutationLocked || (!connected && !s?.band_preference_enabled), error: errors.band_preference, onChange: (val) => handleToggle("band_preference", () => setBandPreference(val, s?.band_preference ?? "a")) }), SP_JSX.jsx(InfoRow, { label: "Custom DNS", subtitle: "Override DNS servers for this network", explanation: "Your internet provider's DNS servers translate domain names into IP addresses. They can be slow or unreliable. Switching to a public DNS like Cloudflare (1.1.1.1) or Google (8.8.8.8) can speed up initial connections and improve reliability. This only affects the current WiFi network.", ...getBadge(undefined, status, errors.dns ?? null), checked: s?.dns_enabled ?? false, disabled: mutationLocked || (!connected && !s?.dns_enabled), error: errors.dns, onChange: (val) => handleToggle("dns", () => setDns(val, s?.dns_provider ?? "cloudflare", customDnsInput)), children: s?.dns_enabled && (SP_JSX.jsxs(SP_JSX.Fragment, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.DropdownItem, { label: "DNS Provider", rgOptions: DNS_OPTIONS, selectedOption: s?.dns_provider ?? "cloudflare", onChange: (option) => {
                                            const custom = option.data === "custom" ? customDnsInput : "";
                                            handleToggle("dns", () => setDns(true, option.data, custom));
                                        } }) }), s?.dns_provider === "custom" && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.TextField, { label: "DNS servers (space-separated)", value: customDnsInput, onChange: (e) => setCustomDnsInput(e.target.value), onBlur: () => {
                                            if (customDnsInput) {
                                                handleToggle("dns", () => setDns(true, "custom", customDnsInput));
                                            }
                                        } }) }))] })) }), SP_JSX.jsx(InfoRow, { label: "Disable IPv6", subtitle: "Use IPv4 only on this network", explanation: "Some networks have poor or misconfigured IPv6 support, which can cause slow DNS resolution, connection timeouts, or routing issues. Disabling IPv6 forces all traffic through IPv4. Only enable this if you're experiencing issues - most modern networks handle IPv6 fine.", ...getBadge("ipv6", status, errors.ipv6 ?? null), checked: s?.ipv6_disabled ?? false, disabled: mutationLocked || (!connected && !s?.ipv6_disabled), error: errors.ipv6, onChange: (val) => handleToggle("ipv6", () => setIpv6(val)) }), SP_JSX.jsx(InfoRow, { label: "Traffic shaping (CAKE)", subtitle: "Fair queuing and bufferbloat prevention", explanation: "Replaces the default network queue with CAKE, which isolates traffic flows so a background download or another device can't starve your game stream. Also filters redundant TCP acknowledgments and prioritizes latency-sensitive packets. Does not limit your bandwidth. Resets on reboot and is reapplied automatically if auto-fix on wake is enabled.", ...getBadge("cake", status, errors.cake ?? null), checked: s?.cake_enabled ?? false, disabled: mutationLocked || (!connected && !s?.cake_enabled), error: errors.cake, onChange: (val) => handleToggle("cake", () => setCake(val)) }), status?.live?.backend_tool_available && (SP_JSX.jsx(BackendToggleRow, { status: status, backendSwitch: backendSwitch, error: errors.wifi_backend ?? backendSwitch?.error, isBusy: mutationLocked, onToggle: handleBackendToggle, onRetry: handleBackendRetry }))] }), SP_JSX.jsxs(DFL.PanelSection, { title: "Live status", children: [connected && status?.live?.ip_address && (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { fontSize: theme.fontSize.tiny, color: theme.text.tertiary }, children: ["IP: ", status.live.ip_address] }) })), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(StatsGrid, { live: status?.live ?? {}, connected: connected }) })] }), SP_JSX.jsx(ActionsSection, { connected: connected, isBusy: mutationLocked, onForceReapply: handleForceReapply, onReset: handleResetSettings }), SP_JSX.jsx(UpdatesSection, { channel: s?.update_channel ?? "stable", updating: updating, checkingUpdate: checkingUpdate, updateInfo: updateInfo, updateError: updateError, onChannelChange: handleChannelChange, onApply: handleApplyUpdate, onCheck: handleCheckForUpdate }), SP_JSX.jsx(PanelFooter, { version: status?.version ?? "?" })] }));
}
var index = definePlugin(() => {
    let gameLifetimeUnsub = null;
    try {
        gameLifetimeUnsub = SteamClient.GameSessions.RegisterForAppLifetimeNotifications((notification) => {
            if (notification.bRunning) {
                setTimeout(() => {
                    reapplyVolatile().catch(() => { });
                }, 3000);
            }
        });
    }
    catch (e) {
        console.error("WiFi Optimizer TMS: failed to register game launch listener", e);
    }
    return {
        name: "WiFi Optimizer TMS",
        titleView: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "WiFi Optimizer TMS" }),
        content: (SP_JSX.jsx(ErrorBoundary, { children: SP_JSX.jsx(Content, {}) })),
        icon: SP_JSX.jsx(FaWifi, {}),
        onDismount() {
            gameLifetimeUnsub?.unregister();
        },
    };
});

export { index as default };
//# sourceMappingURL=index.js.map

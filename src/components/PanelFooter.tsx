import { PanelSection, PanelSectionRow, ButtonItem } from "@decky/ui";
import { theme } from "../theme";
import * as backend from "../backend";
import { useState } from "react";

interface PanelFooterProps {
  version: string;
}

export function PanelFooter({ version }: PanelFooterProps) {
  const [diagState, setDiagState] = useState<
    "idle" | "copying" | "done" | "saved" | "error"
  >("idle");
  const rowStyle: React.CSSProperties = {
    fontSize: theme.fontSize.tiny,
    color: theme.text.dim,
  };

  const handleCopyDiagnostics = async () => {
    setDiagState("copying");
    try {
      const info = await backend.getDiagnosticInfo();
      // Check the collection success flag before reporting done/saved.
      if (!info || (info as { success?: boolean }).success === false) {
        throw new Error("diagnostic collection failed");
      }
      const text = JSON.stringify(info, null, 2);
      try {
        await navigator.clipboard.writeText(text);
        setDiagState("done");
      } catch {
        const saved = await backend.saveDiagnosticInfo();
        // Check the save success flag before reporting saved.
        if (!saved || (saved as { success?: boolean }).success === false) {
          throw new Error("diagnostic save failed");
        }
        setDiagState("saved");
      }
      setTimeout(() => setDiagState("idle"), 5000);
    } catch {
      setDiagState("error");
      setTimeout(() => setDiagState("idle"), 3000);
    }
  };

  const label =
    diagState === "done"
      ? "Copied to clipboard"
      : diagState === "saved"
        ? "Saved to plugin settings folder"
        : diagState === "error"
          ? "Failed to collect diagnostics"
          : diagState === "copying"
            ? "Collecting..."
            : "Copy diagnostics";

  return (
    <PanelSection>
      <PanelSectionRow>
        <div style={rowStyle}>v{version} - by jasonridesabike</div>
      </PanelSectionRow>
      <PanelSectionRow>
        <div style={rowStyle}>
          If WiFi won't reconnect, a reboot usually fixes it.
          <br />
          Bugs? Report at github.com/undefined3491/wifi-optimizer-tms
        </div>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          disabled={diagState === "copying"}
          onClick={handleCopyDiagnostics}
        >
          {label}
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>
  );
}

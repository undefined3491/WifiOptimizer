import { PanelSection, PanelSectionRow, ButtonItem } from "@decky/ui";
import { theme } from "../theme";
import * as backend from "../backend";
import { useEffect, useRef, useState } from "react";

interface PanelFooterProps {
  version: string;
}

export function PanelFooter({ version }: PanelFooterProps) {
  const [diagState, setDiagState] = useState<
    "idle" | "copying" | "done" | "saved" | "error"
  >("idle");
  // Timeout ids (D5): cleared on unmount so no timer touches state late.
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const disposedRef = useRef(false);
  useEffect(() => {
    return () => {
      disposedRef.current = true;
      for (const id of timeoutsRef.current) clearTimeout(id);
      timeoutsRef.current = [];
    };
  }, []);
  const laterIdle = (ms: number) => {
    timeoutsRef.current.push(setTimeout(() => {
      if (disposedRef.current) return;
      setDiagState("idle");
    }, ms));
  };
  const rowStyle: React.CSSProperties = {
    fontSize: theme.fontSize.tiny,
    color: theme.text.dim,
  };

  const handleCopyDiagnostics = async () => {
    setDiagState("copying");
    try {
      const info = await backend.getDiagnosticInfo();
      if (disposedRef.current) return;
      // Check the collection success flag before reporting done/saved.
      if (!info || (info as { success?: boolean }).success === false) {
        throw new Error("diagnostic collection failed");
      }
      const text = JSON.stringify(info, null, 2);
      try {
        await navigator.clipboard.writeText(text);
        if (disposedRef.current) return;
        setDiagState("done");
      } catch {
        const saved = await backend.saveDiagnosticInfo();
        if (disposedRef.current) return;
        // Check the save success flag before reporting saved.
        if (!saved || (saved as { success?: boolean }).success === false) {
          throw new Error("diagnostic save failed");
        }
        setDiagState("saved");
      }
      laterIdle(5000);
    } catch {
      if (disposedRef.current) return;
      setDiagState("error");
      laterIdle(3000);
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

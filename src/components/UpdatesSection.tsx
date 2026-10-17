import { PanelSection, PanelSectionRow, ButtonItem } from "@decky/ui";
import type { UpdateCheckResult } from "../types";
import { theme } from "../theme";

interface UpdatesSectionProps {
  updating: boolean;
  checkingUpdate: boolean;
  updateInfo: UpdateCheckResult | null;
  updateError: string | null;
  onApply: () => void;
  onCheck: () => void;
}

// The Updates panel section: optional warning text for a
// stuck / failed update, and a button that context-switches between
// "Updating...", "Update Now", "Up to date", and "Check for Updates"
// depending on state.
export function UpdatesSection({
  updating,
  checkingUpdate,
  updateInfo,
  updateError,
  onApply,
  onCheck,
}: UpdatesSectionProps) {
  return (
    <PanelSection title="Updates">
      {updateError && !updating && (
        <PanelSectionRow>
          <div style={{ fontSize: theme.fontSize.body, color: theme.warning.text }}>
            &#9888; {updateError}
          </div>
        </PanelSectionRow>
      )}
      {updating ? (
        <PanelSectionRow>
          <div style={{ fontSize: theme.fontSize.body, color: theme.info.text }}>
            Updating... plugin will restart momentarily.
          </div>
        </PanelSectionRow>
      ) : updateInfo?.update_available ? (
        <>
          <PanelSectionRow>
            <div style={{ fontSize: theme.fontSize.body, color: theme.success.text }}>
              v{updateInfo.latest_version} available (you have v{updateInfo.current_version})
            </div>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" onClick={onApply}>
              Update Now
            </ButtonItem>
          </PanelSectionRow>
        </>
      ) : (
        <>
          {updateInfo && updateInfo.success === false && updateInfo.message && (
            <PanelSectionRow>
              <div style={{ fontSize: theme.fontSize.tiny, color: theme.error.text }}>
                {updateInfo.message}
              </div>
            </PanelSectionRow>
          )}
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={checkingUpdate} onClick={onCheck}>
              {checkingUpdate
                ? "Checking..."
                : updateInfo?.success && !updateInfo?.update_available
                  ? "Up to date"
                  : "Check for Updates"}
            </ButtonItem>
          </PanelSectionRow>
        </>
      )}
    </PanelSection>
  );
}

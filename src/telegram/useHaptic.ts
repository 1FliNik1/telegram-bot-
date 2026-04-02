import { tg } from "./index";

export function useHaptic() {
  const impact = (style: "light" | "medium" | "heavy" = "light") => {
    tg?.HapticFeedback.impactOccurred(style);
  };

  const notification = (type: "error" | "success" | "warning") => {
    tg?.HapticFeedback.notificationOccurred(type);
  };

  const selection = () => {
    tg?.HapticFeedback.selectionChanged();
  };

  return { impact, notification, selection };
}

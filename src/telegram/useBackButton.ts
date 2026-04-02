import { useEffect } from "react";
import { tg } from "./index";

export function useBackButton(onBack: (() => void) | null) {
  useEffect(() => {
    if (!tg) return;

    if (onBack) {
      tg.BackButton.show();
      tg.BackButton.onClick(onBack);
    } else {
      tg.BackButton.hide();
    }

    return () => {
      if (onBack) tg.BackButton.offClick(onBack);
    };
  }, [onBack]);
}

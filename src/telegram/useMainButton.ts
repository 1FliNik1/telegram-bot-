import { useEffect } from "react";
import { tg } from "./index";

interface MainButtonOptions {
  text: string;
  onClick: () => void;
  loading?: boolean;
}

export function useMainButton({ text, onClick, loading = false }: MainButtonOptions) {
  useEffect(() => {
    if (!tg) return;

    tg.MainButton.setText(text);
    tg.MainButton.show();

    if (loading) {
      tg.MainButton.showProgress(false);
    } else {
      tg.MainButton.hideProgress();
    }

    tg.MainButton.onClick(onClick);

    return () => {
      tg.MainButton.offClick(onClick);
      tg.MainButton.hide();
    };
  }, [text, onClick, loading]);
}

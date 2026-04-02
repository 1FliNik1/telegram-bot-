import { useEffect, useRef, useState } from "react";
import styles from "./BottomSheet.module.css";

interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

export default function BottomSheet({ open, onClose, children }: BottomSheetProps) {
  const [visible, setVisible] = useState(false);
  const [animate, setAnimate] = useState(false);
  const startY = useRef<number>(0);
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setVisible(true);
      requestAnimationFrame(() => setAnimate(true));
    } else {
      setAnimate(false);
      const t = setTimeout(() => setVisible(false), 300);
      return () => clearTimeout(t);
    }
  }, [open]);

  const handleTouchStart = (e: React.TouchEvent) => {
    startY.current = e.touches[0].clientY;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const delta = e.changedTouches[0].clientY - startY.current;
    if (delta > 80) onClose();
  };

  if (!visible) return null;

  return (
    <div className={`${styles.overlay} ${animate ? styles.overlayVisible : ""}`} onClick={onClose}>
      <div
        ref={sheetRef}
        className={`${styles.sheet} ${animate ? styles.sheetOpen : ""}`}
        onClick={(e) => e.stopPropagation()}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <div className={styles.handle} />
        {children}
      </div>
    </div>
  );
}

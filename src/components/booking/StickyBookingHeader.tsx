import styles from "./StickyBookingHeader.module.css";

interface StickyBookingHeaderProps {
  serviceName?: string;
  masterName?: string;
  price?: number;
  date?: string;
}

export default function StickyBookingHeader({
  serviceName,
  masterName,
  price,
  date,
}: StickyBookingHeaderProps) {
  const parts = [serviceName, masterName, date].filter(Boolean);
  return (
    <div className={styles.header}>
      <p className={styles.context}>{parts.join(" · ")}</p>
      {price != null && <p className={styles.price}>{price} ₴</p>}
    </div>
  );
}

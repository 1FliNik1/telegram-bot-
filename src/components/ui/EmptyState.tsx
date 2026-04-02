import styles from "./EmptyState.module.css";

interface EmptyStateProps {
  emoji: string;
  title: string;
  subtitle?: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({ emoji, title, subtitle, action }: EmptyStateProps) {
  return (
    <div className={styles.container}>
      <div className={styles.emoji}>{emoji}</div>
      <p className={styles.title}>{title}</p>
      {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      {action && (
        <button className={styles.button} onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}

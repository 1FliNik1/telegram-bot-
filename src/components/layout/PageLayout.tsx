import styles from "./PageLayout.module.css";

interface PageLayoutProps {
  title?: string;
  children: React.ReactNode;
}

export default function PageLayout({ title, children }: PageLayoutProps) {
  return (
    <div className={styles.page}>
      {title && (
        <header className={styles.header}>
          <h1 className={styles.title}>{title}</h1>
        </header>
      )}
      <main className={styles.content}>{children}</main>
    </div>
  );
}

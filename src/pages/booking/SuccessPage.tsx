import { useNavigate } from "react-router-dom";
import { useBackButton } from "../../telegram/useBackButton";
import styles from "./SuccessPage.module.css";

export default function SuccessPage() {
  const navigate = useNavigate();

  // На success BackButton не показуємо — тільки кнопки на сторінці
  useBackButton(null);

  return (
    <div className={styles.page}>
      <div className={styles.icon}>✅</div>
      <h1 className={styles.title}>Записано!</h1>
      <p className={styles.subtitle}>
        Нагадаємо за день та за 2 години 💬
      </p>

      <div className={styles.actions}>
        <button
          className={styles.btnSecondary}
          onClick={() => navigate("/", { replace: true })}
        >
          На головну
        </button>
        <button
          className={styles.btnPrimary}
          onClick={() => navigate("/appointments", { replace: true })}
        >
          Мої записи
        </button>
      </div>
    </div>
  );
}

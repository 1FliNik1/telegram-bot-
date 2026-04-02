import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { createBooking } from "../../api/booking";
import { useBookingStore } from "../../store/bookingStore";
import { useBackButton } from "../../telegram/useBackButton";
import { useMainButton } from "../../telegram/useMainButton";
import { useHaptic } from "../../telegram/useHaptic";
import Toast from "../../components/ui/Toast";
import styles from "./ConfirmStep.module.css";

function formatDateFull(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("uk-UA", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export default function ConfirmStep() {
  const navigate = useNavigate();
  const { notification } = useHaptic();
  const { service, master, date, slot, reset } = useBookingStore();
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useBackButton(() => navigate(-1));

  useEffect(() => {
    if (!service || !master || !date || !slot) navigate("/booking/time");
  }, [service, master, date, slot, navigate]);

  const handleConfirm = async () => {
    if (!service || !master || !date || !slot || loading) return;
    setLoading(true);
    try {
      await createBooking({
        service_id: service.id,
        master_id: master.id,
        timeslot_id: slot.id, // backend requires timeslot_id
      });
      notification("success");
      reset();
      navigate("/booking/success", { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setToast("Цей час щойно зайняли. Оберіть інший.");
        notification("error");
        navigate("/booking/time");
      } else {
        setToast("Помилка. Спробуйте ще раз.");
        notification("error");
      }
    } finally {
      setLoading(false);
    }
  };

  useMainButton({ text: "Підтвердити запис", onClick: handleConfirm, loading });

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Підтвердження</h1>
      </header>

      <div className={styles.content}>
        <div className={styles.summaryCard}>
          {service && (
            <div className={styles.row}>
              <span className={styles.rowIcon}>✂️</span>
              <span className={styles.rowValue}>{service.name}</span>
            </div>
          )}
          {master && (
            <div className={styles.row}>
              <span className={styles.rowIcon}>👩</span>
              <span className={styles.rowValue}>{master.name}</span>
            </div>
          )}
          {date && (
            <div className={styles.row}>
              <span className={styles.rowIcon}>📅</span>
              <span className={styles.rowValue}>{formatDateFull(date)}</span>
            </div>
          )}
          {slot && date && (
            <div className={styles.row}>
              <span className={styles.rowIcon}>🕐</span>
              <span className={styles.rowValue}>
                {slot.start_time.slice(0, 5)} — {slot.end_time.slice(0, 5)}
              </span>
            </div>
          )}
          {service && (
            <div className={`${styles.row} ${styles.priceRow}`}>
              <span className={styles.rowIcon}>💰</span>
              <span className={styles.rowValue}>{service.price} ₴</span>
            </div>
          )}
        </div>

        <p className={styles.hint}>
          Натисніть кнопку нижче для підтвердження запису
        </p>
      </div>

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  );
}

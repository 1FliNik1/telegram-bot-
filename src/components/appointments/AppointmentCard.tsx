import type { Appointment } from "../../api/appointments";
import styles from "./AppointmentCard.module.css";

const STATUS_CONFIG = {
  pending: { label: "Очікує", emoji: "⏳", className: "pending" },
  confirmed: { label: "Підтверджено", emoji: "✅", className: "confirmed" },
  cancelled: { label: "Скасовано", emoji: "❌", className: "cancelled" },
  completed: { label: "Завершено", emoji: "✔️", className: "completed" },
} as const;

function formatDateTime(date: string, time: string): string {
  const d = new Date(date);
  const dayLabel = d.toLocaleDateString("uk-UA", { weekday: "short", day: "numeric", month: "short" });
  return `${dayLabel} · ${time.slice(0, 5)}`;
}

function isWithin2Hours(date: string, time: string): boolean {
  const dt = new Date(`${date}T${time}`);
  return dt.getTime() - Date.now() < 2 * 60 * 60 * 1000;
}

interface AppointmentCardProps {
  appointment: Appointment;
  onCancel: (id: number, withinWarning: boolean) => void;
}

export default function AppointmentCard({ appointment, onCancel }: AppointmentCardProps) {
  const status = STATUS_CONFIG[appointment.status];
  const canCancel = appointment.status === "pending" || appointment.status === "confirmed";
  const warning = isWithin2Hours(appointment.date, appointment.start_time);

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <div className={styles.service}>
          <span className={styles.serviceName}>{appointment.service_name}</span>
          <span className={`${styles.statusBadge} ${styles[status.className]}`}>
            {status.emoji} {status.label}
          </span>
        </div>
        <p className={styles.meta}>
          {appointment.master_name} · {formatDateTime(appointment.date, appointment.start_time)}
        </p>
        <p className={styles.price}>{appointment.price} ₴</p>
      </div>

      {canCancel && (
        <div className={styles.actions}>
          <button
            className={styles.cancelBtn}
            onClick={() => onCancel(appointment.id, warning)}
          >
            Скасувати
          </button>
        </div>
      )}
    </div>
  );
}

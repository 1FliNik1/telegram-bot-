import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { getAppointments, cancelAppointment } from "../api/appointments";
import { useBackButton } from "../telegram/useBackButton";
import { useHaptic } from "../telegram/useHaptic";
import AppointmentCard from "../components/appointments/AppointmentCard";
import Skeleton from "../components/ui/Skeleton";
import EmptyState from "../components/ui/EmptyState";
import Toast from "../components/ui/Toast";
import styles from "./AppointmentsPage.module.css";

interface PendingCancel {
  id: number;
  warning: boolean;
}

export default function AppointmentsPage() {
  const navigate = useNavigate();
  const { notification } = useHaptic();
  const queryClient = useQueryClient();
  const [pendingCancel, setPendingCancel] = useState<PendingCancel | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useBackButton(() => navigate("/"));

  const { data: appointments = [], isLoading } = useQuery({
    queryKey: ["appointments"],
    queryFn: getAppointments,
  });

  const { mutate: doCancel } = useMutation({
    mutationFn: (id: number) => cancelAppointment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
      notification("success");
      setToast("Запис скасовано");
    },
    onError: (err) => {
      notification("error");
      if (
        axios.isAxiosError(err) &&
        err.response?.data?.detail?.error === "too_late_to_cancel"
      ) {
        setToast("Скасування недоступне менш ніж за 2 години до запису");
      } else {
        setToast("Помилка при скасуванні");
      }
    },
  });

  const handleCancelRequest = (id: number, warning: boolean) => {
    setPendingCancel({ id, warning });
  };

  const handleConfirmCancel = () => {
    if (!pendingCancel) return;
    doCancel(pendingCancel.id);
    setPendingCancel(null);
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Мої записи</h1>
      </header>

      <div className={styles.content}>
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className={styles.skeletonCard}>
              <Skeleton width="60%" height={18} />
              <Skeleton width="80%" height={14} />
              <Skeleton width="40%" height={14} />
            </div>
          ))
        ) : appointments.length === 0 ? (
          <EmptyState
            emoji="📅"
            title="Немає активних записів"
            subtitle="Запишіться на послугу прямо зараз"
            action={{ label: "✂️ Записатись", onClick: () => navigate("/catalog") }}
          />
        ) : (
          appointments.map((apt) => (
            <AppointmentCard
              key={apt.id}
              appointment={apt}
              onCancel={handleCancelRequest}
            />
          ))
        )}
      </div>

      {/* Cancel confirm dialog */}
      {pendingCancel && (
        <div className={styles.dialogOverlay} onClick={() => setPendingCancel(null)}>
          <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
            {pendingCancel.warning && (
              <p className={styles.dialogWarning}>
                ⚠️ До запису менше 2 годин. Впевнені що хочете скасувати?
              </p>
            )}
            <p className={styles.dialogText}>
              {pendingCancel.warning
                ? "Скасування пізніше ніж за 2 години може бути платним."
                : "Підтвердіть скасування запису."}
            </p>
            <div className={styles.dialogActions}>
              <button className={styles.dialogCancel} onClick={() => setPendingCancel(null)}>
                Назад
              </button>
              <button className={styles.dialogConfirm} onClick={handleConfirmCancel}>
                Скасувати запис
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  );
}

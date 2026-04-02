import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAvailableDates } from "../../api/booking";
import { useBookingStore } from "../../store/bookingStore";
import { useBackButton } from "../../telegram/useBackButton";
import { useHaptic } from "../../telegram/useHaptic";
import StickyBookingHeader from "../../components/booking/StickyBookingHeader";
import Skeleton from "../../components/ui/Skeleton";
import styles from "./DateStep.module.css";

// Mon=0 … Sun=6  (ISO week order)
const WEEK_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"];

/** Offset from Monday for a given ISO date string */
function weekOffset(dateStr: string): number {
  const day = new Date(dateStr).getDay(); // Sun=0, Mon=1…
  return (day + 6) % 7; // Mon=0 … Sun=6
}

function getDayNumber(dateStr: string): number {
  return new Date(dateStr).getDate();
}

/** "Квіт" / "Бер" etc. for the month header */
function monthLabel(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("uk-UA", { month: "long", year: "numeric" });
}

export default function DateStep() {
  const navigate = useNavigate();
  const { impact } = useHaptic();
  const { service, master, setDate } = useBookingStore();

  useBackButton(() => navigate(-1));

  useEffect(() => {
    if (!service || !master) navigate("/booking/master");
  }, [service, master, navigate]);

  const { data: dates = [], isLoading } = useQuery({
    queryKey: ["available-dates", master?.id, service?.id],
    queryFn: () => getAvailableDates(master!.id, service!.id),
    enabled: !!master && !!service,
  });

  const handleSelect = (date: string) => {
    impact("medium");
    setDate(date);
    navigate("/booking/time");
  };

  // Leading empty cells so first date aligns to correct weekday column
  const leadingEmpties = dates.length > 0 ? weekOffset(dates[0].date) : 0;

  // Group dates by month to show month header
  const firstMonth = dates.length > 0 ? monthLabel(dates[0].date) : "";

  return (
    <div className={styles.page}>
      <StickyBookingHeader
        serviceName={service?.name}
        masterName={master?.name}
        price={service?.price}
      />

      <div className={styles.content}>
        <h2 className={styles.heading}>Оберіть дату</h2>

        {isLoading ? (
          <Skeleton height={280} borderRadius={16} />
        ) : (
          <div className={styles.calendar}>
            {firstMonth && <p className={styles.monthLabel}>{firstMonth}</p>}

            {/* Weekday headers */}
            <div className={styles.weekRow}>
              {WEEK_DAYS.map((d) => (
                <div key={d} className={styles.weekDay}>{d}</div>
              ))}
            </div>

            {/* Date grid — leading empty cells + 14 date cells */}
            <div className={styles.daysGrid}>
              {Array.from({ length: leadingEmpties }).map((_, i) => (
                <div key={`empty-${i}`} />
              ))}
              {dates.map((d) => (
                <button
                  key={d.date}
                  className={`${styles.dayCell} ${d.has_slots ? styles.available : styles.unavailable}`}
                  disabled={!d.has_slots}
                  onClick={() => handleSelect(d.date)}
                >
                  <span className={styles.dayNum}>{getDayNumber(d.date)}</span>
                  {d.has_slots && <span className={styles.dot} />}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className={styles.legend}>
          <span className={styles.legendDot} /> є вільні слоти
          <span className={styles.legendEmpty} /> немає слотів
        </div>
      </div>
    </div>
  );
}

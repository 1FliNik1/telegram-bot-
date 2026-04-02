import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAvailableSlots, type TimeSlot } from "../../api/booking";
import { useBookingStore } from "../../store/bookingStore";
import { useBackButton } from "../../telegram/useBackButton";
import { useHaptic } from "../../telegram/useHaptic";
import StickyBookingHeader from "../../components/booking/StickyBookingHeader";
import Skeleton from "../../components/ui/Skeleton";
import EmptyState from "../../components/ui/EmptyState";
import styles from "./TimeStep.module.css";

function groupSlots(slots: TimeSlot[]) {
  const morning: TimeSlot[] = [];
  const afternoon: TimeSlot[] = [];
  const evening: TimeSlot[] = [];

  for (const slot of slots) {
    // start_time may be "09:00:00" or "09:00"
    const hour = parseInt(slot.start_time.split(":")[0], 10);
    if (hour < 12) morning.push(slot);
    else if (hour < 17) afternoon.push(slot);
    else evening.push(slot);
  }
  return { morning, afternoon, evening };
}

function formatTime(time: string): string {
  return time.slice(0, 5);
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("uk-UA", { weekday: "short", day: "numeric", month: "short" });
}

interface SlotGroupProps {
  label: string;
  slots: TimeSlot[];
  onSelect: (slot: TimeSlot) => void;
}

function SlotGroup({ label, slots, onSelect }: SlotGroupProps) {
  if (slots.length === 0) return null;
  return (
    <div className={styles.group}>
      <p className={styles.groupLabel}>{label}</p>
      <div className={styles.slotsGrid}>
        {slots.map((slot) => (
          <button
            key={slot.start_time}
            className={styles.slot}
            onClick={() => onSelect(slot)}
          >
            {formatTime(slot.start_time)}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function TimeStep() {
  const navigate = useNavigate();
  const { impact } = useHaptic();
  const { service, master, date, setSlot } = useBookingStore();

  useBackButton(() => navigate(-1));

  useEffect(() => {
    if (!service || !master || !date) navigate("/booking/date");
  }, [service, master, date, navigate]);

  const { data: slots = [], isLoading } = useQuery({
    queryKey: ["available-slots", master?.id, service?.id, date],
    queryFn: () => getAvailableSlots(master!.id, service!.id, date!),
    enabled: !!master && !!service && !!date,
  });

  const handleSelect = (slot: TimeSlot) => {
    impact("medium");
    setSlot(slot);
    navigate("/booking/confirm");
  };

  const { morning, afternoon, evening } = groupSlots(slots);

  return (
    <div className={styles.page}>
      <StickyBookingHeader
        serviceName={service?.name}
        masterName={master?.name}
        date={date ? formatDateLabel(date) : undefined}
      />

      <div className={styles.content}>
        <h2 className={styles.heading}>Оберіть час</h2>

        {isLoading ? (
          <Skeleton height={200} borderRadius={16} />
        ) : slots.length === 0 ? (
          <EmptyState
            emoji="😔"
            title="Немає вільних слотів"
            subtitle="Спробуйте іншу дату"
            action={{ label: "Обрати іншу дату", onClick: () => navigate(-1) }}
          />
        ) : (
          <div className={styles.groups}>
            <SlotGroup label="Ранок" slots={morning} onSelect={handleSelect} />
            <SlotGroup label="День" slots={afternoon} onSelect={handleSelect} />
            <SlotGroup label="Вечір" slots={evening} onSelect={handleSelect} />
          </div>
        )}
      </div>
    </div>
  );
}

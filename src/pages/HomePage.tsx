import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getMe } from "../api/me";
import { useBackButton } from "../telegram/useBackButton";
import Skeleton from "../components/ui/Skeleton";
import styles from "./HomePage.module.css";

function formatCountdown(date: string, time: string): string {
  const appointmentDate = new Date(`${date}T${time}`);
  const now = new Date();
  const diffMs = appointmentDate.getTime() - now.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours === 0) return "сьогодні скоро";
    return `сьогодні о ${time.slice(0, 5)}`;
  }
  if (diffDays === 1) return "завтра";
  return `через ${diffDays} дні`;
}

function formatDate(date: string): string {
  const d = new Date(date);
  return d.toLocaleDateString("uk-UA", { weekday: "short", day: "numeric", month: "long" });
}

const NAV_CARDS = [
  { label: "Каталог", emoji: "📋", path: "/catalog" },
  { label: "Запис", emoji: "✂️", path: "/booking/master" },
  { label: "Мої записи", emoji: "📅", path: "/appointments" },
  { label: "Прайс", emoji: "💰", path: "/pricelist" },
];

export default function HomePage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({ queryKey: ["me"], queryFn: getMe });

  // На головній BackButton не потрібна
  useBackButton(null);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <span className={styles.salonName}>Салон краси</span>
      </header>

      <main className={styles.content}>
        {/* Greeting */}
        <div className={styles.greeting}>
          {isLoading ? (
            <Skeleton width={200} height={28} />
          ) : (
            <h1 className={styles.greetingText}>
              Привіт, {data?.first_name ?? ""}! 👋
            </h1>
          )}
        </div>

        {/* Upcoming appointment smart-block */}
        {isLoading ? (
          <div className={styles.upcomingBlock}>
            <Skeleton height={90} borderRadius={16} />
          </div>
        ) : data?.upcoming_appointment ? (
          <button
            className={styles.upcomingBlock}
            onClick={() => navigate("/appointments")}
          >
            <div className={styles.upcomingEmoji}>💅</div>
            <div className={styles.upcomingInfo}>
              <p className={styles.upcomingService}>
                {data.upcoming_appointment.service_name}
              </p>
              <p className={styles.upcomingMaster}>
                {data.upcoming_appointment.master_name} ·{" "}
                {formatDate(data.upcoming_appointment.date)} ·{" "}
                {data.upcoming_appointment.start_time.slice(0, 5)}
              </p>
              <p className={styles.upcomingCountdown}>
                {formatCountdown(
                  data.upcoming_appointment.date,
                  data.upcoming_appointment.start_time
                )}
              </p>
            </div>
            <span className={styles.upcomingArrow}>›</span>
          </button>
        ) : null}

        {/* 2x2 Navigation grid */}
        <div className={styles.navGrid}>
          {NAV_CARDS.map((card) => (
            <button
              key={card.path}
              className={styles.navCard}
              onClick={() => navigate(card.path)}
            >
              <span className={styles.navEmoji}>{card.emoji}</span>
              <span className={styles.navLabel}>{card.label}</span>
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}

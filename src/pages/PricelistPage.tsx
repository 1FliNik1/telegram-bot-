import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getPricelist, type PricelistCategory } from "../api/pricelist";
import { useBookingStore } from "../store/bookingStore";
import { useBackButton } from "../telegram/useBackButton";
import { useHaptic } from "../telegram/useHaptic";
import Skeleton from "../components/ui/Skeleton";
import styles from "./PricelistPage.module.css";

function formatPrice(price: number, priceMax: number | null): string {
  return priceMax != null ? `${price}–${priceMax} ₴` : `${price} ₴`;
}

interface AccordionItemProps {
  category: PricelistCategory;
  searchQuery: string;
  onServiceClick: (name: string) => void;
}

function AccordionItem({ category, searchQuery, onServiceClick }: AccordionItemProps) {
  const [open, setOpen] = useState(false);
  const { impact } = useHaptic();

  const filteredServices = searchQuery
    ? category.services.filter((s) =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : category.services;

  if (searchQuery && filteredServices.length === 0) return null;

  const isForced = searchQuery.length > 0;

  return (
    <div className={styles.accordionItem}>
      <button
        className={styles.accordionHeader}
        onClick={() => {
          if (!isForced) {
            impact("light");
            setOpen((v) => !v);
          }
        }}
      >
        <span className={styles.categoryName}>
          {category.emoji} {category.name}
        </span>
        {!isForced && (
          <span className={`${styles.chevron} ${open ? styles.chevronOpen : ""}`}>
            ›
          </span>
        )}
      </button>

      {(open || isForced) && (
        <div className={styles.serviceList}>
          {filteredServices.map((service, i) => (
            <button
              key={i}
              className={styles.serviceRow}
              onClick={() => onServiceClick(service.name)}
            >
              <div className={styles.serviceLeft}>
                <p className={styles.serviceName}>{service.name}</p>
                <p className={styles.serviceDuration}>{service.duration_minutes} хв</p>
              </div>
              <p className={styles.servicePrice}>
                {formatPrice(service.price, service.price_max)}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PricelistPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const setService = useBookingStore((s) => s.setService);

  useBackButton(() => navigate("/"));

  const { data: categories = [], isLoading } = useQuery({
    queryKey: ["pricelist"],
    queryFn: getPricelist,
  });

  // Pricelist doesn't have full Service objects, so we navigate to catalog on tap
  const handleServiceClick = (_name: string) => {
    navigate("/catalog");
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Прайс-лист</h1>
      </header>

      <div className={styles.searchWrap}>
        <input
          className={styles.searchInput}
          type="text"
          placeholder="🔍 Пошук послуги..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className={styles.content}>
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className={styles.skeletonItem}>
              <Skeleton height={52} borderRadius={12} />
            </div>
          ))
        ) : (
          categories.map((cat) => (
            <AccordionItem
              key={cat.name}
              category={cat}
              searchQuery={search}
              onServiceClick={handleServiceClick}
            />
          ))
        )}
      </div>
    </div>
  );
}

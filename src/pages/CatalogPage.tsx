import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getCategories, getServices } from "../api/catalog";
import { useBackButton } from "../telegram/useBackButton";
import { useHaptic } from "../telegram/useHaptic";
import CategoryTabs from "../components/catalog/CategoryTabs";
import ServiceCard from "../components/catalog/ServiceCard";
import ServiceDetail from "../components/catalog/ServiceDetail";
import BottomSheet from "../components/layout/BottomSheet";
import Skeleton from "../components/ui/Skeleton";
import EmptyState from "../components/ui/EmptyState";
import styles from "./CatalogPage.module.css";

export default function CatalogPage() {
  const navigate = useNavigate();
  const { impact } = useHaptic();
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);

  useBackButton(() => navigate("/"));

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: getCategories,
  });

  const { data: services = [], isLoading } = useQuery({
    queryKey: ["services", selectedCategory],
    queryFn: () => getServices(selectedCategory),
  });

  const handleCategorySelect = (id: number | null) => {
    impact("light");
    setSelectedCategory(id);
  };

  const handleServiceClick = (id: number) => {
    impact("light");
    setSelectedServiceId(id);
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Каталог</h1>
      </header>

      <CategoryTabs
        categories={categories}
        selected={selectedCategory}
        onSelect={handleCategorySelect}
      />

      <div className={styles.grid}>
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className={styles.skeletonCard}>
              <Skeleton height={160} borderRadius={12} />
              <Skeleton width="70%" height={14} />
              <Skeleton width="50%" height={12} />
            </div>
          ))
        ) : services.length === 0 ? (
          <div className={styles.emptyWrap}>
            <EmptyState
              emoji="💅"
              title="Каталог оновлюється"
              subtitle="Послуги в цій категорії скоро з'являться"
            />
          </div>
        ) : (
          services.map((service) => (
            <ServiceCard
              key={service.id}
              service={service}
              onClick={() => handleServiceClick(service.id)}
            />
          ))
        )}
      </div>

      <BottomSheet
        open={selectedServiceId != null}
        onClose={() => setSelectedServiceId(null)}
      >
        {selectedServiceId != null && (
          <ServiceDetail
            serviceId={selectedServiceId}
            onClose={() => setSelectedServiceId(null)}
          />
        )}
      </BottomSheet>
    </div>
  );
}

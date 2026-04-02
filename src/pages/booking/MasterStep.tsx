import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getServiceDetail } from "../../api/catalog";
import { useBookingStore } from "../../store/bookingStore";
import { useBackButton } from "../../telegram/useBackButton";
import { useHaptic } from "../../telegram/useHaptic";
import StickyBookingHeader from "../../components/booking/StickyBookingHeader";
import GradientPlaceholder from "../../components/ui/GradientPlaceholder";
import Skeleton from "../../components/ui/Skeleton";
import EmptyState from "../../components/ui/EmptyState";
import styles from "./MasterStep.module.css";

export default function MasterStep() {
  const navigate = useNavigate();
  const { impact } = useHaptic();
  const { service, setMaster } = useBookingStore();
  const [imgErrors, setImgErrors] = useState<Set<number>>(new Set());

  useBackButton(() => navigate(-1));

  // Redirect if no service selected
  useEffect(() => {
    if (!service) navigate("/catalog");
  }, [service, navigate]);

  const { data, isLoading } = useQuery({
    queryKey: ["service", service?.id],
    queryFn: () => getServiceDetail(service!.id),
    enabled: !!service,
  });

  // Auto-advance if only 1 master
  useEffect(() => {
    if (data?.masters.length === 1) {
      setMaster(data.masters[0]);
      navigate("/booking/date", { replace: true });
    }
  }, [data, setMaster, navigate]);

  const handleSelect = (master: NonNullable<typeof data>["masters"][number]) => {
    impact("medium");
    setMaster(master);
    navigate("/booking/date");
  };

  return (
    <div className={styles.page}>
      <StickyBookingHeader
        serviceName={service?.name}
        price={service?.price}
      />

      <div className={styles.content}>
        <h2 className={styles.heading}>Оберіть майстра</h2>

        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className={styles.skeletonCard}>
              <Skeleton width={56} height={56} borderRadius="50%" />
              <div className={styles.skeletonInfo}>
                <Skeleton width={120} height={16} />
                <Skeleton width={160} height={13} />
              </div>
            </div>
          ))
        ) : data?.masters.length === 0 ? (
          <EmptyState emoji="😔" title="Немає доступних майстрів" />
        ) : (
          data?.masters.map((master) => {
            const price = master.custom_price ?? service?.price;
            return (
              <button
                key={master.id}
                className={styles.masterCard}
                onClick={() => handleSelect(master)}
              >
                <div className={styles.avatar}>
                  {master.avatar_url && !imgErrors.has(master.id) ? (
                    <img
                      src={master.avatar_url}
                      alt={master.name}
                      className={styles.avatarImg}
                      onError={() =>
                        setImgErrors((prev) => new Set(prev).add(master.id))
                      }
                    />
                  ) : (
                    <GradientPlaceholder name={master.name} />
                  )}
                </div>
                <div className={styles.masterInfo}>
                  <p className={styles.masterName}>{master.name}</p>
                  {master.bio && (
                    <p className={styles.masterBio}>{master.bio}</p>
                  )}
                  {price != null && (
                    <p className={styles.masterPrice}>{price} ₴</p>
                  )}
                </div>
                <span className={styles.arrow}>›</span>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}

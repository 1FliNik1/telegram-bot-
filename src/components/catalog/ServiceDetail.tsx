import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getServiceDetail } from "../../api/catalog";
import { useBookingStore } from "../../store/bookingStore";
import GradientPlaceholder from "../ui/GradientPlaceholder";
import Skeleton from "../ui/Skeleton";
import styles from "./ServiceDetail.module.css";

interface ServiceDetailProps {
  serviceId: number;
  onClose: () => void;
}

export default function ServiceDetail({ serviceId, onClose }: ServiceDetailProps) {
  const navigate = useNavigate();
  const setService = useBookingStore((s) => s.setService);
  const [imgError, setImgError] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["service", serviceId],
    queryFn: () => getServiceDetail(serviceId),
  });

  const handleBook = () => {
    if (!data) return;
    setService(data);
    onClose();
    navigate("/booking/master");
  };

  const priceLabel = data
    ? data.price_max != null
      ? `${data.price}–${data.price_max} ₴`
      : `${data.price} ₴`
    : "";

  return (
    <div className={styles.container}>
      {isLoading ? (
        <>
          <Skeleton height={220} borderRadius={12} />
          <div className={styles.body}>
            <Skeleton width={180} height={24} />
            <Skeleton width={120} height={16} />
            <Skeleton height={60} />
          </div>
        </>
      ) : data ? (
        <>
          <div className={styles.imageWrap}>
            {data.photo_url && !imgError ? (
              <img
                src={data.photo_url}
                alt={data.name}
                className={styles.image}
                onError={() => setImgError(true)}
              />
            ) : (
              <GradientPlaceholder name={data.name} className={styles.placeholder} />
            )}
          </div>
          <div className={styles.body}>
            <h2 className={styles.name}>{data.name}</h2>
            <p className={styles.meta}>
              💰 {priceLabel} &nbsp;·&nbsp; ⏱ {data.duration_minutes} хв
            </p>
            {data.description && (
              <p className={styles.description}>{data.description}</p>
            )}
            {data.masters.length > 0 && (
              <p className={styles.masters}>
                Майстри: {data.masters.map((m) => m.name).join(", ")}
              </p>
            )}
          </div>
          <button className={styles.bookButton} onClick={handleBook}>
            ✂️ Записатись
          </button>
        </>
      ) : null}
    </div>
  );
}

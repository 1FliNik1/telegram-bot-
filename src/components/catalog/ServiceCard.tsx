import { useState } from "react";
import type { Service } from "../../api/catalog";
import GradientPlaceholder from "../ui/GradientPlaceholder";
import styles from "./ServiceCard.module.css";

interface ServiceCardProps {
  service: Service;
  onClick: () => void;
}

export default function ServiceCard({ service, onClick }: ServiceCardProps) {
  const [imgError, setImgError] = useState(false);

  const priceLabel =
    service.price_max != null
      ? `${service.price}–${service.price_max} ₴`
      : `${service.price} ₴`;

  return (
    <button className={styles.card} onClick={onClick}>
      <div className={styles.imageWrap}>
        {service.photo_url && !imgError ? (
          <img
            src={service.photo_url}
            alt={service.name}
            className={styles.image}
            loading="lazy"
            onError={() => setImgError(true)}
          />
        ) : (
          <GradientPlaceholder name={service.name} />
        )}
      </div>
      <div className={styles.info}>
        <p className={styles.name}>{service.name}</p>
        <p className={styles.meta}>
          {priceLabel} · {service.duration_minutes} хв
        </p>
      </div>
    </button>
  );
}

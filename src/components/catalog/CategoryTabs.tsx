import type { Category } from "../../api/catalog";
import styles from "./CategoryTabs.module.css";

interface CategoryTabsProps {
  categories: Category[];
  selected: number | null;
  onSelect: (id: number | null) => void;
}

export default function CategoryTabs({ categories, selected, onSelect }: CategoryTabsProps) {
  return (
    <div className={styles.tabs}>
      <button
        className={`${styles.tab} ${selected === null ? styles.active : ""}`}
        onClick={() => onSelect(null)}
      >
        Все
      </button>
      {categories.map((cat) => (
        <button
          key={cat.id}
          className={`${styles.tab} ${selected === cat.id ? styles.active : ""}`}
          onClick={() => onSelect(cat.id)}
        >
          {cat.emoji} {cat.name}
        </button>
      ))}
    </div>
  );
}

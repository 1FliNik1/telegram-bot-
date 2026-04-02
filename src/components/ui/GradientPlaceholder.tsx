import styles from "./GradientPlaceholder.module.css";

const GRADIENTS = [
  "linear-gradient(135deg, #f093fb, #f5576c)",
  "linear-gradient(135deg, #4facfe, #00f2fe)",
  "linear-gradient(135deg, #43e97b, #38f9d7)",
  "linear-gradient(135deg, #fa709a, #fee140)",
  "linear-gradient(135deg, #a18cd1, #fbc2eb)",
  "linear-gradient(135deg, #fccb90, #d57eeb)",
];

function pickGradient(name: string): string {
  const index = name.charCodeAt(0) % GRADIENTS.length;
  return GRADIENTS[index];
}

interface GradientPlaceholderProps {
  name: string;
  className?: string;
}

export default function GradientPlaceholder({ name, className }: GradientPlaceholderProps) {
  return (
    <div
      className={`${styles.placeholder} ${className ?? ""}`}
      style={{ background: pickGradient(name) }}
    >
      <span className={styles.letter}>{name.charAt(0).toUpperCase()}</span>
    </div>
  );
}

import { Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { tg } from "./telegram";
import HomePage from "./pages/HomePage";
import CatalogPage from "./pages/CatalogPage";
import AppointmentsPage from "./pages/AppointmentsPage";
import PricelistPage from "./pages/PricelistPage";
import MasterStep from "./pages/booking/MasterStep";
import DateStep from "./pages/booking/DateStep";
import TimeStep from "./pages/booking/TimeStep";
import ConfirmStep from "./pages/booking/ConfirmStep";
import SuccessPage from "./pages/booking/SuccessPage";

export default function App() {
  const location = useLocation();

  // Sync Telegram theme CSS variables on mount
  useEffect(() => {
    if (!tg) return;
    const params = tg.themeParams;
    const root = document.documentElement;
    if (params.bg_color) root.style.setProperty("--tg-theme-bg-color", params.bg_color);
    if (params.text_color) root.style.setProperty("--tg-theme-text-color", params.text_color);
    if (params.hint_color) root.style.setProperty("--tg-theme-hint-color", params.hint_color);
    if (params.link_color) root.style.setProperty("--tg-theme-link-color", params.link_color);
    if (params.button_color) root.style.setProperty("--tg-theme-button-color", params.button_color);
    if (params.button_text_color) root.style.setProperty("--tg-theme-button-text-color", params.button_text_color);
    if (params.secondary_bg_color) root.style.setProperty("--tg-theme-secondary-bg-color", params.secondary_bg_color);
  }, []);

  return (
    <div key={location.pathname} className="page-enter">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/appointments" element={<AppointmentsPage />} />
        <Route path="/pricelist" element={<PricelistPage />} />
        <Route path="/booking/master" element={<MasterStep />} />
        <Route path="/booking/date" element={<DateStep />} />
        <Route path="/booking/time" element={<TimeStep />} />
        <Route path="/booking/confirm" element={<ConfirmStep />} />
        <Route path="/booking/success" element={<SuccessPage />} />
      </Routes>
    </div>
  );
}

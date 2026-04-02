import { apiClient } from "./client";

export interface AvailableDate {
  date: string;       // "2026-04-05"
  day_name: string;   // "Нд"
  has_slots: boolean; // computed on frontend from backend response
}

export interface TimeSlot {
  id: number;         // timeslot_id — needed for POST /booking/create
  start_time: string; // "09:00:00"
  end_time: string;   // "10:00:00"
  master_id: number;
}

export interface BookingCreatePayload {
  service_id: number;
  master_id: number;
  timeslot_id: number; // backend uses timeslot_id, not date+start_time
}

export interface BookingResponse {
  id: number;
  service_name: string;
  master_name: string;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
}

// ── response shapes from backend ──────────────────────────────────────────────

interface AvailableDatesResponse {
  // Backend returns ONLY dates that have slots — no has_slots field
  dates: Array<{ date: string; day_name: string }>;
}

interface AvailableSlotsResponse {
  date: string;
  slots: TimeSlot[];
}

interface BookingCreateResponse {
  appointment: BookingResponse;
}

// ── public API functions ───────────────────────────────────────────────────────

/**
 * Returns 14 days starting from today.
 * Dates present in the backend response are marked has_slots=true, rest false.
 */
export async function getAvailableDates(
  masterId: number,
  serviceId: number
): Promise<AvailableDate[]> {
  const { data } = await apiClient.get<AvailableDatesResponse>(
    "/booking/available-dates",
    { params: { master_id: masterId, service_id: serviceId } }
  );

  const availableSet = new Set(data.dates.map((d) => d.date));
  const dayNamesMap = Object.fromEntries(data.dates.map((d) => [d.date, d.day_name]));

  const DAY_NAMES_UK = ["Нд", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];
  const result: AvailableDate[] = [];
  const today = new Date();

  for (let i = 0; i < 14; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const iso = d.toISOString().slice(0, 10); // "2026-04-05"
    result.push({
      date: iso,
      day_name: dayNamesMap[iso] ?? DAY_NAMES_UK[d.getDay()],
      has_slots: availableSet.has(iso),
    });
  }
  return result;
}

export async function getAvailableSlots(
  masterId: number,
  serviceId: number,
  date: string
): Promise<TimeSlot[]> {
  const { data } = await apiClient.get<AvailableSlotsResponse>(
    "/booking/available-slots",
    { params: { master_id: masterId, service_id: serviceId, date } }
  );
  return data.slots;
}

export async function createBooking(
  payload: BookingCreatePayload
): Promise<BookingResponse> {
  const { data } = await apiClient.post<BookingCreateResponse>(
    "/booking/create",
    payload
  );
  return data.appointment;
}

import { create } from "zustand";
import type { Service, Master } from "../api/catalog";
import type { TimeSlot } from "../api/booking";

interface BookingState {
  service: Service | null;
  master: Master | null;
  date: string | null;
  slot: TimeSlot | null; // slot.id = timeslot_id for POST /booking/create

  setService: (service: Service) => void;
  setMaster: (master: Master) => void;
  setDate: (date: string) => void;
  setSlot: (slot: TimeSlot) => void;
  reset: () => void;
}

export const useBookingStore = create<BookingState>((set) => ({
  service: null,
  master: null,
  date: null,
  slot: null,

  setService: (service) => set({ service, master: null, date: null, slot: null }),
  setMaster: (master) => set({ master, date: null, slot: null }),
  setDate: (date) => set({ date, slot: null }),
  setSlot: (slot) => set({ slot }),
  reset: () => set({ service: null, master: null, date: null, slot: null }),
}));

import { apiClient } from "./client";

export interface Appointment {
  id: number;
  service_name: string;
  master_name: string;
  date: string;
  start_time: string;
  end_time: string;
  price: number | null;
  status: "pending" | "confirmed" | "cancelled" | "completed";
}

interface AppointmentsResponse {
  appointments: Appointment[];
}

export async function getAppointments(): Promise<Appointment[]> {
  const { data } = await apiClient.get<AppointmentsResponse>("/appointments");
  return data.appointments;
}

export async function cancelAppointment(id: number): Promise<void> {
  await apiClient.post(`/appointments/${id}/cancel`);
}

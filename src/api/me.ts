import { apiClient } from "./client";

export interface UpcomingAppointment {
  id: number;
  service_name: string;
  master_name: string;
  date: string;
  start_time: string;
}

export interface MeResponse {
  first_name: string;
  total_visits: number;
  upcoming_appointment: UpcomingAppointment | null;
}

export async function getMe(): Promise<MeResponse> {
  const { data } = await apiClient.get<MeResponse>("/me");
  return data;
}

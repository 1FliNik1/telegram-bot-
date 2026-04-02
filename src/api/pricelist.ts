import { apiClient } from "./client";

export interface PricelistItem {
  name: string;
  price: number;
  price_max: number | null;
  duration_minutes: number;
}

export interface PricelistCategory {
  name: string;
  emoji: string | null;
  services: PricelistItem[];
}

interface PricelistResponse {
  salon_name: string;
  categories: PricelistCategory[];
}

export async function getPricelist(): Promise<PricelistCategory[]> {
  const { data } = await apiClient.get<PricelistResponse>("/pricelist");
  return data.categories;
}

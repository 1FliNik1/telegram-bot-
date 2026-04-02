import { apiClient } from "./client";

export interface Category {
  id: number;
  name: string;
  emoji: string | null;
  services_count: number;
}

export interface Service {
  id: number;
  name: string;
  description: string | null;
  price: number;
  price_max: number | null;
  duration_minutes: number;
  // Backend stores Telegram file_id, not a URL — we treat it as null for <img>
  photo_url: string | null;
  masters_count: number;
}

export interface Master {
  id: number;
  name: string;
  specialization: string | null;
  bio: string | null;
  avatar_url: string | null;
  custom_price: number | null;
  custom_duration: number | null;
}

export interface ServiceDetail extends Service {
  masters: Master[];
}

// ── response shapes from backend ──────────────────────────────────────────────

interface CategoriesResponse {
  categories: Array<{
    id: number;
    name: string;
    emoji: string | null;
    services_count: number;
  }>;
}

interface ServicesInCategoryResponse {
  services: Array<{
    id: number;
    name: string;
    description: string | null;
    price: number;
    price_max: number | null;
    duration_minutes: number;
    photo_file_id: string | null;
    masters_count: number;
  }>;
}

interface ServiceDetailResponse {
  service: {
    id: number;
    name: string;
    description: string | null;
    price: number;
    price_max: number | null;
    duration_minutes: number;
    photo_file_id: string | null;
    masters_count: number;
  };
  masters: Array<{
    id: number;
    name: string;
    specialization: string | null;
    bio: string | null;
    photo_file_id: string | null;
    custom_price: number | null;
    custom_duration: number | null;
  }>;
}

// ── public API functions ───────────────────────────────────────────────────────

export async function getCategories(): Promise<Category[]> {
  const { data } = await apiClient.get<CategoriesResponse>("/catalog/categories");
  return data.categories;
}

export async function getServices(categoryId: number | null): Promise<Service[]> {
  const url =
    categoryId != null
      ? `/catalog/categories/${categoryId}/services`
      : "/catalog/services";
  const { data } = await apiClient.get<ServicesInCategoryResponse>(url);
  return data.services.map((s) => ({
    ...s,
    photo_url: null, // photo_file_id can't be used as <img src>
  }));
}

export async function getServiceDetail(serviceId: number): Promise<ServiceDetail> {
  const { data } = await apiClient.get<ServiceDetailResponse>(
    `/catalog/services/${serviceId}`
  );
  return {
    ...data.service,
    photo_url: null,
    masters: data.masters.map((m) => ({
      ...m,
      avatar_url: null,
    })),
  };
}

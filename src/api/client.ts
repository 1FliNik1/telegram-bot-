import axios from "axios";
import { getInitData } from "../telegram";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const initData = getInitData();
  if (initData) {
    config.headers.Authorization = `tma ${initData}`;
  }
  return config;
});

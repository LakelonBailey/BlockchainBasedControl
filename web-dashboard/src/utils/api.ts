import axios from "axios";
import { API_ORIGIN } from "../constants/api";
import { AuthService } from "./auth";
import { showErrorSnackbar } from "./feedback";

const api = axios.create({
  baseURL: API_ORIGIN,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = new AuthService().getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    showErrorSnackbar("We experienced an error processing your request.");
    console.log(error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(undefined, (error) => {
  showErrorSnackbar("We experienced an error processing your request.");
  return Promise.reject(error);
});

export default api;

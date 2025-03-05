import { API_ORIGIN } from "../constants/api";
import { IAuthProvider } from "react-oauth2-code-pkce";
import { authTokenLocalStorageKey } from "../constants/auth";

export const authConfig: IAuthProvider["authConfig"] = {
  clientId: import.meta.env.VITE_OAUTH_CLIENT_ID as string,
  authorizationEndpoint: `${API_ORIGIN}/o/authorize/`,
  tokenEndpoint: `${API_ORIGIN}/o/token/`,
  redirectUri: `${window.origin}/oauth/callback/`,
  scope: "openid",
  decodeToken: false,
  autoLogin: true,
};

export class AuthService {
  getToken() {
    return localStorage.getItem(authTokenLocalStorageKey);
  }
  setToken(token: string) {
    localStorage.setItem(authTokenLocalStorageKey, token);
  }
  clearToken() {
    localStorage.removeItem(authTokenLocalStorageKey);
  }
  isLoggedIn() {
    return !!this.getToken();
  }
}

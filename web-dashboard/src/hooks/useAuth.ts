import { useContext } from "react";
import { AuthContext } from "react-oauth2-code-pkce";

export default function useAuth() {
  return useContext(AuthContext);
}

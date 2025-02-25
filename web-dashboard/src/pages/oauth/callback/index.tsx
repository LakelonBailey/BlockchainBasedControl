import { Box, CircularProgress } from "@mui/material";
import useAuth from "../../../hooks/useAuth";
import { authTokenLocalStorageKey } from "../../../constants/auth";

export default function Authenticating() {
  const { loginInProgress, token } = useAuth();
  if (token && !loginInProgress) {
    localStorage.setItem(authTokenLocalStorageKey, token);
    window.location.assign("/");
  }
  return (
    <Box
      sx={{
        height: "100dvh",
        width: "100vw",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <CircularProgress size={"100px"} />
    </Box>
  );
}

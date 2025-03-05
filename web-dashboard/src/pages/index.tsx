import { Box } from "@mui/material";
import useGet from "../hooks/useGet";
import { API_ORIGIN } from "../constants/api";

export default function Home() {
  const { data } = useGet(`${API_ORIGIN}/api/transactions/`, {
    params: {
      page: 1,
      limit: 10,
    },
  });
  if (data) {
    console.log(data);
  }
  return (
    <Box>
      <h2>Home</h2>
    </Box>
  );
}

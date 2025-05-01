import { Box, Typography } from "@mui/material";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid2";
import { Link } from "react-router-dom";

interface BoxLinkRoutes {
  path: string;
  title: string;
  description: string;
}
function BoxLink({ path, title, description }: BoxLinkRoutes) {
  return (
    <Grid size={6}>
      <Link to={path} style={{ textDecoration: "none" }}>
        <Box
          component={Paper}
          elevation={3}
          p={3}
          sx={{
            height: "200px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            backgroundColor: "rgba(0, 0, 0, 0.04)",
            transition: "transform 0.2s, box-shadow 0.2s",
            "&:hover": {
              transform: "translateY(-4px)",
              boxShadow: 6,
            },
            cursor: "pointer",
          }}
        >
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {description}
          </Typography>
        </Box>
      </Link>
    </Grid>
  );
}

export default function Home() {
  return (
    <Box sx={{ width: "100%", minHeight: "100vh", p: 4 }}>
      <Grid container spacing={2}>
        <BoxLink
          path="/analytics"
          title="Analytics Dashboard"
          description="Explore real-time metrics and uncover insights."
        />
        <BoxLink
          path="/meters"
          title="System Status"
          description="Monitor system health and performance metrics."
        />
      </Grid>
    </Box>
  );
}

import React from "react";
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Button,
} from "@mui/material";
import { Menu } from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import { Link } from "react-router-dom";

interface LayoutProps {
  children: React.ReactNode;
}

const Offset = styled("div")(({ theme }) => theme.mixins.toolbar);

export default function Layout({ children }: LayoutProps) {
  return (
    <Box>
      <AppBar position="fixed" sx={{ backgroundColor: "#FF8200" }}>
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
          >
            <Menu />
          </IconButton>

          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Blockchain Based Control
          </Typography>

          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              color="inherit"
              component={Link}
              to="/analytics"
              sx={{ textTransform: "none" }}
            >
              Analytics Dashboard
            </Button>
            <Button
              color="inherit"
              component={Link}
              to="/meters"
              sx={{ textTransform: "none" }}
            >
              System Status
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Offset />
      {children}
    </Box>
  );
}

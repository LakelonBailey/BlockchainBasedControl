import React from "react";
import { AppBar, Toolbar, IconButton, Typography, Box } from "@mui/material";
import { Menu } from "@mui/icons-material";
import { styled } from "@mui/material/styles";

interface LayoutProps {
  children: React.ReactNode;
}
const Offset = styled("div")(({ theme }) => theme.mixins.toolbar);

export default function Layout({ children }: LayoutProps) {
  return (
    <Box>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
          >
            <Menu />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            BlockChain Based Control
          </Typography>
        </Toolbar>
      </AppBar>
      <Offset />
      {children}
    </Box>
  );
}

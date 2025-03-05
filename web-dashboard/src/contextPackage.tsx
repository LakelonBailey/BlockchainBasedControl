import React from "react";
import { AuthProvider } from "react-oauth2-code-pkce";
import { authConfig } from "./utils/auth";
import { QueryClient, QueryClientProvider } from "react-query";
import { SnackbarProvider } from "notistack";
import CssBaseline from "@mui/material/CssBaseline";

interface Props {
  children: React.ReactNode;
}
const queryClient = new QueryClient();

export default function ContextPackage({ children }: Props) {
  return (
    <AuthProvider authConfig={authConfig}>
      <QueryClientProvider client={queryClient}>
        <SnackbarProvider>
          <CssBaseline />
          {children}
        </SnackbarProvider>
      </QueryClientProvider>
    </AuthProvider>
  );
}

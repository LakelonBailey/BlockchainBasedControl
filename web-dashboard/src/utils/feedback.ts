import { enqueueSnackbar } from "notistack";

export function showSuccessSnackbar(message: string) {
  enqueueSnackbar(message, {
    variant: "success",
    anchorOrigin: {
      horizontal: "right",
      vertical: "top",
    },
    autoHideDuration: 2000,
  });
}

export function showErrorSnackbar(message: string) {
  enqueueSnackbar(message, {
    variant: "error",
    anchorOrigin: {
      horizontal: "right",
      vertical: "top",
    },
    autoHideDuration: 4000,
  });
}

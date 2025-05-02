import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemButtonProps,
  ListItemText,
  Paper,
  Tooltip,
  Typography,
  Button,
} from "@mui/material";
import { CheckCircle, HighlightOff } from "@mui/icons-material";
import { API_ORIGIN } from "../../constants/api";
import useGet from "../../hooks/useGet";
import useWebSocket, { ReceiveType } from "../../hooks/useWebSocket";
import useDisclosure from "../../hooks/useDisclosure";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface SmartMeter {
  uuid: string;
  last_ping_ts: string;
  total_orders: number;
}

interface SmartMeterListItemProps {
  smartMeter: SmartMeter;
}

// Defines the active interval threshold (in seconds)
const ACTIVE_METER_INTERVAL = 20;

// Compute whether a meter is active based on its last ping timestamp
const isActiveSmartMeter = (smartMeter: SmartMeter) => {
  const lastPing = new Date(smartMeter.last_ping_ts).getTime();
  const now = Date.now();
  return (now - lastPing) / 1000 < ACTIVE_METER_INTERVAL;
};

// Reusable component to display fields uniformly
interface FieldDisplayProps {
  label: string;
  value: React.ReactNode;
}
const FieldDisplay = ({ label, value }: FieldDisplayProps) => (
  <Box sx={{ display: "flex", alignItems: "center", mb: 0.5 }}>
    <Typography variant="subtitle2" sx={{ fontWeight: "bold", mr: 1 }}>
      {label}:
    </Typography>
    <Typography variant="body2">{value}</Typography>
  </Box>
);

function SmartMeterListItem({ smartMeter, ...props }: SmartMeterListItemProps) {
  const active = isActiveSmartMeter(smartMeter);
  return (
    <ListItemButton
      {...props}
      divider
      LinkComponent={Link}
      to={`/analytics?smart_meter_id=${smartMeter.uuid}`}
    >
      <ListItemText
        disableTypography
        primary={
          <Box
            display="flex"
            alignItems="center"
            justifyContent="space-between"
          >
            <Typography variant="body1" fontWeight="bold">
              ID: {smartMeter.uuid}
            </Typography>
            {active ? (
              <Tooltip title="Active">
                <Box display="flex" alignItems="center">
                  <Typography variant="overline">Active</Typography>
                  <CheckCircle color="success" sx={{ ml: 1 }} />
                </Box>
              </Tooltip>
            ) : (
              <Tooltip title="Inactive">
                <Box display="flex" alignItems="center">
                  <Typography variant="overline">Inactive</Typography>
                  <HighlightOff color="error" sx={{ ml: 1 }} />
                </Box>
              </Tooltip>
            )}
          </Box>
        }
        secondary={
          <Box mt={1}>
            <FieldDisplay
              label="Last Ping"
              value={new Date(smartMeter.last_ping_ts).toLocaleString()}
            />
            <FieldDisplay
              label="Total Orders"
              value={smartMeter.total_orders}
            />
          </Box>
        }
      />
    </ListItemButton>
  );
}

export default function Meters() {
  const { data } = useGet(`${API_ORIGIN}/api/meters/`);

  const [smartMeters, setSmartMeters] = useState<Record<string, SmartMeter>>(
    {}
  );

  // Merge or replace fetched pages
  useEffect(() => {
    if (data) {
      const entries = Object.fromEntries(
        data.results.map((m: SmartMeter) => [m.uuid, m])
      );
      setSmartMeters(entries);
    }
  }, [data]);

  // Handle WebSocket meter status updates
  useWebSocket({
    path: "/ws/meters/status/",
    enabled: true,
    messageTypes: {
      receive: { METER_STATUS: "meter_status" },
      send: {},
    },
    onMessage: useCallback((msg: ReceiveType) => {
      if (msg.type === "meter_status") {
        const info = msg.data as {
          last_ping_ts: string;
          smart_meter_id: string;
          total_orders?: number;
        };
        setSmartMeters((prev) => ({
          ...prev,
          [info.smart_meter_id]: {
            ...prev[info.smart_meter_id],
            last_ping_ts: info.last_ping_ts,
            total_orders:
              info.total_orders ?? prev[info.smart_meter_id].total_orders,
          },
        }));
      }
    }, []),
  });

  return (
    <>
      <Box
        p={2}
        sx={{ backgroundColor: "rgba(0, 0, 0, .1)", minHeight: "100vh" }}
      >
        <Typography variant="h4" gutterBottom fontWeight={"bold"}>
          Smart Meter Status
        </Typography>

        <List component={Paper}>
          {Object.values(smartMeters).map((meter) => (
            <SmartMeterListItem key={meter.uuid} smartMeter={meter} />
          ))}
        </List>
      </Box>
    </>
  );
}

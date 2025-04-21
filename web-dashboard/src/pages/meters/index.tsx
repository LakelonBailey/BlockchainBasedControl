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
} from "@mui/material";
import { CheckCircle, HighlightOff } from "@mui/icons-material";
import { API_ORIGIN } from "../../constants/api";
import useGet from "../../hooks/useGet";
import useWebSocket, { ReceiveType } from "../../hooks/useWebSocket";
import useDisclosure from "../../hooks/useDisclosure";
import { useCallback, useEffect, useState } from "react";
import { formatSeconds } from "../../utils/formatting";

interface SmartMeter {
  uuid: string;
  last_ping_ts: string;
  total_transactions: number;
}

interface SmartMeterListItemProps {
  smartMeter: SmartMeter;
  currentTime: Date;
}

// Defines the active interval threshold (in seconds)
const ACTIVE_METER_INTERVAL = 20;

// Compute whether a meter is active using the current time
const isActiveSmartMeter = (smartMeter: SmartMeter, currentTime: Date) => {
  const timeSincePing = Math.round(
    (currentTime.getTime() - new Date(smartMeter.last_ping_ts).getTime()) / 1000
  );
  return timeSincePing < ACTIVE_METER_INTERVAL;
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

// SmartMeter list item component now receives the current time via props.
function SmartMeterListItem({
  smartMeter,
  currentTime,
  ...props
}: SmartMeterListItemProps & ListItemButtonProps) {
  const timeSincePing = Math.round(
    (currentTime.getTime() - new Date(smartMeter.last_ping_ts).getTime()) / 1000
  );

  return (
    <ListItemButton {...props} divider>
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
            {isActiveSmartMeter(smartMeter, currentTime) ? (
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
              label="Time since last ping"
              value={formatSeconds(timeSincePing)}
            />
            <FieldDisplay
              label="Total Transactions"
              value={smartMeter.total_transactions}
            />
          </Box>
        }
      />
    </ListItemButton>
  );
}

export default function Meters() {
  const { data } = useGet(`${API_ORIGIN}/api/meters/`, {
    params: { page: 1, limit: 10 },
  });
  const [smartMeters, setSmartMeters] = useState<Record<string, SmartMeter>>(
    {}
  );
  const [selectedSmartMeterId, setSelectedSmartMeterId] = useState<
    string | null
  >(null);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const smartMeterAnalysisDisc = useDisclosure();

  // Global timer: update current time and re-evaluate each meter's active status every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Update state when new data is fetched from the API
  useEffect(() => {
    if (data) {
      const newSmartMeterMap = Object.fromEntries(
        (data.results as SmartMeter[]).map((smartMeter) => [
          smartMeter.uuid,
          smartMeter,
        ])
      ) as Record<string, SmartMeter>;
      setSmartMeters(newSmartMeterMap);
    }
  }, [data]);

  // Update smart meter details upon receiving WebSocket messages
  useWebSocket({
    path: "/ws/meters/status/",
    enabled: true,
    messageTypes: {
      receive: { METER_STATUS: "meter_status" },
      send: {},
    },
    onMessage: useCallback((data: ReceiveType) => {
      if (data.type === "meter_status") {
        const smartMeterInfo = data.data as {
          last_ping_ts: string;
          smart_meter_id: string;
          total_transactions?: number;
        };
        console.log(
          `Received ping from meter: ${smartMeterInfo.smart_meter_id}`
        );
        setSmartMeters((prev) => ({
          ...prev,
          [smartMeterInfo.smart_meter_id]: {
            ...prev[smartMeterInfo.smart_meter_id],
            last_ping_ts: smartMeterInfo.last_ping_ts,
            total_transactions:
              smartMeterInfo.total_transactions ??
              prev[smartMeterInfo.smart_meter_id]?.total_transactions ??
              0,
          },
        }));
      }
    }, []),
  });

  return (
    <>
      <Dialog {...smartMeterAnalysisDisc.getDisclosureProps()}>
        <DialogTitle component={"div"}>
          <Typography variant="h5">Smart Meter Analysis</Typography>
          <Typography variant="subtitle2" sx={{ color: "rgba(0, 0, 0, .6)" }}>
            ID: {selectedSmartMeterId}
          </Typography>
        </DialogTitle>
        {selectedSmartMeterId && (
          <DialogContent>
            Time since last ping:{" "}
            {formatSeconds(
              Math.round(
                (new Date().getTime() -
                  new Date(
                    smartMeters[selectedSmartMeterId].last_ping_ts
                  ).getTime()) /
                  1000
              )
            )}
          </DialogContent>
        )}
      </Dialog>
      <Box p={2} sx={{ backgroundColor: "lightgray", minHeight: "100vh" }}>
        <Typography variant="h5" fontWeight="bold" mb={2}>
          Smart Meter Status
        </Typography>
        <List component={Paper}>
          {Object.values(smartMeters).map((smartMeter) => (
            <SmartMeterListItem
              key={smartMeter.uuid}
              smartMeter={smartMeter}
              currentTime={currentTime}
              onClick={() => {
                console.log(`Clicked: ${smartMeter.uuid}`);
                setSelectedSmartMeterId(smartMeter.uuid);
                smartMeterAnalysisDisc.onOpen();
              }}
            />
          ))}
        </List>
      </Box>
    </>
  );
}

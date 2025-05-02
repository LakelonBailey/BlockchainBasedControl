import { useState } from "react";
import {
  Box,
  Grid2 as Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
} from "@mui/material";
import { LineChart } from "@mui/x-charts/LineChart";
import { BarChart } from "@mui/x-charts/BarChart";
import useGet from "../../hooks/useGet";
import { useSearchParams } from "react-router-dom";

export default function AnalyticsDashboard() {
  const [searchParams] = useSearchParams();
  const [meterInput, setMeterInput] = useState(
    searchParams.get("smart_meter_id") || ""
  );
  const params = meterInput ? { smart_meter_id: meterInput } : {};

  const { data: summary } = useGet("/api/analytics/summary/", { params });
  const { data: txTime } = useGet("/api/analytics/transactions_over_time/", {
    params,
  });
  const { data: energyFlow } = useGet("/api/analytics/energy_flow/", {
    params,
  });
  const { data: avgPrice } = useGet("/api/analytics/avg_price_over_time/", {
    params,
  });

  // Data transforms
  const txDates = txTime?.map((p) => new Date(p.date)) ?? [];
  const txCounts = txTime?.map((p) => p.count ?? 0) ?? [];

  // For bar chart, use string categories (YYYY-MM-DD)
  const flowDates = energyFlow?.map((p) => p.date) ?? [];
  const boughtSeries = energyFlow?.map((p) => p.energy_bought ?? 0) ?? [];
  const soldSeries = energyFlow?.map((p) => p.energy_sold ?? 0) ?? [];

  const priceDates = avgPrice?.map((p) => new Date(p.date)) ?? [];
  const priceSeries = avgPrice?.map((p) => p.avg_price ?? 0) ?? [];

  // Date formatter for time axes
  const dateFormatter = (value: Date | number) => {
    const d = value instanceof Date ? value : new Date(value);
    return d.toLocaleDateString();
  };

  // Prepare cards with optional subtext
  const cards = [
    {
      label: "Total Orders",
      value: summary?.total_orders?.toString(),
      subtext: `(${summary?.total_buy_orders ?? 0} buy | ${
        summary?.total_sell_orders ?? 0
      } sell)`,
    },
    {
      label: "Total Transactions",
      value: summary?.total_transactions?.toString(),
      subtext: `(${summary?.total_buy_transactions ?? 0} buy | ${
        summary?.total_sell_transactions ?? 0
      } sell)`,
    },
    { label: "Energy Bought (kWh)", value: summary?.total_energy_bought },
    { label: "Energy Sold (kWh)", value: summary?.total_energy_sold },
  ];

  return (
    <Box
      p={2}
      sx={{
        backgroundColor: "rgba(0, 0, 0, .1)",
      }}
    >
      <Typography variant="h4" gutterBottom fontWeight={"bold"}>
        Blockchain Energy Dashboard
      </Typography>

      <Box mb={2} display="flex" alignItems="center">
        <TextField
          label="Filter meters (comma-sep UUIDs)"
          value={meterInput}
          onChange={(e) => setMeterInput(e.target.value)}
          fullWidth
        />
        <Button
          sx={{ ml: 2 }}
          onClick={() => {
            setMeterInput("");
          }}
          variant="contained"
        >
          Clear
        </Button>
      </Box>

      <Grid container spacing={2} mb={3}>
        {cards.map((card) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={card.label}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  {card.label}
                </Typography>
                <Typography variant="h5">{card.value ?? "—"}</Typography>
                {card.subtext && (
                  <Typography variant="body2" color="textSecondary">
                    {card.subtext}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Transactions Over Time */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Transactions Over Time
          </Typography>
          <LineChart
            xAxis={[
              {
                data: txDates,
                scaleType: "time",
                valueFormatter: dateFormatter,
              },
            ]}
            series={[{ data: txCounts }]}
            height={300}
          />
        </CardContent>
      </Card>

      {/* Energy Flow */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Energy Flow (Buy vs Sell)
          </Typography>
          <BarChart
            xAxis={[{ data: flowDates, scaleType: "band" }]}
            series={[
              { data: boughtSeries, label: "Bought (kWh)" },
              { data: soldSeries, label: "Sold (kWh)" },
            ]}
            height={300}
          />
        </CardContent>
      </Card>

      {/* Average Price Over Time */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Average Executed Price Over Time
          </Typography>
          <LineChart
            xAxis={[
              {
                data: priceDates,
                scaleType: "time",
                valueFormatter: dateFormatter,
              },
            ]}
            series={[{ data: priceSeries }]}
            height={300}
          />
        </CardContent>
      </Card>
    </Box>
  );
}

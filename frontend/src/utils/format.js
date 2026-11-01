export function inr(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: digits,
  }).format(Number(value));
}

export function num(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: digits }).format(Number(value));
}

export function pct(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(digits)}%`;
}

export function downloadCsv(filename, rows) {
  if (!rows?.length) return;
  const headers = Object.keys(rows[0]);
  const csv = [headers.join(","), ...rows.map((r) => headers.map((h) => csvCell(r[h])).join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function csvCell(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (text.includes(",") || text.includes('"')) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

export const FILTER_OPTIONS = {
  cities: ["Ahmedabad", "Bengaluru", "Chennai", "Delhi", "Hyderabad", "Kolkata", "Mumbai", "Pune"],
  categories: ["Beverages", "Dairy", "Fruits", "Grocery", "Home Care", "Personal Care", "Snacks", "Vegetables"],
  brands: ["Amul", "Britannia", "HUL", "ITC", "Nestle", "Parle", "PepsiCo", "Tata"],
  channels: ["Offline", "Omnichannel", "Online"],
  storeFormats: ["Express", "Hyper", "Super"],
  paymentModes: ["Card", "Cash", "UPI", "Wallet"],
};

export const FEATURE_LABELS = {
  lag_1: "Previous-day sales",
  lag_7: "Sales 7 days ago",
  lag_14: "Sales 14 days ago",
  lag_30: "Sales 30 days ago",
  rolling_mean_7: "Average sales, last 7 days",
  rolling_mean_14: "Average sales, last 14 days",
  rolling_mean_30: "Average sales, last 30 days",
  rolling_std_7: "How much sales varied, last 7 days",
  rolling_std_30: "How much sales varied, last 30 days",
  rolling_min_7: "Lowest sales, last 7 days",
  rolling_max_7: "Highest sales, last 7 days",
  day_of_week: "Day of week",
  day_of_month: "Day of month",
  week_of_year: "Week of year",
  is_weekend: "Weekend",
  is_month_start: "Start of month",
  is_month_end: "End of month",
  Category: "Product category",
  year: "Year",
  month: "Month",
  quarter: "Quarter",
  day: "Calendar day",
};

export function featureLabel(name) {
  return FEATURE_LABELS[name] || name;
}

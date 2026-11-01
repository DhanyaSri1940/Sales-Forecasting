export function seriesExtent(rows, keys) {
  let min = Infinity;
  let max = -Infinity;
  for (const row of rows || []) {
    for (const key of keys) {
      const raw = row?.[key];
      if (raw == null || raw === "") continue;
      const value = Number(raw);
      if (!Number.isFinite(value)) continue;
      min = Math.min(min, value);
      max = Math.max(max, value);
    }
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) return { min: 0, max: 1 };
  return { min, max };
}

export function seriesMax(rows, keys) {
  return seriesExtent(rows, keys).max;
}

export function niceMax(maxValue) {
  const max = Math.max(Number(maxValue) || 0, 1);
  const pow = 10 ** Math.floor(Math.log10(max));
  const n = max / pow;
  const nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
  return nice * pow;
}

export function formatRupeeTick(value, maxValue) {
  const v = Number(value);
  if (!Number.isFinite(v)) return "";
  const max = Math.max(Number(maxValue) || Math.abs(v), 1);
  const abs = Math.abs(v);
  if (max >= 10_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (max >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
  if (max >= 100_000) return `${Math.round(v / 1000)}k`;
  if (max >= 10_000) return `${(v / 1000).toFixed(1)}k`;
  if (max >= 1_000) return `${(v / 1000).toFixed(2)}k`;
  if (abs >= 100) return abs.toFixed(0);
  return abs.toFixed(0);
}

export function niceStep(span, targetTicks = 5) {
  const raw = Math.max(Number(span) || 1, 1) / Math.max(targetTicks, 2);
  const pow = 10 ** Math.floor(Math.log10(raw));
  const n = raw / pow;
  const nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10;
  return nice * pow;
}

export function rupeeAxis(rows, keys, { fromZero = true } = {}) {
  const { min, max } = seriesExtent(rows, keys);
  if (fromZero) {
    const top = niceMax(max * 1.05);
    return {
      domain: [0, top],
      ticks: undefined,
      tickCount: 5,
      width: top >= 1_000_000 ? 58 : 52,
      tickFormatter: (value) => formatRupeeTick(value, top),
    };
  }
  const span = Math.max(max - min, Math.abs(max) * 0.04, 1);
  const pad = span * 0.08;
  const step = niceStep(span + 2 * pad, 5);
  const bottom = Math.max(0, Math.floor((min - pad) / step) * step);
  const top = Math.ceil((max + pad) / step) * step;
  const ticks = [];
  for (let value = bottom; value <= top + step / 2; value += step) {
    ticks.push(value);
  }
  return {
    domain: [bottom, top],
    ticks,
    tickCount: ticks.length,
    width: top >= 1_000_000 ? 62 : 52,
    tickFormatter: (value) => formatRupeeTick(value, top),
  };
}

export function monthStartTicks(rows, dateKey = "Date") {
  const ticks = [];
  let last = "";
  for (const row of rows || []) {
    const date = row[dateKey];
    if (!date) continue;
    const ym = String(date).slice(0, 7);
    if (ym !== last) {
      ticks.push(date);
      last = ym;
    }
  }
  return ticks;
}

export function horizonDateTicks(rows, horizon, dateKey = "Date") {
  const dates = (rows || []).map((row) => row[dateKey]).filter(Boolean);
  const step = Number(horizon) === 7 ? 1 : Number(horizon) === 14 ? 2 : 5;
  if (!dates.length) return [];
  const ticks = dates.filter((_, index) => index % step === 0);
  if (ticks[ticks.length - 1] !== dates[dates.length - 1]) ticks.push(dates[dates.length - 1]);
  return ticks;
}

export function spacedDateTicks(rows, dateKey = "Date", maxTicks = 7) {
  const dates = (rows || []).map((row) => row[dateKey]).filter(Boolean);
  if (dates.length <= maxTicks) return dates;
  const step = Math.ceil((dates.length - 1) / (maxTicks - 1));
  const ticks = [];
  for (let i = 0; i < dates.length; i += step) ticks.push(dates[i]);
  if (ticks[ticks.length - 1] !== dates[dates.length - 1]) ticks.push(dates[dates.length - 1]);
  return ticks;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatChartDate(iso) {
  const part = String(iso || "").slice(0, 10);
  const match = part.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return iso;
  const day = Number(match[3]);
  const month = MONTHS[Number(match[2]) - 1];
  return `${day} ${month}`;
}

export function spanDays(rows, dateKey = "Date") {
  const dates = (rows || []).map((row) => row[dateKey]).filter(Boolean);
  if (dates.length < 2) return dates.length;
  const first = new Date(`${dates[0]}T00:00:00`);
  const last = new Date(`${dates[dates.length - 1]}T00:00:00`);
  return Math.max(1, Math.round((last - first) / 86400000) + 1);
}

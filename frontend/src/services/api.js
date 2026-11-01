const API_BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* keep default */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

export const api = {
  dashboard: () => request("/api/dashboard"),
  forecast: (params) => request(`/api/forecast?${new URLSearchParams(clean(params))}`),
  categories: (params) => request(`/api/analytics/categories?${new URLSearchParams(clean(params))}`),
  cities: (params) => request(`/api/analytics/cities?${new URLSearchParams(clean(params))}`),
  brands: (params) => request(`/api/analytics/brands?${new URLSearchParams(clean(params))}`),
  channels: (params) => request(`/api/analytics/channels?${new URLSearchParams(clean(params))}`),
  storeFormats: (params) => request(`/api/analytics/store-formats?${new URLSearchParams(clean(params))}`),
  paymentModes: (params) => request(`/api/analytics/payment-modes?${new URLSearchParams(clean(params))}`),
  loyalty: (params) => request(`/api/analytics/loyalty?${new URLSearchParams(clean(params))}`),
  daily: (params) => request(`/api/analytics/daily?${new URLSearchParams(clean(params))}`),
  inventory: (params) => request(`/api/inventory/risk?${new URLSearchParams(clean(params))}`),
  model: () => request("/api/model/performance"),
  features: () => request("/api/model/features"),
  insight: (question) => request("/api/insights", { method: "POST", body: JSON.stringify({ question }) }),
};

function clean(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
  );
}

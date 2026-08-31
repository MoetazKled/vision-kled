export type Lead = {
  id: number;
  name: string;
  phone: string;
  business_type: string;
  profession: string;
  has_website: string;
  how_found: string;
  country: string;
  language: string;
  product: string;
  status: string;
  source: string;
  consent_opt_in: boolean;
  opted_out: boolean;
  notes: string;
};

export type Product = {
  slug: string;
  name_ar: string;
  audience: string;
  price: string;
  setup: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || "تعذر الاتصال بالخادم");
  }
  return response.json() as Promise<T>;
}

export const api = {
  stats: () => request<Record<string, number>>("/api/stats"),
  products: () => request<Product[]>("/api/products"),
  leads: () => request<Lead[]>("/api/leads"),
  createLead: (payload: Partial<Lead>) =>
    request<Lead>("/api/leads", { method: "POST", body: JSON.stringify(payload) }),
  trialLead: () => request<Lead>("/api/leads/trial", { method: "POST" }),
  deleteLead: (id: number) => request<{ ok: boolean }>(`/api/leads/${id}`, { method: "DELETE" }),
  lead: (id: number) =>
    request<{
      lead: Lead;
      history: { role: string; content: string }[];
      phase: string;
      demos: { slug: string; url: string; template: string }[];
    }>(`/api/leads/${id}`),
  start: (id: number) =>
    request<{ reply: string; history: { role: string; content: string }[] }>(
      `/api/leads/${id}/start`,
      { method: "POST" }
    ),
  chat: (id: number, message: string, forceDemo = false) =>
    request<{ reply: string; lead: Lead; phase: string; demo_url?: string }>(
      `/api/leads/${id}/chat`,
      { method: "POST", body: JSON.stringify({ message, force_demo: forceDemo }) }
    ),
  buildDemo: (id: number) =>
    request<{ reply: string; demo_url?: string }>(`/api/leads/${id}/build-demo`, {
      method: "POST",
    }),
  subscribe: (id: number) =>
    request(`/api/leads/${id}/subscribe`, {
      method: "POST",
      body: JSON.stringify({ plan: "portfolio_monthly", price_usd: "12" }),
    }),
  demos: () =>
    request<{ id: number; lead_id: number; slug: string; url: string; template: string }[]>(
      "/api/demos"
    ),
  subscriptions: () =>
    request<{ id: number; lead_id: number; plan: string; price_usd: string; status: string }[]>(
      "/api/subscriptions"
    ),
};

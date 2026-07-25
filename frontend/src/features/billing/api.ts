import api from "@/lib/api";

export interface PlanInfo {
  name: string;
  display_name: string;
  price_monthly: number;
  limits: Record<string, unknown>;
  features: string[];
}

export interface SubscriptionInfo {
  id: number;
  plan: string;
  status: string;
  stripe_customer_id: string;
  current_period_end: string | null;
  trial_end: string | null;
  limits: Record<string, unknown>;
  created_at: string;
}

export const billingApi = {
  getPlans: () => api.get<PlanInfo[]>("/billing/plans/"),

  getSubscription: () =>
    api.get<SubscriptionInfo>("/billing/subscription/"),

  checkout: (plan: string) =>
    api.post<{ checkout_url: string }>("/billing/checkout/", { plan }),

  portal: () =>
    api.post<{ portal_url: string }>("/billing/portal/"),
};

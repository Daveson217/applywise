import { PricingCards } from "@/features/billing/components/pricing-cards";

export function PricingPage() {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-bold">
          Choose Your Plan
        </h1>
        <p className="mt-2 text-muted-foreground">
          Start free, upgrade when you need more power.
        </p>
      </div>

      <PricingCards />
    </div>
  );
}

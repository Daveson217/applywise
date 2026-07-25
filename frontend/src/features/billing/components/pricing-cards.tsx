import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { Check, Sparkles } from "lucide-react";

import { billingApi, type PlanInfo } from "../api";
import { useUsage } from "../usage-api";

export function PricingCards() {
  const { data: plans, isLoading } = useQuery({
    queryKey: ["billing", "plans"],
    queryFn: () => billingApi.getPlans().then((r) => r.data),
  });

  const { data: subscription } = useQuery({
    queryKey: ["billing", "subscription"],
    queryFn: () => billingApi.getSubscription().then((r) => r.data),
  });

  const { data: usage } = useUsage();

  // Beta / testing mode — payments disabled globally. Show a banner
  // instead of upgrade prompts.
  if (usage && !usage.payments_enabled) {
    return (
      <div className="mx-auto max-w-2xl">
        <Card className="border-primary/40 bg-primary/5">
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <Sparkles className="h-10 w-10 text-primary" />
            <h3 className="text-lg font-semibold">
              Everything's unlocked — you're in beta mode
            </h3>
            <p className="max-w-md text-sm text-muted-foreground">
              All features are enabled for every account while we're in early
              access. When we start charging, you'll see plan options here.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="grid gap-6 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-96 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {plans?.map((plan) => (
        <PricingCard
          key={plan.name}
          plan={plan}
          currentPlan={subscription?.plan || "free"}
        />
      ))}
    </div>
  );
}

function PricingCard({
  plan,
  currentPlan,
}: {
  plan: PlanInfo;
  currentPlan: string;
}) {
  const isCurrent = plan.name === currentPlan;
  const isPopular = plan.name === "pro";

  return (
    <Card
      className={cn(
        "relative flex flex-col",
        isPopular && "border-primary shadow-lg"
      )}
    >
      {isPopular && (
        <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
          Most Popular
        </Badge>
      )}
      <CardHeader>
        <CardTitle>{plan.display_name}</CardTitle>
        <CardDescription>
          {plan.price_monthly === 0 ? (
            <span className="text-3xl font-bold text-foreground">Free</span>
          ) : (
            <>
              <span className="text-3xl font-bold text-foreground">
                ${plan.price_monthly}
              </span>
              <span className="text-muted-foreground">/month</span>
            </>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1">
        <ul className="space-y-2">
          {plan.features.map((feature) => (
            <li key={feature} className="flex items-start gap-2 text-sm">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              {feature}
            </li>
          ))}
        </ul>
      </CardContent>
      <CardFooter>
        <Button
          className="w-full"
          variant={isCurrent ? "outline" : isPopular ? "default" : "secondary"}
          disabled={isCurrent}
        >
          {isCurrent ? "Current Plan" : `Upgrade to ${plan.display_name}`}
        </Button>
      </CardFooter>
    </Card>
  );
}

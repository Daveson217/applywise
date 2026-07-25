from django.urls import path

from . import views

urlpatterns = [
    path("billing/plans/", views.PlansView.as_view(), name="billing-plans"),
    path(
        "billing/subscription/",
        views.SubscriptionView.as_view(),
        name="billing-subscription",
    ),
    path("billing/checkout/", views.CheckoutView.as_view(), name="billing-checkout"),
    path("billing/portal/", views.BillingPortalView.as_view(), name="billing-portal"),
    path("billing/usage/", views.UsageView.as_view(), name="billing-usage"),
]

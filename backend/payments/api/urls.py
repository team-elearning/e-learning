from django.urls import path

from payments.api.views import MomoCreatePaymentView, MomoIPNView, PaymentHistoryView


urlpatterns = [
    path("momo/create/", MomoCreatePaymentView.as_view(), name="momo-create"),
    path("momo/ipn/", MomoIPNView.as_view(), name="momo-ipn"),
    path("history/", PaymentHistoryView.as_view(), name="payment-history"),
]

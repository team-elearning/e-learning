from __future__ import annotations

import base64
import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from payments.api.serializers import (
    MomoCreatePaymentSerializer,
    MomoIPNSerializer,
    PaymentHistorySerializer,
)
from payments.models import Payment, SubscriptionPlan
from payments.services import MomoGatewayError, get_momo_gateway


def _generate_order_id(user_id) -> str:
    user_part = str(user_id).replace("-", "")[:6].upper()
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"EDU{user_part}{ts}{suffix}"


def _encode_extra_data(payment: Payment) -> str:
    payload = {"payment_id": str(payment.id), "user_id": payment.user_id}
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")


class MomoCreatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MomoCreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plan = None
        if plan_id := data.get("plan_id"):
            plan = get_object_or_404(SubscriptionPlan, pk=plan_id)

        plan_name = data.get("plan_name") or (plan.name if plan else "Gói học")
        amount_number = int(data["amount"])
        order_info = data.get("order_info") or f"Thanh toán {plan_name}"

        payment = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=Decimal(str(amount_number)).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP),
            status="pending",
            metadata={
                "gateway": "momo",
                "plan_name": plan_name,
            },
        )

        order_id = _generate_order_id(request.user.id)
        request_id = uuid.uuid4().hex

        extra_data = _encode_extra_data(payment)

        gateway = get_momo_gateway()

        try:
            momo_response = gateway.create_payment(
                amount=amount_number,
                order_id=order_id,
                request_id=request_id,
                order_info=order_info[:250],
                extra_data=extra_data,
                redirect_url=data.get("redirect_url"),
            )
        except MomoGatewayError as exc:
            payment.status = "failed"
            payment.metadata["momo_error"] = exc.response
            payment.save(update_fields=["status", "metadata"])
            return Response({"detail": exc.message}, status=status.HTTP_502_BAD_GATEWAY)

        payment.transaction_id = order_id
        payment.metadata.update(
            {
                "momo_order_id": order_id,
                "momo_request_id": request_id,
                "momo_payload": momo_response,
            }
        )
        payment.save(update_fields=["transaction_id", "metadata"])

        response_data = {
            "paymentId": str(payment.id),
            "orderId": order_id,
            "requestId": request_id,
            "payUrl": momo_response.get("payUrl"),
            "deeplink": momo_response.get("deeplink"),
            "qrCodeUrl": momo_response.get("qrCodeUrl"),
            "resultCode": momo_response.get("resultCode"),
            "message": momo_response.get("message"),
        }
        return Response(response_data, status=status.HTTP_200_OK)


class MomoIPNView(APIView):
    """
    Endpoint for MoMo to notify payment result.
    """

    authentication_classes: list = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = MomoIPNSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: Dict[str, str] = serializer.validated_data

        gateway = get_momo_gateway()
        if not gateway.verify_ipn_signature(request.data):
            return Response({"resultCode": 1, "message": "Invalid signature"})

        extra_data = data.get("extraData") or ""
        payment_id = None
        try:
            decoded = base64.b64decode(extra_data).decode("utf-8") if extra_data else "{}"
            payment_id = json.loads(decoded).get("payment_id")
        except (ValueError, json.JSONDecodeError, KeyError):
            pass

        if not payment_id:
            return Response({"resultCode": 1, "message": "Payment not found"})

        payment = Payment.objects.filter(id=payment_id).first()
        if not payment:
            return Response({"resultCode": 1, "message": "Payment not found"})

        payment.metadata["momo_ipn"] = data

        if data["resultCode"] == 0:
            payment.status = "paid"
            payment.paid_at = timezone.now()
            payment.transaction_id = data.get("transId") or payment.transaction_id
        else:
            payment.status = "failed"
            payment.paid_at = None

        payment.save(update_fields=["status", "paid_at", "transaction_id", "metadata"])

        # MoMo expects resultCode/message in response
        return Response({"resultCode": 0, "message": "Confirm Success"})


class PaymentHistoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class PaymentHistoryView(generics.ListAPIView):
    serializer_class = PaymentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentHistoryPagination

    def get_queryset(self):
        queryset = Payment.objects.filter(user=self.request.user).order_by("-created_at", "-paid_at", "-pk")

        status_param = self.request.query_params.get("status")
        if status_param:
            status_param = status_param.lower()
            status_mapping = {
                "pending": ["pending"],
                "processing": ["pending"],
                "success": ["paid"],
                "failed": ["failed"],
                "refunded": ["refunded"],
            }
            payment_statuses = status_mapping.get(status_param)
            if payment_statuses:
                queryset = queryset.filter(status__in=payment_statuses)

        method = self.request.query_params.get("method")
        if method:
            queryset = queryset.filter(metadata__gateway__iexact=method)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        summary = self._build_summary(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["summary"] = summary
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data, "summary": summary})

    def _build_summary(self, queryset):
        total_success_amount = 0
        pending_count = 0
        success_count = 0
        failed_count = 0

        for payment in queryset:
            if payment.status == "paid":
                total_success_amount += int(payment.amount)
                success_count += 1
            elif payment.status == "pending":
                pending_count += 1
            elif payment.status == "failed":
                failed_count += 1

        return {
            "total_amount": total_success_amount,
            "pending_count": pending_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "currency": "VND",
        }

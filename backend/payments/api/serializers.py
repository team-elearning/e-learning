from rest_framework import serializers

from payments.models import Payment


class MomoCreatePaymentSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1000, max_value=50_000_000)
    plan_id = serializers.UUIDField(required=False)
    plan_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    redirect_url = serializers.URLField(required=False)
    order_info = serializers.CharField(required=False, allow_blank=True, max_length=255)


class MomoIPNSerializer(serializers.Serializer):
    accessKey = serializers.CharField()
    partnerCode = serializers.CharField()
    orderId = serializers.CharField()
    requestId = serializers.CharField()
    amount = serializers.CharField()
    orderInfo = serializers.CharField()
    orderType = serializers.CharField(required=False, allow_blank=True)
    transId = serializers.CharField(required=False, allow_blank=True)
    resultCode = serializers.IntegerField()
    message = serializers.CharField()
    payType = serializers.CharField(required=False, allow_blank=True)
    responseTime = serializers.CharField(required=False, allow_blank=True)
    extraData = serializers.CharField(required=False, allow_blank=True)
    signature = serializers.CharField()


class PaymentHistorySerializer(serializers.ModelSerializer):
    order_code = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    method = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    status_variant = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_code",
            "plan_name",
            "amount",
            "currency",
            "method",
            "status",
            "status_variant",
            "created_at",
            "paid_at",
        ]
        read_only_fields = fields

    def get_order_code(self, obj: Payment) -> str:
        return (
            obj.transaction_id
            or obj.metadata.get("momo_order_id")
            or f"PAY-{str(obj.id).split('-')[0].upper()}"
        )

    def get_plan_name(self, obj: Payment) -> str:
        if obj.plan_id and obj.plan:
            return obj.plan.name
        return obj.metadata.get("plan_name") or "Gói học"

    def get_method(self, obj: Payment) -> str:
        return obj.metadata.get("gateway", "MoMo").title()

    def get_currency(self, obj: Payment) -> str:
        return obj.metadata.get("currency", "VND")

    def get_status_variant(self, obj: Payment) -> str:
        mapping = {
            "paid": "success",
            "pending": "pending",
            "failed": "failed",
            "refunded": "refunded",
        }
        return mapping.get(obj.status, obj.status)

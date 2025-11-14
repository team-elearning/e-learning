from __future__ import annotations

import hmac
import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)


class MomoGatewayError(Exception):
    """Raised when MoMo responds with an error or cannot be reached."""

    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.response = response or {}


@dataclass
class MomoGateway:
    partner_code: str
    access_key: str
    secret_key: str
    endpoint: str
    redirect_url: str
    ipn_url: str
    partner_name: str = "MoMo Payment"
    store_id: str = "Test Store"
    request_type: str = "payWithMethod"
    order_type: str = "momo_wallet"
    lang: str = "vi"
    auto_capture: bool = True

    def _sign(self, data: Dict[str, Any]) -> str:
        """
        Build the raw signature string in the specific order required by MoMo.
        """
        ordered_keys = [
            "accessKey",
            "amount",
            "extraData",
            "ipnUrl",
            "orderId",
            "orderInfo",
            "partnerCode",
            "redirectUrl",
            "requestId",
            "requestType",
        ]
        raw = "&".join(f"{key}={data.get(key, '')}" for key in ordered_keys)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def create_payment(
        self,
        *,
        amount: int,
        order_id: str,
        request_id: str,
        order_info: str,
        extra_data: str = "",
        redirect_url: Optional[str] = None,
        ipn_url: Optional[str] = None,
        lang: Optional[str] = None,
        auto_capture: Optional[bool] = None,
    ) -> Dict[str, Any]:
        payload = {
            "partnerCode": self.partner_code,
            "partnerName": self.partner_name,
            "storeId": self.store_id,
            "orderId": order_id,
            "orderInfo": order_info,
            "amount": str(amount),
            "requestId": request_id,
            "requestType": self.request_type,
            "orderType": self.order_type,
            "extraData": extra_data,
            "redirectUrl": redirect_url or self.redirect_url,
            "ipnUrl": ipn_url or self.ipn_url,
            "lang": lang or self.lang,
            "autoCapture": self.auto_capture if auto_capture is None else auto_capture,
            "orderGroupId": "",
        }

        payload["signature"] = self._sign(
            {
                "accessKey": self.access_key,
                "amount": payload["amount"],
                "extraData": payload["extraData"],
                "ipnUrl": payload["ipnUrl"],
                "orderId": payload["orderId"],
                "orderInfo": payload["orderInfo"],
                "partnerCode": payload["partnerCode"],
                "redirectUrl": payload["redirectUrl"],
                "requestId": payload["requestId"],
                "requestType": payload["requestType"],
            }
        )

        try:
            response = requests.post(self.endpoint, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.exception("MoMo create_payment request failed")
            raise MomoGatewayError("Không thể kết nối tới cổng MoMo", {"error": str(exc)}) from exc
        except ValueError as exc:
            logger.exception("MoMo create_payment returned invalid JSON")
            raise MomoGatewayError("Dữ liệu phản hồi từ MoMo không hợp lệ") from exc

        result_code = data.get("resultCode")
        if result_code not in (0, "0"):
            logger.error("MoMo returned error resultCode=%s message=%s", result_code, data.get("message"))
            raise MomoGatewayError(data.get("message", "MoMo từ chối giao dịch"), data)

        return data

    def verify_ipn_signature(self, payload: Dict[str, Any]) -> bool:
        ordered_keys = [
            "accessKey",
            "amount",
            "extraData",
            "message",
            "orderId",
            "orderInfo",
            "orderType",
            "partnerCode",
            "payType",
            "requestId",
            "responseTime",
            "resultCode",
            "transId",
        ]
        raw = "&".join(f"{key}={payload.get(key, '')}" for key in ordered_keys)
        expected = hmac.new(
            self.secret_key.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return expected == payload.get("signature")


def _env(key: str, default: Optional[str] = None) -> str:
    value = getattr(settings, key, None) or default
    if value is None:
        raise ImproperlyConfigured(f"{key} is required for MoMo integration")
    return value


def get_momo_gateway() -> MomoGateway:
    """
    Build a gateway instance from Django settings.
    """
    return MomoGateway(
        partner_code=_env("MOMO_PARTNER_CODE", "MOMO"),
        access_key=_env("MOMO_ACCESS_KEY"),
        secret_key=_env("MOMO_SECRET_KEY"),
        endpoint=_env("MOMO_ENDPOINT", "https://test-payment.momo.vn/v2/gateway/api/create"),
        redirect_url=_env("MOMO_REDIRECT_URL", "https://example.com/payment-return"),
        ipn_url=_env("MOMO_IPN_URL", "https://example.com/api/payments/momo/ipn/"),
        partner_name=getattr(settings, "MOMO_PARTNER_NAME", "MoMo Payment"),
        store_id=getattr(settings, "MOMO_STORE_ID", "E-learning Store"),
        request_type=getattr(settings, "MOMO_REQUEST_TYPE", "payWithMethod"),
        order_type=getattr(settings, "MOMO_ORDER_TYPE", "momo_wallet"),
        lang=getattr(settings, "MOMO_LANG", "vi"),
        auto_capture=getattr(settings, "MOMO_AUTO_CAPTURE", True),
    )

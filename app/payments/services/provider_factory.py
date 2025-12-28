from payments.services.base_payment_provider import BasePaymentProvider
from payments.enum.provider import PaymentProvider
from payments.services.yookassa_payment_provider import YookassaPaymentProvider

from payments.config.payment_config import payment_settings
from common.logger import logger


class PaymentProviderFactory:
    @staticmethod
    def create(provider: PaymentProvider) -> BasePaymentProvider:
        match provider:
            case PaymentProvider.YOOKASSA:
                return YookassaPaymentProvider(
                    secret_key=payment_settings.YOOKASSA_SECRET_KEY,
                    shop_id=payment_settings.YOOKASSA_SHOP_ID
                )
            case _:
                logger.error(f"Unknown payment provider: {provider}")

                raise Exception(
                    f"PaymentProviderFactory:create: Unknown payment provider: {provider}"
                )

from app.payments.services.base_payment_provider import BasePaymentProvider
from app.payments.enum.provider import PaymentProvider
from app.payments.services.yookassa_payment_provider import YookassaPaymentProvider
from app.payments.config import payment_config
from common.utils.logger import logger


class PaymentProviderFactory:
    @staticmethod
    def create(provider: PaymentProvider) -> BasePaymentProvider:
        match provider:
            case PaymentProvider.YOOKASSA:
                return YookassaPaymentProvider(
                    secret_key=payment_config.YOOKASSA_SECRET_KEY,
                    shop_id=payment_config.YOOKASSA_SHOP_ID,
                )
            case _:
                logger.error(f"Unknown payment provider: {provider}")

                raise Exception(
                    f"PaymentProviderFactory:create: Unknown payment provider: {provider}"
                )


async def get_payment_provider_factory() -> PaymentProviderFactory:
    return PaymentProviderFactory()

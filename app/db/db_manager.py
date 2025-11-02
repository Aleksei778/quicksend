from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from sqlalchemy import Date
from datetime import timedelta

from database.models import (
    UserOrm,
    CampaignOrm,
    SubscriptionOrm,
    TokenOrm,
    PaypalPlansOrm,
)


class DBManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_campaign(
        self,
        sender_name,
        subject,
        body_template,
        recipients,
        attachment_files,
        user_id,
        campaign_time=datetime.now(),
    ) -> CampaignOrm:
        new_campaign = CampaignOrm(
            sender_name=sender_name,
            subject=subject,
            body_template=body_template,
            recipients=",".join(recipients),
            attachment_files=",".join(attachment_files),
            campaign_time=campaign_time,
            user_id=user_id,
        )

        self.session.add(new_campaign)
        await self.session.flush()
        await self.session.commit()
        return new_campaign

    async def create_user(self, email, first_name, last_name, picture) -> UserOrm:
        new_user = UserOrm(
            email=email, first_name=first_name, last_name=last_name, picture=picture
        )

        self.session.add(new_user)
        await self.session.flush()
        await self.session.commit()
        return new_user

    async def create_sub(self, id, plan, period, status, is_trial):
        sub = SubscriptionOrm(
            user_id=id,
            plan=plan,
            status=status,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=period),
            is_trial=is_trial,
        )

        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)

        return sub

    async def create_token(
        self,
        user_id,
        access_token,
        refresh_token,
        token_type,
        expires_in,
        expires_at,
        scope,
    ) -> TokenOrm:
        new_token = TokenOrm(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            expires_in=expires_in,
            expires_at=expires_at,
            scope=scope,
        )

        self.session.add(new_token)
        await self.session.flush()
        await self.session.commit()
        return new_token

    async def create_paypal_plan(
        self, plan_id, status, name, period, plan
    ) -> PaypalPlansOrm:
        new_plan = PaypalPlansOrm(
            plan_id=plan_id, status=status, name=name, period=period, plan=plan
        )

        self.session.add(new_plan)
        await self.session.flush()
        await self.session.commit()
        return new_plan

    async def get_all_campaigns(self, user_id: str) -> CampaignOrm:
        result = await self.session.execute(
            select(CampaignOrm).where(CampaignOrm.user_id == user_id)
        )

        return result.scalars().all()

    async def get_user_by_email(self, user_email: str) -> UserOrm:
        result = await self.session.execute(
            select(UserOrm).where(UserOrm.email == user_email)
        )

        return result.scalar_one_or_none()

    async def get_paypal_plan(self, plan: str, period: str) -> PaypalPlansOrm:
        result = await self.session.execute(
            select(PaypalPlansOrm)
            .where(PaypalPlansOrm.plan == plan)
            .where(PaypalPlansOrm.period == period)
        )

        return result.scalar_one_or_none()

    async def get_token(self, user_id: str) -> TokenOrm:
        result = await self.session.execute(
            select(TokenOrm).where(TokenOrm.user_id == user_id)
        )

        return result.scalar_one_or_none()

    async def get_all_recipients_in_campaigns_by_date(
        self, user_id: str, datee: date
    ) -> int:
        result = await self.session.execute(
            select(CampaignOrm)
            .where(CampaignOrm.user_id == user_id)
            .where(CampaignOrm.campaign_time.cast(Date) == datee)
        )
        campaigns = result.scalars().all()

        all_recipients = ""
        for camp in campaigns:
            all_recipients += camp.recipients

        all_recipients_list = all_recipients.split(",")

        total_recipients = len(all_recipients_list)

        return total_recipients

    async def get_user_subs(self, user_id):
        result = await self.session.execute(
            select(SubscriptionOrm).where(SubscriptionOrm.user_id == user_id)
        )
        subs = result.scalars().all()
        return subs

    async def get_active_sub(self, user_id) -> bool:
        result = await self.session.execute(
            select(SubscriptionOrm)
            .where(SubscriptionOrm.user_id == user_id)
            .where(SubscriptionOrm.status == "active")
            .where(SubscriptionOrm.end_date > datetime.utcnow())
        )

        subscription = result.scalar_one_or_none()
        print(subscription)
        return subscription

    async def has_used_trial(self, id):
        stmt = select(SubscriptionOrm).where(
            SubscriptionOrm.user_id == id, SubscriptionOrm.is_trial == True
        )
        result = await self.session.execute(stmt)
        existing_trial = result.scalar_one_or_none()

        return existing_trial

    async def can_send_emails(
        self, user: UserOrm, cur_recipients_count: int
    ) -> tuple[bool, str]:
        print("нет ошибки1")
        subs = await self.get_user_subs(user.id)
        if not subs:
            return False, "No subs"

        print("нет ошибки1")
        print(user.id)
        subscription = await self.get_active_sub(user.id)
        print(subscription)
        print("нет ошибки2")
        if not subscription:
            return False, "No active sub"

        active_sub_plan = subscription.plan
        print("нет ошибки3")
        today = date.today()

        prev_recipients_count = await self.get_all_recipients_in_campaigns_by_date(
            user.id, today
        )
        print("нет ошибки4")
        print(prev_recipients_count + cur_recipients_count)

        if (
            prev_recipients_count + cur_recipients_count > 50
            and active_sub_plan == "free_trial"
        ):
            return False, "Recipient limit per day exceeded in trial plan"

        if (
            prev_recipients_count + cur_recipients_count > 500
            and active_sub_plan == "standart"
        ):
            return False, "Recipient limit per day exceeded in standart plan"

        return True, "Active sub"

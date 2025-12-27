from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import asyncio

from celery_conf import celery_app
from db.db_manager import DBManager
from db.session import get_db, get_db2
from models.user import User

from auth.dependencies import get_current_user

# --- РОУТЕР ПОДПИСОК ---
subscription_router = APIRouter()

# --- КОНСТАНТА ПЕРИОДА БЕСПЛАТНОГО ПОЛЬЗОВАНИЯ ---
TRIAL_DAYS = 7


# --- НАЧАЛО ПРОБНОГО ПЕРИОДА ---
@subscription_router.post("/start_trial")
async def start_trial(
    current_user: UserOrm = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_manager = DBManager(session=db)

    existing_trial = await db_manager.has_used_trial(current_user.id)

    if existing_trial:
        print("existing_trial")
        raise HTTPException(
            status_code=400, detail="You have already used your free trial"
        )

    # создаем пробную подписку
    trial_sub = await db_manager.create_sub(
        id=current_user.id, plan="free_trial", period=TRIAL_DAYS, is_trial=True
    )

    return {"message": f"Free trial started. It will end on {trial_sub.end_date}"}


@subscription_router.get("/has_already_use_trial")
async def start_trial(
    current_user: UserOrm = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_manager = DBManager(session=db)

    existing_trial = await db_manager.has_used_trial(current_user.id)

    if existing_trial:
        return {"message": "Yes"}

    return {"message": "No"}


# --- ПОДПИСКА ---
async def subscribe(
    email: str, plan: str, period: str, current_user: UserOrm, db: AsyncSession
):
    db_manager = DBManager(session=db)

    if plan not in ["standart", "premium"]:
        print("Invalid subscription plan")
        return (False, "invalid sub plan")

    if period not in ["month", "year"]:
        print("Invalid subscription period")
        return (False, "invalid sub period")

    sub_user = await db_manager.get_user_by_email(email)

    if not sub_user:
        print("there is no such user")
        return (False, "there is no such user")

    # Проверяем, есть ли уже активная подписка
    active_sub = await db_manager.get_active_sub(sub_user.id)

    if (active_sub.plan == "standart" and plan != "premium") or (
        active_sub.plan == "premium"
    ):
        return (False, f"have already had sub, end_date={active_sub.end_date}")

    periods = {"month": 30, "year": 365}

    new_subscription = await db_manager.create_sub(
        id=sub_user.id,
        plan=plan,
        period=periods[period],
        status="created",
        is_trial=False,
    )

    return (True, new_subscription)


@subscription_router.post("/unsubscribe")
async def unsubscribe(
    current_user: UserOrm = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SubscriptionOrm).where(
        SubscriptionOrm.user_id == current_user.id, SubscriptionOrm.status == "active"
    )
    result = await db.execute(stmt)
    active_sub = result.scalar_one_or_none()

    if not active_sub:
        raise HTTPException(status_code=400, detail="No active subscription to cancel")

    active_sub.status = "inactive"
    active_sub.end_date = datetime.utcnow()

    await db.commit()
    await db.refresh(active_sub)

    return {"message": "Successfully unsubsribed"}


@subscription_router.get("/get_active_sub")
async def get_sub(
    current_user: UserOrm = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_manager = DBManager(session=db)

    subscription = await db_manager.get_active_sub(current_user.id)

    if not subscription:
        return {"message": "No active sub"}

    plans = {
        "free_trial": "Free Trial Plan",
        "standart": "Standart Plan",
        "premium": "Premium Plan",
    }

    return {
        "plan": plans[subscription.plan],
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
    }


@celery_app.task(bind=True)
def update_subscription_status_task():
    asyncio.run(async_update_subscription_status())


async def async_update_subscription_status(db: AsyncSession):
    async with get_db2() as db:
        try:
            stmt = select(SubscriptionOrm).where(
                SubscriptionOrm.status == "active",
                SubscriptionOrm.end_date <= datetime.utcnow(),
            )
            result = await db.execute(stmt)
            expired_subs = result.scalars().all()

            if expired_subs:
                for sub in expired_subs:
                    sub.status = "inactive"

                await db.commit()

        except Exception as e:
            print(f"Error while updating: {e}")

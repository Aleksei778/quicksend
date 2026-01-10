from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.campaigns.models.campaign import Campaign
from app.campaigns.models.attachment import Attachment
from app.campaigns.models.recipient import Recipient
from app.subscriptions.model import Subscription
from app.payments.model import Payment
from common.users.model import User
from common.google.token.model import GoogleToken
from common.utils.database import Base
from common.utils.config import base_config

config = context.config

section = config.config_ini_section
config.set_section_option(section, "DB_HOST", str(base_config.DB_HOST))
config.set_section_option(section, "DB_NAME", str(base_config.DB_NAME))
config.set_section_option(section, "DB_PASS", str(base_config.DB_PASS))
config.set_section_option(section, "DB_USER", str(base_config.DB_USER))
config.set_section_option(section, "DB_PORT", str(base_config.DB_PORT))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

from db.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    currency = Column(String)
    amount = Column(Numeric(10, 2))
    status = Column(String)  # "pending", "successfull", "failed"
    payment_method = Column(String)
    transaction_id = Column(String, unique=True)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    subscription = relationship("Subscription", back_populates="payments")
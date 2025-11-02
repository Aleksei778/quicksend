from models.user import User


class UserRepository:
    def __init__(self, db):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

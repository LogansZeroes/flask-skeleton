from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Boolean, Integer, String, DateTime

from .base import Base
from .mixins import CRUDMixin
from .user import User
from data.util import generate_random_token

def tomorrow():
    return datetime.utcnow() + timedelta(seconds=30)

class UserPasswordToken(Base, CRUDMixin):
    __tablename__ = 'user_password_tokens'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship(User)
    token = Column(String, nullable=False, default=generate_random_token())
    is_used = Column(Boolean(name="used"), default=False)
    expiration_dt = Column(DateTime, default=tomorrow())
    expired = expiration_dt < func.now()

    # TODO: This is broken, needs to be fixed
    @hybrid_property
    def invalid(self):
        return self.is_used | self.expired

    @classmethod
    def invalid_tokens(cls, session, user_id):
        "Returns all invalid tokens for a user. A token is invalid if it has been used or has expired"
        session.query(cls).filter(cls.user_id == user_id, cls.invalid)

    @classmethod
    def valid_token(cls, session, user_id):
        "Returns valid token for a user if it exists"
        session.query(cls).filter(cls.user_id == user_id, ~cls.invalid).scalar()

    @classmethod
    def get_or_create_token(cls, session, user_id):
        invalid_tokens = UserPasswordToken.invalid_tokens(session, user_id)
        if invalid_tokens:
            invalid_tokens.delete()
        token = UserPasswordToken.valid_token(session, user_id)
        return token if token else UserPasswordToken.create(session, user_id=user_id)

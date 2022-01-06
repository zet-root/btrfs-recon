from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import inflection
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy_repr import RepresentableBase

if TYPE_CHECKING:
    from .address import Address

__all__ = [
    'Base',
    'BaseModel',
    'BaseStruct',
]

Base = declarative_base(cls=RepresentableBase)


class BaseModel(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return inflection.underscore(cls.__name__)

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, server_default=sa.func.now(), nullable=False)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, server_default=sa.func.now(), server_onupdate=sa.func.now(), nullable=False)


class BaseStruct(BaseModel):
    """Base model for all addressable structures"""
    __abstract__ = True

    address_id: declared_attr[int] = declared_attr(lambda cls: sa.Column(sa.ForeignKey('address.id'), nullable=False))
    address: declared_attr[Address] = declared_attr(lambda cls: orm.relationship('Address', lazy='joined'))

from app.db.base import Base
from app.models.mixins import PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin


class ORMModel(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __abstract__ = True

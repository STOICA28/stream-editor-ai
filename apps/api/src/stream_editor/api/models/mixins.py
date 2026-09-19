from typing import Any
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_mixin, declared_attr
import datetime

@declarative_mixin
class JobLeaseMixin:
    __allow_unmapped__ = True

    @declared_attr
    def worker_id(cls: Any):  # type: ignore[no-untyped-def]
        return Column(String, nullable=True)

    @declared_attr
    def started_at(cls: Any):  # type: ignore[no-untyped-def]
        return Column(DateTime, nullable=True)

    @declared_attr
    def heartbeat_at(cls: Any):  # type: ignore[no-untyped-def]
        return Column(DateTime, nullable=True)

    @declared_attr
    def lease_expires_at(cls: Any):  # type: ignore[no-untyped-def]
        return Column(DateTime, nullable=True)

    @declared_attr
    def attempt(cls: Any):  # type: ignore[no-untyped-def]
        return Column(Integer, default=1)


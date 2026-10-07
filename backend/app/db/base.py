import json
from typing import Any, List, Optional
from sqlalchemy import JSON, Text, TypeDecorator
from sqlalchemy.orm import DeclarativeBase

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class Base(DeclarativeBase):
    pass


class VectorType(TypeDecorator):
    """
    Portable Vector Type:
    - Under PostgreSQL with pgvector: maps to pgvector Vector(dim)
    - Under SQLite / fallback: maps to JSON array of floats
    """
    impl = Text
    cache_ok = True

    def __init__(self, dimension: int = 384, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.dimension = dimension

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(Vector(self.dimension))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Optional[List[float]], dialect) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return value
        return value  # JSON serializer handles list of floats

    def process_result_value(self, value: Any, dialect) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [float(x) for x in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return [float(x) for x in parsed]
            except Exception:
                pass
        return list(value)


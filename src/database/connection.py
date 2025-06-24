# src/database/connection.py
import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator


DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{os.getenv('POSTGRES_USER', 'rag_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'rag_password')}@"
    f"localhost:5432/{os.getenv('POSTGRES_DB', 'rag_db')}"
)

engine = create_engine(DATABASE_URL, echo=False)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

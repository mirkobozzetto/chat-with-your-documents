# src/database/connection.py
import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is required")
    return url

engine = create_engine(get_database_url(), echo=False)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

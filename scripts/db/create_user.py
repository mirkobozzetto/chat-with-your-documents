# scripts/db/create_user.py
import sys
import os
import bcrypt
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import select
from src.database import get_db_session, User


def create_user(username: str, password: str, is_active: bool = True) -> bool:
    try:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with next(get_db_session()) as session:
            existing_user = session.exec(select(User).where(User.username == username)).first()
            if existing_user:
                print(f"❌ User '{username}' already exists")
                return False

            new_user = User(
                username=username,
                password_hash=password_hash,
                is_active=is_active
            )

            session.add(new_user)
            session.commit()

            print(f"✅ User '{username}' created successfully")
            return True

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/db/create_user.py <username> <password> [active]")
        print("Example: python scripts/db/create_user.py admin mypassword")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    is_active = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True

    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        sys.exit(1)

    success = create_user(username, password, is_active)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

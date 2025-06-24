# scripts/db/migrate_auth.py
import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import get_db_session, User


def migrate_users_from_json() -> bool:
    try:
        auth_users_path = Path(__file__).parent.parent.parent / "auth_users.json"
        
        if not auth_users_path.exists():
            print("⚠️ auth_users.json not found, skipping migration")
            return True
        
        with open(auth_users_path, 'r') as f:
            users_data = json.load(f)
        
        if not users_data:
            print("⚠️ No users found in auth_users.json")
            return True
        
        migrated_count = 0
        skipped_count = 0
        
        with next(get_db_session()) as session:
            for username, password_hash in users_data.items():
                existing_user = session.query(User).filter(User.username == username).first()
                if existing_user:
                    print(f"⏭️ User '{username}' already exists, skipping")
                    skipped_count += 1
                    continue
                
                new_user = User(
                    username=username,
                    password_hash=password_hash,
                    is_active=True
                )
                
                session.add(new_user)
                migrated_count += 1
                print(f"✅ Migrated user: {username}")
            
            session.commit()
        
        print(f"\n📊 Migration Summary:")
        print(f"   Migrated: {migrated_count} users")
        print(f"   Skipped: {skipped_count} users")
        print(f"   Total: {migrated_count + skipped_count} users processed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating users: {e}")
        return False


def main():
    print("🔄 Starting auth users migration...")
    success = migrate_users_from_json()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
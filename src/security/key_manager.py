# src/security/key_manager.py
import os
import secrets
import hashlib
from typing import Optional
from pathlib import Path


class KeyManager:
    """Secure key management for JWT and other cryptographic operations"""
    
    def __init__(self):
        self._key_file = Path(".secrets/jwt_key")
        self._ensure_key_directory()
    
    def _ensure_key_directory(self) -> None:
        """Create secure directory for keys if it doesn't exist"""
        self._key_file.parent.mkdir(mode=0o700, exist_ok=True)
    
    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key from environment or generate secure one"""
        env_key = os.getenv("JWT_SECRET_KEY")
        
        if env_key and env_key != "your-secret-key-change-this-in-production":
            if self._is_secure_key(env_key):
                return env_key
            else:
                raise ValueError("JWT_SECRET_KEY is not secure enough. Must be at least 32 characters with mixed case, numbers, and symbols.")
        
        return self._get_or_create_file_key()
    
    def _is_secure_key(self, key: str) -> bool:
        """Validate key security requirements"""
        if len(key) < 32:
            return False
        
        has_upper = any(c.isupper() for c in key)
        has_lower = any(c.islower() for c in key)
        has_digit = any(c.isdigit() for c in key)
        has_symbol = any(not c.isalnum() for c in key)
        
        return has_upper and has_lower and has_digit and has_symbol
    
    def _get_or_create_file_key(self) -> str:
        """Get existing key from file or create new secure one"""
        if self._key_file.exists():
            return self._read_key_file()
        else:
            return self._create_new_key()
    
    def _read_key_file(self) -> str:
        """Read key from secure file"""
        try:
            with open(self._key_file, 'r') as f:
                key = f.read().strip()
            
            if not self._is_secure_key(key):
                return self._create_new_key()
            
            return key
        except Exception:
            return self._create_new_key()
    
    def _create_new_key(self) -> str:
        """Generate and store new cryptographically secure key"""
        secure_key = self._generate_secure_key()
        
        try:
            with open(self._key_file, 'w') as f:
                f.write(secure_key)
            
            os.chmod(self._key_file, 0o600)
            
            print("🔐 New secure JWT key generated and stored")
            return secure_key
        except Exception as e:
            print(f"⚠️ Could not save key to file: {e}")
            return secure_key
    
    def _generate_secure_key(self) -> str:
        """Generate cryptographically secure random key"""
        random_bytes = secrets.token_bytes(32)
        random_string = secrets.token_urlsafe(32)
        
        combined = f"{random_string}_{hashlib.sha256(random_bytes).hexdigest()[:16]}"
        
        return combined
    
    def rotate_key(self) -> str:
        """Generate new key and invalidate old one"""
        if self._key_file.exists():
            backup_file = self._key_file.with_suffix('.bak')
            self._key_file.rename(backup_file)
            print("🔄 Old JWT key backed up")
        
        new_key = self._create_new_key()
        print("✅ JWT key rotated successfully")
        return new_key
    
    def validate_current_key(self) -> bool:
        """Validate current key meets security requirements"""
        try:
            current_key = self.get_jwt_secret_key()
            return self._is_secure_key(current_key)
        except Exception:
            return False
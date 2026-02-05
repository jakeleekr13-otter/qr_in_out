import bcrypt

class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with automatic salt.
        Uses work factor of 12 (2^12 iterations) for security.
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its bcrypt hash.
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except (ValueError, TypeError):
            # Handle invalid hash format gracefully
            return False

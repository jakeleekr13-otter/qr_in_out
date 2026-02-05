import hashlib

class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using SHA-256.
        In a production environment, use bcrypt or argon2.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        """
        return AuthManager.hash_password(password) == password_hash

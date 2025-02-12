import hashlib

def hash_password(password: str) -> str:
    """
    Hash password using SHA-256
    Args:
        password: Plain text password
    Returns:
        Hashed password string
    """
    return hashlib.sha256(password.encode()).hexdigest()
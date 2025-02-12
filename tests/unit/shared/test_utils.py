import pytest
from shared.utils import hash_password

def test_hash_password():
    password = "test_password"
    hashed = hash_password(password)
    
    # Test that same password produces same hash
    assert hash_password(password) == hashed
    
    # Test that different passwords produce different hashes
    assert hash_password("different_password") != hashed
    
    # Test hash length (SHA-256 produces 64 character hex string)
    assert len(hashed) == 64
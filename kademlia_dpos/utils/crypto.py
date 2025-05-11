import hashlib
import json
import uuid
import time
from typing import Dict, Any, List
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)

def generate_keys():
    """
    Generate RSA key pair for node identification and message signing.
    
    Returns:
        Tuple of (private_key_pem, public_key_pem) as strings
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode('utf-8'), public_pem.decode('utf-8')

def hash_data(data: Any) -> str:
    """
    Create a hash of the given data.
    
    Args:
        data: Data to hash
        
    Returns:
        Hex string hash
    """
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode('utf-8')).hexdigest()

def sign_data(data: Any, private_key_pem: str) -> str:
    """
    Sign data with a private key.
    
    Args:
        data: Data to sign
        private_key_pem: PEM-encoded private key
        
    Returns:
        Base64-encoded signature
    """
    json_data = json.dumps(data, sort_keys=True)
    private_key = load_pem_private_key(private_key_pem.encode('utf-8'), password=None)
    
    signature = private_key.sign(
        json_data.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    return signature.hex()

def verify_signature(data: Any, signature: str, public_key_pem: str) -> bool:
    """
    Verify a signature with a public key.
    
    Args:
        data: Data that was signed
        signature: Hex-encoded signature
        public_key_pem: PEM-encoded public key
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        json_data = json.dumps(data, sort_keys=True)
        public_key = load_pem_public_key(public_key_pem.encode('utf-8'))
        
        public_key.verify(
            bytes.fromhex(signature),
            json_data.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return True
    except Exception:
        return False

def create_vote_id() -> str:
    """
    Create a unique ID for a vote.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())

def get_timestamp() -> int:
    """
    Get current Unix timestamp.
    
    Returns:
        Current time as Unix timestamp
    """
    return int(time.time()) 
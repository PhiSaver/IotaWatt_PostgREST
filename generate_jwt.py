#!/usr/bin/env python3
"""
JWT Token Generator for PostgREST API Authentication

This script generates JWT tokens for authenticating with the PostgREST API.
The tokens can be used to access the iotawatt data with different permission levels.

python generate_jwt.py generate phisaver --no-expiry

"""

import jwt
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
import sys
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / '.env'
    env_vars = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

# Load configuration from .env file
env_vars = load_env_file()

# JWT Configuration from .env file
JWT_SECRET = env_vars.get('PGRST_JWT_SECRET')
ROLE_CLAIM_KEY = env_vars.get('PGRST_ROLE_CLAIM_KEY', '.role').replace('.', '')  # Remove dot prefix
POSTGREST_PORT = env_vars.get('POSTGREST_EXTERNAL_PORT', '3001')

# Validate that JWT_SECRET is loaded
if not JWT_SECRET:
    print("❌ Error: PGRST_JWT_SECRET not found in .env file!")
    print("Please ensure your .env file contains a valid JWT secret.")
    sys.exit(1)

# Available roles from init.sql
ROLES = {
    "web_anon": {
        "description": "Anonymous role with read-only access",
        "permissions": ["SELECT on public.iotawatt"]
    },
    "phisaver": {
        "description": "Authenticated user role with full access", 
        "permissions": ["SELECT, INSERT, UPDATE, DELETE on public.iotawatt"]
    }
}

def generate_jwt_token(
    role: str = "phisaver",
    exp_hours: int = 24,
    additional_claims: Optional[dict] = None,
    no_expiry: bool = False
) -> str:
    """
    Generate a JWT token for PostgREST authentication.
    
    Args:
        role: Database role to assume ('web_anon' or 'phisaver')
        exp_hours: Token expiration time in hours (ignored if no_expiry=True)
        additional_claims: Optional additional claims to include
        no_expiry: If True, generate a token without expiration
    
    Returns:
        JWT token string
    """
    if role not in ROLES:
        raise ValueError(f"Invalid role '{role}'. Available roles: {list(ROLES.keys())}")
    
    # Current time and expiration
    now = datetime.now(timezone.utc)
    
    # JWT payload
    payload = {
        "role": role,  # This is the key claim for PostgREST
        "iat": int(now.timestamp()),  # Issued at
        "iss": "iotawatt-jwt-generator",  # Issuer
    }
    
    # Add expiration only if not no_expiry
    if not no_expiry:
        exp = now + timedelta(hours=exp_hours)
        payload["exp"] = int(exp.timestamp())
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Generate the token
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return token

def decode_jwt_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dictionary
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")

def print_role_info():
    """Print information about available roles."""
    print("Available Database Roles:")
    print("=" * 50)
    for role, info in ROLES.items():
        print(f"\nRole: {role}")
        print(f"Description: {info['description']}")
        print("Permissions:")
        for perm in info['permissions']:
            print(f"  • {perm}")

def print_token_info(token: str):
    """Print information about a JWT token."""
    try:
        payload = decode_jwt_token(token)
        print("\nToken Information:")
        print("=" * 50)
        print(f"Role: {payload.get('role')}")
        print(f"Issued At: {datetime.fromtimestamp(payload.get('iat', 0), timezone.utc)}")
        if 'exp' in payload:
            print(f"Expires At: {datetime.fromtimestamp(payload.get('exp', 0), timezone.utc)}")
        else:
            print("Expires At: Never (no expiration)")
        print(f"Issuer: {payload.get('iss', 'N/A')}")
        
        # Check if token is expired
        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload.get('exp', 0), timezone.utc)
            if exp_time < datetime.now(timezone.utc):
                print("⚠️  Token is EXPIRED")
            else:
                time_left = exp_time - datetime.now(timezone.utc)
                print(f"✅ Token is valid for {time_left}")
        else:
            print("🔄 Token has NO EXPIRATION (permanent)")
            
        print("\nFull payload:")
        print(json.dumps(payload, indent=2, default=str))
        
    except ValueError as e:
        print(f"Error decoding token: {e}")

def main():
    """Main CLI interface."""
    if len(sys.argv) == 1:
        print("JWT Token Generator for PostgREST")
        print("=" * 40)
        print("\nUsage:")
        print("  python generate_jwt.py <command> [options]")
        print("\nCommands:")
        print("  generate <role> [hours] [--no-expiry]  - Generate a token for the specified role")
        print("  decode <token>                         - Decode and display token information")
        print("  roles                                  - List available roles and permissions")
        print("\nExamples:")
        print("  python generate_jwt.py generate phisaver 24")
        print("  python generate_jwt.py generate web_anon 72")
        print("  python generate_jwt.py generate phisaver --no-expiry")
        print("  python generate_jwt.py decode <your-token>")
        print("  python generate_jwt.py roles")
        return
    
    command = sys.argv[1].lower()
    
    if command == "roles":
        print_role_info()
        
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Error: Role required for generate command")
            print("Usage: python generate_jwt.py generate <role> [hours] [--no-expiry]")
            return
            
        role = sys.argv[2]
        
        # Check for --no-expiry flag
        no_expiry = "--no-expiry" in sys.argv
        
        # Parse expiration hours (ignore if --no-expiry is set)
        exp_hours = 24  # default
        if not no_expiry:
            for i, arg in enumerate(sys.argv[3:], 3):
                if arg != "--no-expiry":
                    try:
                        exp_hours = int(arg)
                        break
                    except ValueError:
                        continue
        
        try:
            token = generate_jwt_token(role, exp_hours, no_expiry=no_expiry)
            if no_expiry:
                print(f"Generated JWT token for role '{role}' (NO EXPIRATION):")
            else:
                print(f"Generated JWT token for role '{role}' (expires in {exp_hours} hours):")
            print("=" * 60)
            print(token)
            print("=" * 60)
            
            # Show token info
            print_token_info(token)
            
            # Show usage example
            print("\nUsage with curl:")
            print(f"curl -H 'Authorization: Bearer {token}' \\")
            print(f"     'http://localhost:{POSTGREST_PORT}/iotawatt?limit=10'")
            
        except ValueError as e:
            print(f"Error: {e}")
            
    elif command == "decode":
        if len(sys.argv) < 3:
            print("Error: Token required for decode command")
            print("Usage: python generate_jwt.py decode <token>")
            return
            
        token = sys.argv[2]
        print_token_info(token)
        
    else:
        print(f"Unknown command: {command}")
        print("Use 'python generate_jwt.py' for help")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
JWT Token Generator for PostgREST API Authentication

The tokens can be used to access the iotawatt data with different permission levels.

"""

import os
import jwt
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
import typer


# JWT Configuration from .env file
JWT_SECRET = os.environ.get("PGRST_JWT_SECRET", "").strip()
ROLE_CLAIM_KEY = os.environ.get("PGRST_ROLE_CLAIM_KEY", ".role").replace(".", "")  # Remove dot prefix
POSTGREST_PORT = os.environ.get("POSTGREST_EXTERNAL_PORT", "3000")
PG_READER_USER = os.environ.get("PG_READER_USER", "reader")
PG_WRITER_USER = os.environ.get("PG_WRITER_USER", "writer")

app = typer.Typer(help="JWT Token Generator for PostgREST API")

# Validate that JWT_SECRET is loaded
if not JWT_SECRET:
    print("Error: PGRST_JWT_SECRET not found in .env file!")
    print("Please ensure your .env file contains a valid JWT secret.")
    raise typer.Exit(1)

# Available roles from init.sql
ROLES = {
    "anon": {
        "description": "Anonymous role with read-only access to structure",
        "permissions": ["SELECT on public.iotawatt"],
    },
    PG_WRITER_USER: {
        "description": "Authenticated user role with read/write access",
        "permissions": ["SELECT, INSERT, UPDATE, DELETE on public.iotawatt"],
    },
    PG_READER_USER: {
        "description": "Authenticated user role with read-only access",
        "permissions": ["SELECT on public.iotawatt"],
    },
}


def generate_jwt_token(
    role: str,
    exp_hours: Optional[int] = None,
    additional_claims: Optional[dict] = None,
) -> str:
    """Generate a JWT token for PostgREST authentication."""
    if role not in ROLES:
        raise typer.BadParameter(f"Invalid role '{role}'. Available roles: {list(ROLES.keys())}")

    now = datetime.now(timezone.utc)

    payload = {
        "role": role,
        "iat": int(now.timestamp()),
        "iss": "iotawatt-jwt-generator",
    }

    if exp_hours is not None:
        exp = now + timedelta(hours=exp_hours)
        payload["exp"] = int(exp.timestamp())

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_jwt_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise typer.BadParameter("Token has expired")
    except jwt.InvalidTokenError as e:
        raise typer.BadParameter(f"Invalid token: {e}")


@app.command()
def roles():
    """List available database roles and their permissions."""
    print("\nAvailable Database Roles:")
    print("=" * 80)
    for role, info in ROLES.items():
        print(f"\nRole: {role}")
        print(f"  Description: {info['description']}")
        print("  Permissions:")
        for perm in info["permissions"]:
            print(f"    - {perm}")


@app.command()
def decode(token: str):
    """Decode and display JWT token information."""
    payload = decode_jwt_token(token)

    print("\nToken Information:")
    print("=" * 80)
    print(f"Role: {payload.get('role', 'N/A')}")
    print(f"Issued At: {datetime.fromtimestamp(payload.get('iat', 0), timezone.utc)}")

    if "exp" in payload:
        exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
        print(f"Expires At: {exp_time}")

        if exp_time < datetime.now(timezone.utc):
            print("Status: EXPIRED")
        else:
            time_left = exp_time - datetime.now(timezone.utc)
            print(f"Status: VALID for {time_left}")
    else:
        print("Expires At: Never (no expiration)")
        print("Status: VALID (permanent)")

    print(f"Issuer: {payload.get('iss', 'N/A')}")

    print("\nFull payload:")
    print(json.dumps(payload, indent=2, default=str))


@app.command()
def example():
    """
    Show usage example for using generated JWT token with curl.
    """
    print("\nUsage with curl:")
    print("export JWT_TOKEN=`uv run jwtutil.py generate writer`")
    print(f"curl -H 'Authorization: Bearer $JWT_TOKEN' 'http://localhost:{POSTGREST_PORT}/iotawatt_data?limit=10'")
    print()


@app.command()
def generate(
    role: str = typer.Argument(..., help="Database role (writer, reader, anon)"),
    hours: Optional[int] = typer.Option(None, "--hours", "-h", help="Token expiration in hours"),
    no_expiry: bool = typer.Option(False, "--no-expiry", help="Create token with no expiration"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Generate a JWT token for PostgREST authentication."""
    exp_hours = None if no_expiry else (hours or 24)

    token = generate_jwt_token(role, exp_hours)

    print(token)
    
    if verbose:
        print(f"\nGenerated token for role: {role}", file=__import__('sys').stderr)
        if exp_hours:
            print(f"Token expires in: {exp_hours} hours", file=__import__('sys').stderr)
        else:
            print("Token has no expiration", file=__import__('sys').stderr)
if __name__ == "__main__":
    app()

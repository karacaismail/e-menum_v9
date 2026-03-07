#!/usr/bin/env python3
"""
Database connection test script. Run inside the container to diagnose DB issues.
Reads connection info from environment (DATABASE_URL or POSTGRES_*).

Usage (from host):
  docker exec emenum_web python /app/docker/check_db.py
  docker exec -it emenum_web python /app/docker/check_db.py
"""

import os
import sys
from urllib.parse import urlparse, urlunparse


def mask_url(url: str) -> str:
    """Mask password in URL for safe logging."""
    if not url or "@" not in url:
        return url or "(empty)"
    try:
        parsed = urlparse(url)
        if parsed.password:
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc += f":{parsed.port}"
            if parsed.username:
                netloc = f"{parsed.username}:****@{netloc}"
            else:
                netloc = f"****@{netloc}"
            return urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        return "(parse error)"
    return url


def get_database_url() -> str | None:
    """Build DATABASE_URL from env (compose-style)."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "emenum")
    if user and password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return None


def main() -> int:
    print("=" * 60)
    print("E-Menum DB connection test (env-based)")
    print("=" * 60)

    url = get_database_url()
    if not url:
        print("ERROR: No DATABASE_URL and no POSTGRES_USER/POSTGRES_PASSWORD in env.")
        print(
            "Env keys present:",
            [k for k in os.environ if "POSTGRES" in k or "DATABASE" in k],
        )
        return 1

    print("DATABASE_URL (masked):", mask_url(url))
    parsed = urlparse(url)
    print("  host:", parsed.hostname or "(none)")
    print("  port:", parsed.port or 5432)
    print("  user:", parsed.username or "(none)")
    print("  db:  ", (parsed.path or "").strip("/") or "(none)")
    print()

    # 1) Raw TCP connect (no driver)
    import socket

    host = parsed.hostname or "db"
    port = parsed.port or 5432
    print(f"1) TCP connect to {host}:{port} ...")
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        print("   OK (port reachable)")
    except Exception as e:
        print(f"   FAIL: {e}")
        print("   -> Check: same network as db? Is 'db' resolvable?")
        return 1

    # 2) PostgreSQL via psycopg
    print("2) PostgreSQL connect (psycopg) ...")
    try:
        import psycopg
    except ImportError:
        try:
            import psycopg2 as psycopg

            # psycopg2 uses connect(dsn=url) or connect(host=..., user=..., ...)
            try:
                conn = psycopg.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    user=parsed.username,
                    password=parsed.password,
                    dbname=(parsed.path or "").strip("/") or "emenum",
                    connect_timeout=5,
                )
                conn.close()
                print("   OK (connected with psycopg2)")
                return 0
            except Exception as e:
                print(f"   FAIL: {e}")
                return 1
        except ImportError:
            print("   FAIL: neither psycopg nor psycopg2 installed")
            return 1

    try:
        conn = psycopg.connect(url, connect_timeout=5)
        conn.close()
        print("   OK (connected with psycopg)")
        return 0
    except Exception as e:
        print(f"   FAIL: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Supabase client wrapper for Meeting Notes Taker."""

import os
from typing import Optional

from supabase import create_client, Client

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create the Supabase client singleton."""
    global _supabase_client

    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials. "
                "Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            )

        _supabase_client = create_client(url, key)

    return _supabase_client


def reset_supabase_client() -> None:
    """Reset the Supabase client (useful for testing or re-initialization)."""
    global _supabase_client
    _supabase_client = None

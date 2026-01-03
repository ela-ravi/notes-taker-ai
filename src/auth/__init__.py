"""Authentication module for Meeting Notes Taker."""

from .auth_manager import AuthManager, AuthState
from .supabase_client import get_supabase_client

__all__ = ["AuthManager", "AuthState", "get_supabase_client"]

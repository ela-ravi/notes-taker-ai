"""Authentication manager for handling user login, session, and subscription state."""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from supabase import Client

from .supabase_client import get_supabase_client


class AuthState(Enum):
    """Authentication state enum."""
    LOGGED_OUT = "logged_out"
    LOGGED_IN = "logged_in"
    SESSION_EXPIRED = "session_expired"


@dataclass
class UserProfile:
    """User profile data."""
    id: str
    email: str
    full_name: Optional[str]
    subscription_tier: str  # 'free' or 'pro'
    subscription_status: str  # 'active', 'canceled', 'past_due', 'expired'
    meetings_this_month: int
    meetings_limit: int  # 3 for free, unlimited for pro

    @property
    def can_create_meeting(self) -> bool:
        """Check if user can create a new meeting."""
        if self.subscription_tier == "pro":
            return True
        return self.meetings_this_month < self.meetings_limit

    @property
    def meetings_remaining(self) -> int:
        """Get remaining meetings for this month."""
        if self.subscription_tier == "pro":
            return 999999  # Effectively unlimited
        return max(0, self.meetings_limit - self.meetings_this_month)


class AuthManager:
    """Manages user authentication and session state."""

    SESSION_FILE = ".meeting_notes_session.json"

    def __init__(self, on_state_change: Optional[Callable[[AuthState], None]] = None):
        """Initialize the auth manager.

        Args:
            on_state_change: Optional callback when auth state changes
        """
        self._client: Optional[Client] = None
        self._user_profile: Optional[UserProfile] = None
        self._on_state_change = on_state_change
        self._state = AuthState.LOGGED_OUT

    @property
    def client(self) -> Client:
        """Get the Supabase client."""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    @property
    def state(self) -> AuthState:
        """Get current auth state."""
        return self._state

    @property
    def user_profile(self) -> Optional[UserProfile]:
        """Get current user profile."""
        return self._user_profile

    @property
    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return self._state == AuthState.LOGGED_IN

    @property
    def access_token(self) -> Optional[str]:
        """Get current access token for API calls."""
        try:
            session = self.client.auth.get_session()
            return session.access_token if session else None
        except Exception:
            return None

    def _set_state(self, new_state: AuthState) -> None:
        """Update state and notify listeners."""
        if self._state != new_state:
            self._state = new_state
            if self._on_state_change:
                self._on_state_change(new_state)

    def _get_session_path(self) -> Path:
        """Get path to session file."""
        # Store in user's home directory
        return Path.home() / self.SESSION_FILE

    def _save_session(self) -> None:
        """Save current session to file."""
        try:
            session = self.client.auth.get_session()
            if session:
                session_data = {
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                }
                self._get_session_path().write_text(json.dumps(session_data))
        except Exception as e:
            print(f"Failed to save session: {e}")

    def _load_session(self) -> bool:
        """Load session from file. Returns True if session was restored."""
        session_path = self._get_session_path()
        if not session_path.exists():
            return False

        try:
            session_data = json.loads(session_path.read_text())
            refresh_token = session_data.get("refresh_token")

            if refresh_token:
                # Try to refresh the session
                response = self.client.auth.refresh_session(refresh_token)
                if response and response.session:
                    self._save_session()  # Save new tokens
                    return True
        except Exception as e:
            print(f"Failed to restore session: {e}")
            # Delete invalid session file
            try:
                session_path.unlink()
            except Exception:
                pass

        return False

    def _clear_session(self) -> None:
        """Clear saved session."""
        try:
            session_path = self._get_session_path()
            if session_path.exists():
                session_path.unlink()
        except Exception:
            pass

    async def initialize(self) -> bool:
        """Initialize auth manager and restore session if available.

        Returns:
            True if user is logged in, False otherwise
        """
        if self._load_session():
            # Session restored, fetch profile
            if await self._fetch_profile():
                self._set_state(AuthState.LOGGED_IN)
                return True
            else:
                self._set_state(AuthState.SESSION_EXPIRED)
                return False

        self._set_state(AuthState.LOGGED_OUT)
        return False

    def initialize_sync(self) -> bool:
        """Synchronous version of initialize for non-async contexts."""
        if self._load_session():
            if self._fetch_profile_sync():
                self._set_state(AuthState.LOGGED_IN)
                return True
            else:
                self._set_state(AuthState.SESSION_EXPIRED)
                return False

        self._set_state(AuthState.LOGGED_OUT)
        return False

    async def _fetch_profile(self) -> bool:
        """Fetch user profile from Supabase."""
        return self._fetch_profile_sync()

    def _fetch_profile_sync(self) -> bool:
        """Synchronous profile fetch."""
        try:
            user = self.client.auth.get_user()
            if not user or not user.user:
                return False

            # Fetch profile data
            response = self.client.table("profiles").select("*").eq("id", user.user.id).single().execute()

            if response.data:
                data = response.data
                self._user_profile = UserProfile(
                    id=data["id"],
                    email=data.get("email", user.user.email or ""),
                    full_name=data.get("full_name"),
                    subscription_tier=data.get("subscription_tier", "free"),
                    subscription_status=data.get("subscription_status", "active"),
                    meetings_this_month=data.get("meetings_this_month", 0),
                    meetings_limit=3 if data.get("subscription_tier", "free") == "free" else 999999,
                )
                return True

        except Exception as e:
            print(f"Failed to fetch profile: {e}")

        return False

    def refresh_user_profile(self) -> bool:
        """Refresh user profile data from Supabase.
        
        This is useful for checking subscription status changes after payment.
        
        Returns:
            True if profile was successfully refreshed, False otherwise
        """
        return self._fetch_profile_sync()

    def sign_up(self, email: str, password: str, full_name: Optional[str] = None) -> tuple[bool, str]:
        """Sign up a new user.

        Args:
            email: User's email
            password: Password (min 6 characters)
            full_name: Optional full name

        Returns:
            Tuple of (success, message)
        """
        try:
            metadata = {}
            if full_name:
                metadata["full_name"] = full_name

            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": metadata} if metadata else None,
            })

            if response.user:
                # Check if email confirmation is required
                if response.user.email_confirmed_at is None:
                    return True, "Please check your email to confirm your account."
                else:
                    self._save_session()
                    self._fetch_profile_sync()
                    self._set_state(AuthState.LOGGED_IN)
                    return True, "Account created successfully!"

        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower():
                return False, "This email is already registered. Please sign in."
            return False, f"Sign up failed: {error_msg}"

        return False, "Sign up failed. Please try again."

    def sign_in(self, email: str, password: str) -> tuple[bool, str]:
        """Sign in an existing user.

        Args:
            email: User's email
            password: User's password

        Returns:
            Tuple of (success, message)
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            if response.user:
                self._save_session()
                self._fetch_profile_sync()
                self._set_state(AuthState.LOGGED_IN)
                return True, "Signed in successfully!"

        except Exception as e:
            error_msg = str(e)
            if "invalid" in error_msg.lower():
                return False, "Invalid email or password."
            if "not confirmed" in error_msg.lower():
                return False, "Please confirm your email before signing in."
            return False, f"Sign in failed: {error_msg}"

        return False, "Sign in failed. Please try again."

    def sign_out(self) -> tuple[bool, str]:
        """Sign out the current user.

        Returns:
            Tuple of (success, message)
        """
        try:
            self.client.auth.sign_out()
            self._clear_session()
            self._user_profile = None
            self._set_state(AuthState.LOGGED_OUT)
            return True, "Signed out successfully."

        except Exception as e:
            # Even if sign out fails on server, clear local state
            self._clear_session()
            self._user_profile = None
            self._set_state(AuthState.LOGGED_OUT)
            return True, "Signed out."

    def refresh_profile(self) -> bool:
        """Refresh user profile data.

        Returns:
            True if profile was refreshed successfully
        """
        return self._fetch_profile_sync()

    def send_password_reset(self, email: str) -> tuple[bool, str]:
        """Send password reset email.

        Args:
            email: User's email

        Returns:
            Tuple of (success, message)
        """
        try:
            self.client.auth.reset_password_email(email)
            return True, "Password reset email sent. Please check your inbox."
        except Exception as e:
            return False, f"Failed to send reset email: {e}"

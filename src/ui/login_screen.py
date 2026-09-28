"""Login/Signup screen for Meeting Notes Taker."""

import threading
import time
import webbrowser
from typing import Callable, Optional

import customtkinter as ctk

from ..auth import AuthManager, AuthState


class LoginScreen(ctk.CTkFrame):
    """Login/Signup screen widget."""

    def __init__(
        self,
        master: ctk.CTk,
        auth_manager: AuthManager,
        on_login_success: Callable[[], None],
        **kwargs
    ):
        """Initialize the login screen.

        Args:
            master: Parent widget
            auth_manager: AuthManager instance
            on_login_success: Callback when login is successful
        """
        super().__init__(master, **kwargs)

        self.auth_manager = auth_manager
        self.on_login_success = on_login_success
        self._is_signup_mode = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the login UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Center container
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0, padx=40, pady=40)

        # Logo/Title
        title_label = ctk.CTkLabel(
            center_frame,
            text="Meeting Notes Taker",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = ctk.CTkLabel(
            center_frame,
            text="AI-powered meeting notes",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        subtitle_label.pack(pady=(0, 30))

        # Form container
        form_frame = ctk.CTkFrame(center_frame)
        form_frame.pack(padx=20, pady=10, fill="x")

        # Mode label (Sign In / Sign Up)
        self.mode_label = ctk.CTkLabel(
            form_frame,
            text="Sign In",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.mode_label.pack(pady=(20, 20))

        # Name field (only for signup)
        self.name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.name_entry = ctk.CTkEntry(
            self.name_frame,
            placeholder_text="Full Name",
            width=280,
            height=40,
        )
        self.name_entry.pack(pady=5)
        # Hidden by default

        # Email field
        self.email_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Email",
            width=280,
            height=40,
        )
        self.email_entry.pack(pady=10, padx=20)

        # Password field
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Password",
            show="*",
            width=280,
            height=40,
        )
        self.password_entry.pack(pady=10, padx=20)

        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self._on_submit())

        # Error/Status message
        self.status_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="red",
            wraplength=260,
        )
        self.status_label.pack(pady=5)

        # Submit button
        self.submit_button = ctk.CTkButton(
            form_frame,
            text="Sign In",
            width=280,
            height=40,
            command=self._on_submit,
        )
        self.submit_button.pack(pady=15, padx=20)

        # Forgot password link
        self.forgot_password_btn = ctk.CTkButton(
            form_frame,
            text="Forgot Password?",
            width=280,
            height=30,
            fg_color="transparent",
            hover_color=("gray90", "gray20"),
            text_color=("gray50", "gray70"),
            command=self._on_forgot_password,
        )
        self.forgot_password_btn.pack(pady=(0, 10))

        # Toggle mode button
        self.toggle_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.toggle_frame.pack(pady=(5, 20))

        self.toggle_label = ctk.CTkLabel(
            self.toggle_frame,
            text="Don't have an account?",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.toggle_label.pack(side="left", padx=5)

        self.toggle_button = ctk.CTkButton(
            self.toggle_frame,
            text="Sign Up",
            width=70,
            height=25,
            fg_color="transparent",
            hover_color=("gray90", "gray20"),
            text_color=("#1f6feb", "#58a6ff"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_mode,
        )
        self.toggle_button.pack(side="left")

        # Terms notice (for signup)
        self.terms_label = ctk.CTkLabel(
            center_frame,
            text="By signing up, you agree to our Terms of Service",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        # Hidden by default

    def _toggle_mode(self) -> None:
        """Toggle between sign in and sign up mode."""
        self._is_signup_mode = not self._is_signup_mode
        self._update_mode_ui()

    def _update_mode_ui(self) -> None:
        """Update UI based on current mode."""
        if self._is_signup_mode:
            self.mode_label.configure(text="Create Account")
            self.submit_button.configure(text="Sign Up")
            self.toggle_label.configure(text="Already have an account?")
            self.toggle_button.configure(text="Sign In")
            self.name_frame.pack(before=self.email_entry, pady=5, padx=20)
            self.forgot_password_btn.pack_forget()
            self.terms_label.pack(pady=10)
        else:
            self.mode_label.configure(text="Sign In")
            self.submit_button.configure(text="Sign In")
            self.toggle_label.configure(text="Don't have an account?")
            self.toggle_button.configure(text="Sign Up")
            self.name_frame.pack_forget()
            self.forgot_password_btn.pack(pady=(0, 10))
            self.terms_label.pack_forget()

        # Clear status
        self.status_label.configure(text="", text_color="red")

    def _on_submit(self) -> None:
        """Handle form submission."""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        # Validate
        if not email:
            self._show_error("Please enter your email.")
            return

        if not password:
            self._show_error("Please enter your password.")
            return

        if len(password) < 6:
            self._show_error("Password must be at least 6 characters.")
            return

        # Disable button during request
        self.submit_button.configure(state="disabled", text="Please wait...")

        if self._is_signup_mode:
            full_name = self.name_entry.get().strip() or None
            success, message = self.auth_manager.sign_up(email, password, full_name)
        else:
            success, message = self.auth_manager.sign_in(email, password)

        # Re-enable button
        self.submit_button.configure(
            state="normal",
            text="Sign Up" if self._is_signup_mode else "Sign In"
        )

        if success:
            self._show_success(message)
            if self.auth_manager.is_logged_in:
                self.on_login_success()
        else:
            self._show_error(message)

    def _on_forgot_password(self) -> None:
        """Handle forgot password."""
        email = self.email_entry.get().strip()

        if not email:
            self._show_error("Please enter your email first.")
            return

        success, message = self.auth_manager.send_password_reset(email)

        if success:
            self._show_success(message)
        else:
            self._show_error(message)

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.status_label.configure(text=message, text_color="red")

    def _show_success(self, message: str) -> None:
        """Show success message."""
        self.status_label.configure(text=message, text_color="green")


class SubscriptionScreen(ctk.CTkFrame):
    """Subscription management screen."""

    def __init__(
        self,
        master: ctk.CTk,
        auth_manager: AuthManager,
        on_back: Callable[[], None],
        product_id: str,
        supabase_url: str,
        **kwargs
    ):
        """Initialize subscription screen.

        Args:
            master: Parent widget
            auth_manager: AuthManager instance
            on_back: Callback to go back
            product_id: Dodo Payments product ID
            supabase_url: Supabase project URL
        """
        super().__init__(master, **kwargs)

        self.auth_manager = auth_manager
        self.on_back = on_back
        self.product_id = product_id
        self.supabase_url = supabase_url
        self._polling_active = False
        self._poll_thread: Optional[threading.Thread] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up subscription UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        back_btn = ctk.CTkButton(
            header_frame,
            text="< Back",
            width=80,
            fg_color="transparent",
            hover_color=("gray90", "gray20"),
            command=self.on_back,
        )
        back_btn.pack(side="left")

        title = ctk.CTkLabel(
            header_frame,
            text="Subscription",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(side="left", padx=20)

        # Content
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)

        # Current plan
        profile = self.auth_manager.user_profile
        tier = profile.subscription_tier if profile else "free"
        is_pro = tier == "pro"

        current_plan_label = ctk.CTkLabel(
            content_frame,
            text="Current Plan",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        current_plan_label.pack(pady=(20, 5))

        plan_badge = ctk.CTkLabel(
            content_frame,
            text="PRO" if is_pro else "FREE",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#22c55e" if is_pro else "gray",
        )
        plan_badge.pack(pady=5)

        if profile:
            usage_text = f"{profile.meetings_this_month} / {'Unlimited' if is_pro else profile.meetings_limit} meetings this month"
            usage_label = ctk.CTkLabel(
                content_frame,
                text=usage_text,
                font=ctk.CTkFont(size=12),
                text_color="gray",
            )
            usage_label.pack(pady=10)

        # Upgrade section (only show if not pro)
        if not is_pro:
            separator = ctk.CTkFrame(content_frame, height=2, fg_color="gray30")
            separator.pack(fill="x", pady=20, padx=40)

            upgrade_title = ctk.CTkLabel(
                content_frame,
                text="Upgrade to Pro",
                font=ctk.CTkFont(size=18, weight="bold"),
            )
            upgrade_title.pack(pady=10)

            # Pro features
            features = [
                "Unlimited meetings per month",
                "Priority processing",
                "Advanced summarization",
                "Email support",
            ]

            for feature in features:
                feature_label = ctk.CTkLabel(
                    content_frame,
                    text=f"  {feature}",
                    font=ctk.CTkFont(size=13),
                )
                feature_label.pack(pady=2)

            price_label = ctk.CTkLabel(
                content_frame,
                text="$10 / month",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="#22c55e",
            )
            price_label.pack(pady=15)

            upgrade_btn = ctk.CTkButton(
                content_frame,
                text="Upgrade Now",
                width=200,
                height=45,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=self._on_upgrade,
            )
            upgrade_btn.pack(pady=10)

        # Status message
        self.status_label = ctk.CTkLabel(
            content_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.status_label.pack(pady=20)

    def _on_upgrade(self) -> None:
        """Handle upgrade button click."""
        try:
            import httpx

            self.status_label.configure(text="Creating checkout session...")

            # Call the create-checkout edge function
            token = self.auth_manager.access_token
            if not token:
                self.status_label.configure(text="Please sign in again.", text_color="red")
                return

            response = httpx.post(
                f"{self.supabase_url}/functions/v1/create-checkout",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"product_id": self.product_id},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                checkout_url = data.get("checkout_url")
                if checkout_url:
                    self.status_label.configure(
                        text="Opening checkout in browser...\nPlease complete your payment.",
                        text_color="green"
                    )
                    webbrowser.open(checkout_url)
                    
                    # Start polling for subscription status
                    self._start_subscription_polling()
                else:
                    self.status_label.configure(
                        text="Failed to get checkout URL.",
                        text_color="red"
                    )
            else:
                self.status_label.configure(
                    text=f"Error: {response.text}",
                    text_color="red"
                )

        except Exception as e:
            self.status_label.configure(text=f"Error: {e}", text_color="red")

    def _start_subscription_polling(self) -> None:
        """Start polling for subscription status changes."""
        if self._polling_active:
            return  # Already polling
        
        self._polling_active = True
        self._poll_thread = threading.Thread(target=self._poll_subscription_status, daemon=True)
        self._poll_thread.start()

    def _poll_subscription_status(self) -> None:
        """Poll for subscription status changes in background thread."""
        max_polls = 60  # Poll for up to 5 minutes (60 * 5 seconds)
        poll_count = 0
        initial_tier = self.auth_manager.user_profile.subscription_tier if self.auth_manager.user_profile else "free"
        
        while self._polling_active and poll_count < max_polls:
            time.sleep(5)  # Poll every 5 seconds
            poll_count += 1
            
            try:
                # Refresh user profile
                success = self.auth_manager.refresh_user_profile()
                
                if success and self.auth_manager.user_profile:
                    current_tier = self.auth_manager.user_profile.subscription_tier
                    
                    # Check if tier changed to pro
                    if initial_tier != "pro" and current_tier == "pro":
                        # Subscription activated!
                        self._polling_active = False
                        self._on_subscription_activated()
                        return
                        
            except Exception as e:
                # Log but don't stop polling
                print(f"Polling error: {e}")
        
        # Polling timed out
        self._polling_active = False
        if poll_count >= max_polls:
            self.after(0, lambda: self.status_label.configure(
                text="Polling timed out. Please refresh to check status.",
                text_color="orange"
            ))

    def _on_subscription_activated(self) -> None:
        """Called when subscription is successfully activated."""
        self.after(0, lambda: self._show_upgrade_success())

    def _show_upgrade_success(self) -> None:
        """Show success message and refresh UI."""
        # Update status
        self.status_label.configure(
            text="🎉 Subscription activated! Refreshing...",
            text_color="green"
        )
        
        # Rebuild UI after a short delay to show updated plan
        self.after(2000, self._rebuild_ui)

    def _rebuild_ui(self) -> None:
        """Rebuild the subscription UI to reflect new plan."""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Rebuild
        self._setup_ui()

    def destroy(self) -> None:
        """Clean up resources when destroying the widget."""
        self._polling_active = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=1.0)
        super().destroy()

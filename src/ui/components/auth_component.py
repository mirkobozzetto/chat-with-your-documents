# src/ui/components/auth_component.py
import streamlit as st
from src.auth.auth_manager import AuthManager


class AuthComponent:

    def __init__(self):
        self.auth_manager = AuthManager()

    def render_login_form(self) -> bool:
        st.title("🔐 RAG AI Assistant - Login")

        if not self.auth_manager.config.is_auth_enabled():
            st.info("Authentication is disabled")
            return True

        if not self.auth_manager.config.has_global_access():
            st.error("🚫 Service temporarily unavailable")
            st.stop()

        with st.form("login_form"):
            st.subheader("Please login to continue")

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            col1, col2 = st.columns([1, 3])
            with col1:
                submit = st.form_submit_button("Login", type="primary")

            if submit:
                return self._handle_login_attempt(username, password)

        self._render_login_footer()
        return False

    def _handle_login_attempt(self, username: str, password: str) -> bool:
        if not username or not password:
            st.error("Please enter both username and password")
            return False

        if self.auth_manager.authenticate_user(username, password):
            self.auth_manager.login_user(username)
            st.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")
            return False

    def _render_login_footer(self) -> None:
        st.markdown("---")
        auth_status = self.auth_manager.config.get_auth_status()

        if auth_status["total_users"] > 0:
            st.info(f"📊 {auth_status['total_users']} authorized users configured")
        else:
            st.warning("⚠️ No users configured. Check AUTH_USERS environment variable.")

    def render_user_info(self) -> None:
        if not self.auth_manager.is_user_authenticated():
            return

        session_info = self.auth_manager.get_session_info()

        with st.sidebar:
            st.markdown("---")
            st.subheader(f"👤 {session_info['username']}")

            time_remaining = session_info['time_remaining']
            hours_left = int(time_remaining.total_seconds() // 3600)

            if hours_left > 1:
                st.text(f"Session: {hours_left}h remaining")
            else:
                minutes_left = int(time_remaining.total_seconds() // 60)
                st.text(f"Session: {minutes_left}m remaining")

            if st.button("🚪 Logout"):
                self.auth_manager.logout_user()
                st.rerun()

    def render_auth_status(self) -> None:
        if not self.auth_manager.config.is_auth_enabled():
            return

        with st.expander("🔐 Authentication Status"):
            auth_status = self.auth_manager.config.get_auth_status()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Auth Enabled", "✅" if auth_status["auth_enabled"] else "❌")
            with col2:
                st.metric("Global Access", "✅" if auth_status["global_access"] else "❌")

            st.metric("Configured Users", auth_status["total_users"])

            if auth_status["configured_users"]:
                st.text("Users: " + ", ".join(auth_status["configured_users"]))

    def check_authentication(self) -> bool:
        self.auth_manager.refresh_session()

        if self.auth_manager.is_user_authenticated():
            return True

        return self.render_login_form()

    def protect_app(self) -> bool:
        if not self.auth_manager.config.is_auth_enabled():
            return True

        return self.check_authentication()

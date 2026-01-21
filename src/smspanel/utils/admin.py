"""Admin utilities for common user management operations."""

from flask import redirect, url_for, flash
from flask_login import current_user

from smspanel import db
from smspanel.models import User
from smspanel.constants.messages import (
    AUTH_USER_NOT_FOUND,
    USER_CANNOT_DISABLE_SELF,
    USER_CANNOT_DELETE_SELF,
)


def get_user_or_redirect(user_id: int, redirect_route: str = "web.web_admin.users"):
    """Get user by ID or redirect with error if not found.

    Args:
        user_id: User ID to look up.
        redirect_route: Route name to redirect to if user not found.

    Returns:
        User object or redirect response.
    """
    user = db.session.get(User, user_id)
    if not user:
        flash(AUTH_USER_NOT_FOUND, "error")
        return redirect(url_for(redirect_route))
    return user


def check_self_action_allowed(user: User, action_type: str = "modify"):
    """Check if admin can perform action on themselves.

    Args:
        user: User to check.
        action_type: Type of action (for error message). Default: "modify".

    Returns:
        True if allowed, otherwise returns redirect response.
    """
    if user.id == current_user.id:
        if action_type == "disable":
            flash(USER_CANNOT_DISABLE_SELF, "error")
        elif action_type == "delete":
            flash(USER_CANNOT_DELETE_SELF, "error")
        else:
            flash(f"You cannot {action_type} yourself.", "error")
        return redirect(url_for("web.web_admin.users"))
    return True


def validate_passwords_match(password: str, confirm_password: str):
    """Validate that password and confirmation match.

    Args:
        password: Password value.
        confirm_password: Confirmation password value.

    Returns:
        True if match, otherwise returns False.
    """
    return password == confirm_password

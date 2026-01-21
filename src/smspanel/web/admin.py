"""Admin routes for user management."""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.wrappers import Response

from smspanel.models import User
from smspanel.constants.messages import (
    AUTH_USERNAME_PASSWORD_REQUIRED,
    AUTH_PASSWORDS_DO_NOT_MATCH,
    AUTH_NEW_PASSWORD_REQUIRED,
    AUTH_ADMIN_REQUIRED,
    AUTH_LOGIN_REQUIRED,
    USER_CREATED,
    USER_ALREADY_EXISTS,
    USER_PASSWORD_CHANGED,
    USER_ENABLED,
    USER_DISABLED,
    USER_DELETED,
    USER_TOKEN_REGENERATED,
)
from smspanel.utils.admin import get_user_or_redirect, check_self_action_allowed, validate_passwords_match
from smspanel.utils.database import db_transaction

web_admin_bp = Blueprint("web_admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to require admin access."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash(AUTH_LOGIN_REQUIRED, "error")
            return redirect(url_for("web.web_auth.login"))
        if not current_user.is_admin:
            flash(AUTH_ADMIN_REQUIRED, "error")
            return redirect(url_for("web.web_sms.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


@web_admin_bp.route("/users")
@login_required
@admin_required
def users():
    """List all users with actions."""
    # Sort by username ascending, admins at bottom
    users = User.query.order_by(User.is_admin.asc(), User.username.asc()).all()
    return render_template("admin/users.html", users=users)


@web_admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    """Create a new user."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        is_admin = request.form.get("is_admin") == "on"

        if not username or not password:
            flash(AUTH_USERNAME_PASSWORD_REQUIRED, "error")
            return render_template("admin/create_user.html")

        if not validate_passwords_match(password, confirm_password):
            flash(AUTH_PASSWORDS_DO_NOT_MATCH, "error")
            return render_template("admin/create_user.html")

        if User.query.filter_by(username=username).first():
            flash(USER_ALREADY_EXISTS, "error")
            return render_template("admin/create_user.html")

        user = User(username=username)
        user.set_password(password)
        user.token = User.generate_token()
        user.is_admin = is_admin
        user.is_active = True

        with db_transaction() as session:
            session.add(user)

        flash(USER_CREATED.format(username=username), "success")
        return redirect(url_for("web.web_admin.users"))

    return render_template("admin/create_user.html")


@web_admin_bp.route("/users/<int:user_id>/password", methods=["GET", "POST"])
@login_required
@admin_required
def change_password(user_id):
    """Change user password."""
    user = get_user_or_redirect(user_id)
    if isinstance(user, Response):
        return user

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password:
            flash(AUTH_NEW_PASSWORD_REQUIRED, "error")
            return render_template("admin/change_password.html", user=user)

        if not validate_passwords_match(new_password, confirm_password):
            flash(AUTH_PASSWORDS_DO_NOT_MATCH, "error")
            return render_template("admin/change_password.html", user=user)

        user.set_password(new_password)
        with db_transaction() as session:
            session.add(user)

        flash(USER_PASSWORD_CHANGED.format(username=user.username), "success")
        return redirect(url_for("web.web_admin.users"))

    return render_template("admin/change_password.html", user=user)


@web_admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    """Toggle user active status (enable/disable)."""
    user = get_user_or_redirect(user_id)
    if isinstance(user, Response):
        return user

    # Prevent disabling self
    check_result = check_self_action_allowed(user, "disable")
    if isinstance(check_result, Response):
        return check_result

    user.is_active = not user.is_active
    with db_transaction() as session:
        session.add(user)

    message = USER_ENABLED if user.is_active else USER_DISABLED
    flash(message.format(username=user.username), "success")
    return redirect(url_for("web.web_admin.users"))


@web_admin_bp.route("/users/<int:user_id>/delete", methods=["GET", "POST"])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user."""
    user = get_user_or_redirect(user_id)
    if isinstance(user, Response):
        return user

    # Prevent deleting self
    check_result = check_self_action_allowed(user, "delete")
    if isinstance(check_result, Response):
        return check_result

    if request.method == "POST":
        username = user.username
        with db_transaction() as session:
            session.delete(user)

        flash(USER_DELETED.format(username=username), "success")
        return redirect(url_for("web.web_admin.users"))

    return render_template("admin/delete_user.html", user=user)


@web_admin_bp.route("/users/<int:user_id>/regenerate_token", methods=["POST"])
@login_required
@admin_required
def regenerate_token(user_id):
    """Regenerate the API token for a user."""
    user = get_user_or_redirect(user_id)
    if isinstance(user, Response):
        return user

    user.token = User.generate_token()
    with db_transaction() as session:
        session.add(user)

    flash(USER_TOKEN_REGENERATED.format(username=user.username), "success")
    return redirect(url_for("web.web_admin.users"))

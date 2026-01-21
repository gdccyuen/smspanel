"""Web UI authentication routes."""

from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

from smspanel import db, login_manager
from smspanel.models import User
from smspanel.constants.messages import (
    AUTH_USERNAME_PASSWORD_REQUIRED,
    AUTH_INVALID_CREDENTIALS,
)

web_auth_bp = Blueprint("web_auth", __name__)


@login_manager.user_loader
def load_user(user_id: int):
    """Load user by ID for Flask-Login."""
    return db.session.get(User, int(user_id))


@web_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash(AUTH_USERNAME_PASSWORD_REQUIRED, "error")
            return render_template("login.html")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash(AUTH_INVALID_CREDENTIALS, "error")
            return render_template("login.html")

        login_user(user)
        next_page = request.args.get("next")
        return redirect(next_page or url_for("web.web_sms.dashboard"))

    return render_template("login.html")


@web_auth_bp.route("/logout")
@login_required
def logout():
    """User logout."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("web.web_auth.login"))

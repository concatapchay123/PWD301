"""Route handlers for Web UI authentication (Flask-Login with session cookies)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user

from pwd301.blueprints.auth import auth_bp
from pwd301.services.exceptions import ServiceError
from pwd301.services.session_auth_service import (
    create_auth_session,
    revoke_auth_session,
)
from pwd301.services.user_service import (
    get_user_by_email,
    register_user,
    verify_password,
)


def _is_safe_redirect_url(target: str) -> bool:
    """Validate that target redirect URL is strictly local and cannot trigger open redirect."""
    if not target or not isinstance(target, str):
        return False
    # Backslashes are normalized to slashes in modern browsers (e.g. /\attacker.com)
    if "\\" in target:
        return False
    try:
        parsed = urlsplit(target)
    except Exception:
        return False
    if parsed.scheme or parsed.netloc:
        return False
    return parsed.path.startswith("/") and not parsed.path.startswith("//")


def _is_json_request() -> bool:
    """Determine whether request explicitly asks for or provides JSON."""
    if request.is_json:
        return True
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json"


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Any:
    """Handle user login for Web UI and same-origin AJAX."""
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("core.index"))
        return render_template("auth/login.html")

    # POST processing
    if request.is_json:
        data: dict[str, Any] = request.get_json() or {}
        email = str(data.get("email", "")).strip()
        password = str(data.get("password", ""))
        remember = bool(data.get("remember", False))
        next_url = str(data.get("next", ""))
    else:
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))
        next_url = request.args.get("next") or request.form.get("next", "")

    # Credential verification
    user = get_user_by_email(email)
    if user is None or not verify_password(user, password):
        if _is_json_request():
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_CREDENTIALS",
                            "message": "Email hoặc mật khẩu không chính xác.",
                        }
                    }
                ),
                401,
            )
        flash("Email hoặc mật khẩu không chính xác.", "danger")
        return render_template("auth/login.html"), 401

    # Active status verification
    if not user.is_active:
        if _is_json_request():
            return (
                jsonify(
                    {
                        "error": {
                            "code": "ACCOUNT_INACTIVE",
                            "message": "Tài khoản đã bị tạm khóa hoặc ngừng kích hoạt.",
                        }
                    }
                ),
                403,
            )
        flash("Tài khoản đã bị tạm khóa hoặc ngừng kích hoạt.", "danger")
        return render_template("auth/login.html"), 403

    # Create server-side AuthSession in database
    user_agent_str = request.user_agent.string if request.user_agent else None
    auth_session, raw_session_key = create_auth_session(
        user=user,
        ip_address=request.remote_addr,
        user_agent=user_agent_str,
    )

    # Establish Flask-Login session identity
    login_user(user, remember=remember)

    # Store session-integrity values in Flask session cookie
    session["auth_session_key"] = raw_session_key
    session["auth_version"] = user.auth_version
    if user.roles:
        session["active_role"] = user.roles[0].code

    # Safe next_url redirect to prevent open-redirect vulnerabilities
    target_url = url_for("core.index")
    if next_url and _is_safe_redirect_url(next_url):
        target_url = next_url

    if _is_json_request():
        return (
            jsonify(
                {
                    "status": "ok",
                    "message": "Đăng nhập thành công.",
                    "redirect_url": target_url,
                    "user": {
                        "public_id": str(user.public_id),
                        "email": user.email,
                        "display_name": user.display_name,
                    },
                }
            ),
            200,
        )

    flash("Đăng nhập thành công!", "success")
    return redirect(target_url)


@auth_bp.route("/logout", methods=["POST"])
def logout() -> Any:
    """Handle user logout: revokes server-side session and clears client session."""
    raw_session_key = session.get("auth_session_key")
    if raw_session_key:
        revoke_auth_session(raw_session_key)

    logout_user()
    session.clear()

    if _is_json_request():
        return jsonify({"status": "ok", "message": "Đăng xuất thành công."}), 200

    flash("Bạn đã đăng xuất thành công.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> Any:
    """Handle user registration for Web UI."""
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("core.index"))
        return render_template("auth/register.html")

    # POST processing
    if request.is_json:
        data: dict[str, Any] = request.get_json() or {}
        display_name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        password = str(data.get("password", ""))
    else:
        display_name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

    try:
        user = register_user(
            email=email,
            password=password,
            display_name=display_name,
        )
    except ServiceError as exc:
        if _is_json_request():
            return (
                jsonify(
                    {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": str(exc),
                        }
                    }
                ),
                400,
            )
        flash(str(exc), "danger")
        return render_template("auth/register.html"), 400

    if _is_json_request():
        return (
            jsonify(
                {
                    "status": "ok",
                    "message": "Đăng ký tài khoản thành công!",
                    "public_id": str(user.public_id),
                }
            ),
            201,
        )

    flash("Đăng ký tài khoản thành công! Vui lòng đăng nhập.", "success")
    return redirect(url_for("auth.login"))

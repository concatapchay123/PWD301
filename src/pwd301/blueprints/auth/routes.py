"""Route handlers for Web UI authentication (Flask-Login with session cookies)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from flask import (
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from pwd301.blueprints.auth import auth_bp
from pwd301.services.exceptions import InvalidPasswordError, ServiceError
from pwd301.services.rate_limit_service import (
    clear_login_attempts,
    is_login_locked,
    record_failed_login,
)
from pwd301.services.session_auth_service import (
    create_auth_session,
    revoke_auth_session,
)
from pwd301.services.user_service import (
    change_password,
    generate_password_reset_token,
    get_user_by_email,
    mark_email_verified,
    register_user,
    set_password,
    verify_email_verification_token,
    verify_password,
    verify_password_reset_token,
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

    # Rate limiting & lockout check
    remote_ip = request.remote_addr or ""
    is_locked, retry_after = is_login_locked(remote_ip, email)
    if is_locked:
        msg = f"Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau {retry_after} giây."
        if _is_json_request():
            resp = jsonify(
                {
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": msg,
                    }
                }
            )
            resp.status_code = 429
            resp.headers["Retry-After"] = str(retry_after)
            return resp
        flash(msg, "danger")
        html_resp = make_response(render_template("auth/login.html"), 429)
        html_resp.headers["Retry-After"] = str(retry_after)
        return html_resp

    # Credential verification
    user = get_user_by_email(email)
    if user is None or not verify_password(user, password):
        record_failed_login(remote_ip, email)
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

    clear_login_attempts(remote_ip, email)

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


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password_view() -> Any:
    """Handle password change for authenticated users."""
    if request.method == "GET":
        return render_template("auth/change_password.html")

    if request.is_json:
        data: dict[str, Any] = request.get_json() or {}
        current_pwd = str(data.get("current_password", ""))
        new_pwd = str(data.get("new_password", ""))
        confirm_pwd = str(data.get("confirm_password", ""))
    else:
        current_pwd = request.form.get("current_password", "")
        new_pwd = request.form.get("new_password", "")
        confirm_pwd = request.form.get("confirm_password", "")

    if not current_pwd or not new_pwd:
        msg = "Vui lòng nhập đầy đủ mật khẩu hiện tại và mật khẩu mới."
        if _is_json_request():
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": msg}}), 400
        flash(msg, "danger")
        return render_template("auth/change_password.html"), 400

    if new_pwd != confirm_pwd:
        msg = "Mật khẩu xác nhận không khớp với mật khẩu mới."
        if _is_json_request():
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": msg}}), 400
        flash(msg, "danger")
        return render_template("auth/change_password.html"), 400

    try:
        user = change_password(
            user_id=current_user.id,
            current_password=current_pwd,
            new_password=new_pwd,
        )
    except (InvalidPasswordError, ServiceError) as exc:
        if _is_json_request():
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 400
        flash(str(exc), "danger")
        return render_template("auth/change_password.html"), 400

    # Since change_password increments auth_version and revokes existing sessions,
    # establish a fresh authenticated session for the current browser
    user_agent_str = request.user_agent.string if request.user_agent else None
    auth_session, raw_session_key = create_auth_session(
        user=user,
        ip_address=request.remote_addr,
        user_agent=user_agent_str,
    )
    login_user(user)
    session["auth_session_key"] = raw_session_key
    session["auth_version"] = user.auth_version

    if _is_json_request():
        return jsonify({"status": "ok", "message": "Đổi mật khẩu thành công."}), 200

    flash("Đổi mật khẩu thành công!", "success")
    return redirect(url_for("core.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password() -> Any:
    """Handle password reset request."""
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("core.index"))
        return render_template("auth/forgot_password.html")

    if request.is_json:
        data: dict[str, Any] = request.get_json() or {}
        email = str(data.get("email", "")).strip()
    else:
        email = request.form.get("email", "").strip()

    if not email:
        msg = "Vui lòng nhập địa chỉ email."
        if _is_json_request():
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": msg}}), 400
        flash(msg, "danger")
        return render_template("auth/forgot_password.html"), 400

    user = get_user_by_email(email)
    reset_token: str | None = None
    if user is not None and user.is_active:
        reset_token = generate_password_reset_token(user.id)

    # Prevent email enumeration by returning uniform success message
    msg = (
        "Nếu email tồn tại trong hệ thống, hướng dẫn đặt lại mật khẩu đã được "
        "gửi đến hộp thư của bạn."
    )
    if _is_json_request():
        payload: dict[str, Any] = {"status": "ok", "message": msg}
        if reset_token is not None:
            payload["reset_token"] = reset_token
        return jsonify(payload), 200

    flash(msg, "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str) -> Any:
    """Handle password reset using timed secure token."""
    user_id = verify_password_reset_token(token)
    if not user_id:
        msg = "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."
        if _is_json_request():
            return jsonify({"error": {"code": "INVALID_TOKEN", "message": msg}}), 400
        flash(msg, "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "GET":
        return render_template("auth/reset_password.html", token=token)

    if request.is_json:
        data: dict[str, Any] = request.get_json() or {}
        new_pwd = str(data.get("password", "") or data.get("new_password", ""))
        confirm_pwd = str(data.get("confirm_password", ""))
    else:
        new_pwd = request.form.get("password", "") or request.form.get("new_password", "")
        confirm_pwd = request.form.get("confirm_password", "")

    if not new_pwd:
        msg = "Vui lòng nhập mật khẩu mới."
        if _is_json_request():
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": msg}}), 400
        flash(msg, "danger")
        return render_template("auth/reset_password.html", token=token), 400

    if new_pwd != confirm_pwd:
        msg = "Mật khẩu xác nhận không khớp với mật khẩu mới."
        if _is_json_request():
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": msg}}), 400
        flash(msg, "danger")
        return render_template("auth/reset_password.html", token=token), 400

    try:
        set_password(user_id=user_id, new_password=new_pwd)
    except (InvalidPasswordError, ServiceError) as exc:
        if _is_json_request():
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 400
        flash(str(exc), "danger")
        return render_template("auth/reset_password.html", token=token), 400

    msg = "Đặt lại mật khẩu thành công! Vui lòng đăng nhập bằng mật khẩu mới."
    if _is_json_request():
        return jsonify({"status": "ok", "message": msg}), 200

    flash(msg, "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/verify-email/<token>", methods=["GET"])
def verify_email(token: str) -> Any:
    """Verify user email address using secure timed token."""
    user_id = verify_email_verification_token(token)
    if not user_id:
        msg = "Liên kết xác thực email không hợp lệ hoặc đã hết hạn."
        if _is_json_request():
            return jsonify({"error": {"code": "INVALID_TOKEN", "message": msg}}), 400
        flash(msg, "danger")
        return redirect(url_for("auth.login"))

    try:
        mark_email_verified(user_id)
    except ServiceError as exc:
        if _is_json_request():
            return jsonify({"error": {"code": "VERIFICATION_ERROR", "message": str(exc)}}), 400
        flash(str(exc), "danger")
        return redirect(url_for("auth.login"))

    msg = "Email đã được xác thực thành công!"
    if _is_json_request():
        return jsonify({"status": "ok", "message": msg}), 200

    flash(msg, "success")
    return redirect(url_for("auth.login"))

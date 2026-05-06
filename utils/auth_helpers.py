"""
Helpers para autenticación y autorización - Proyecto TITA
Basado en: docs/RBAC_PERFILES_PERMISOS.md
Roles: admin, operator, viewer
"""
import streamlit as st
from functools import wraps
from config.auth_config import has_permission, get_role_info, is_admin, ROLES


def require_auth(func):
    """Decorator que requiere sesión activa"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authentication_status", False):
            st.error("🔒 Debes iniciar sesión para acceder a esta función")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_permission(permission: str):
    """Decorator para requerir un permiso RBAC específico"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not st.session_state.get("authentication_status", False):
                st.error("🔒 Debes iniciar sesión para acceder a esta función")
                st.stop()

            role = st.session_state.get("role", "viewer")
            if not has_permission(role, permission):
                st.error(f"⛔ No tienes permisos suficientes (requiere: {permission})")
                st.stop()

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(func):
    """Decorator que requiere rol admin"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authentication_status", False):
            st.error("🔒 Debes iniciar sesión")
            st.stop()
        if not is_admin(st.session_state.get("role", "")):
            st.error("⛔ Acción reservada para administradores")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def check_permission(permission: str) -> bool:
    """Verifica si el usuario actual tiene un permiso (sin bloquear)"""
    if not st.session_state.get("authentication_status", False):
        return False
    role = st.session_state.get("role", "viewer")
    return has_permission(role, permission)


def check_is_admin() -> bool:
    """Verifica si el usuario actual es admin"""
    if not st.session_state.get("authentication_status", False):
        return False
    return is_admin(st.session_state.get("role", ""))


def get_current_user() -> dict:
    """Retorna información del usuario actual o None si no está autenticado"""
    if not st.session_state.get("authentication_status", False):
        return None

    role = st.session_state.get("role", "viewer")
    role_info = get_role_info(role)

    return {
        "username": st.session_state.get("username", ""),
        "name": st.session_state.get("name", ""),
        "role": role,
        "role_label": role_info["label"],
        "role_icon": role_info["icon"],
    }


def render_user_badge():
    """Renderiza badge del usuario en sidebar con rol y permisos"""
    user = get_current_user()
    if not user:
        return

    st.sidebar.markdown(f"""
    <div style="padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-bottom: 10px;">
        <p style="margin: 0; font-size: 14px;"><strong>{user['role_icon']} {user['name']}</strong></p>
        <p style="margin: 0; font-size: 12px; color: #666;">{user['role_label']}</p>
    </div>
    """, unsafe_allow_html=True)


def render_permission_denied(action: str = ""):
    """Renderiza mensaje de permiso denegado de forma uniforme"""
    msg = "⛔ No tienes permisos para esta acción"
    if action:
        msg += f": {action}"
    st.warning(msg)

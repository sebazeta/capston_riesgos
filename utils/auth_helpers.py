"""
Helpers para autenticación y autorización
"""
import streamlit as st
from config.auth_config import has_permission

def require_permission(permission: str):
    """Decorator para requerir permisos específicos"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'authentication_status' not in st.session_state:
                st.error("🔒 Debes iniciar sesión para acceder a esta función")
                st.stop()
            
            if not st.session_state.authentication_status:
                st.error("🔒 Debes iniciar sesión para acceder a esta función")
                st.stop()
            
            role = st.session_state.get('role', 'auditor')
            if not has_permission(role, permission):
                st.error(f"⛔ No tienes permisos suficientes para esta acción (requiere: {permission})")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_permission(permission: str) -> bool:
    """Verifica si el usuario actual tiene un permiso"""
    if 'authentication_status' not in st.session_state:
        return False
    
    if not st.session_state.authentication_status:
        return False
    
    role = st.session_state.get('role', 'auditor')
    return has_permission(role, permission)

def get_current_user() -> dict:
    """Retorna información del usuario actual"""
    if not st.session_state.get('authentication_status', False):
        return None
    
    return {
        'username': st.session_state.get('username', ''),
        'name': st.session_state.get('name', ''),
        'role': st.session_state.get('role', 'auditor')
    }

def render_user_badge():
    """Renderiza badge del usuario en sidebar"""
    user = get_current_user()
    if not user:
        return
    
    role_emojis = {
        'admin': '👑',
        'analyst': '🔬',
        'auditor': '🔍'
    }
    
    role_names = {
        'admin': 'Administrador',
        'analyst': 'Analista',
        'auditor': 'Auditor'
    }
    
    emoji = role_emojis.get(user['role'], '👤')
    role_name = role_names.get(user['role'], 'Usuario')
    
    st.sidebar.markdown(f"""
    <div style="padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-bottom: 10px;">
        <p style="margin: 0; font-size: 14px;"><strong>{emoji} {user['name']}</strong></p>
        <p style="margin: 0; font-size: 12px; color: #666;">{role_name}</p>
    </div>
    """, unsafe_allow_html=True)

"""
Configuración de autenticación para Proyecto TITA
Basado en: docs/RBAC_PERFILES_PERMISOS.md
Roles: admin, operator, viewer
"""
from pathlib import Path

# ==================== ROLES DEFINIDOS ====================
ROLES = {
    "admin": {
        "label": "Administrador",
        "description": "Superusuario con control total del sistema",
        "icon": ""
    },
    "operator": {
        "label": "Operador / Analista",
        "description": "Analista de riesgos con permisos de operación diaria",
        "icon": ""
    },
    "viewer": {
        "label": "Consulta",
        "description": "Usuario de solo lectura para consulta de resultados",
        "icon": ""
    }
}

# ==================== PERMISOS POR ROL (RBAC) ====================
ROLE_PERMISSIONS = {
    "admin": {
        # Gestión de usuarios
        "can_create_users": True,
        "can_edit_users": True,
        "can_toggle_user_status": True,
        "can_assign_roles": True,
        "can_reset_other_passwords": True,
        "can_view_user_list": True,
        # Activos
        "can_create_activos": True,
        "can_edit_activos": True,
        "can_delete_activos": True,
        "can_import_activos": True,
        "can_view_activos": True,
        # Cuestionarios / Plantillas
        "can_create_plantillas": True,
        "can_edit_plantillas": True,
        "can_delete_plantillas": True,
        "can_publish_plantillas": True,
        "can_manage_preguntas": True,
        "can_respond_cuestionarios": True,
        "can_view_cuestionarios": True,
        # Evaluaciones
        "can_create_evaluaciones": True,
        "can_edit_evaluaciones": True,
        "can_delete_evaluaciones": True,
        "can_assign_evaluaciones": True,
        "can_view_evaluaciones": True,
        # IA
        "can_execute_ia": True,
        "can_execute_ia_advanced": True,
        "can_view_ia_history": True,
        "can_save_ia_recommendations": True,
        "can_validate_ia": True,
        "can_configure_ia": True,
        # Resultados / Reportes
        "can_view_dashboards": True,
        "can_view_results": True,
        "can_export_pdf": True,
        "can_export_excel": True,
        "can_view_comparativas": True,
        # Administración
        "can_edit_config_global": True,
        "can_edit_catalogos": True,
        "can_view_audit_global": True,
        "can_view_own_logs": True,
        "can_backup_db": True,
        # Perfil
        "can_edit_own_profile": True,
        "can_change_own_password": True,
    },
    "operator": {
        # Gestión de usuarios — DENEGADO
        "can_create_users": False,
        "can_edit_users": False,
        "can_toggle_user_status": False,
        "can_assign_roles": False,
        "can_reset_other_passwords": False,
        "can_view_user_list": False,
        # Activos — CONDICIONAL (ABAC por evaluación)
        "can_create_activos": True,
        "can_edit_activos": True,
        "can_delete_activos": True,
        "can_import_activos": True,
        "can_view_activos": True,
        # Cuestionarios / Plantillas — Plantillas maestras DENEGADO
        "can_create_plantillas": False,
        "can_edit_plantillas": False,
        "can_delete_plantillas": False,
        "can_publish_plantillas": False,
        "can_manage_preguntas": False,
        "can_respond_cuestionarios": True,
        "can_view_cuestionarios": True,
        # Evaluaciones — CONDICIONAL (propias/asignadas)
        "can_create_evaluaciones": True,
        "can_edit_evaluaciones": True,   # Solo propias (ABAC)
        "can_delete_evaluaciones": False,
        "can_assign_evaluaciones": False,
        "can_view_evaluaciones": True,   # Propias/asignadas (ABAC)
        # IA — CONDICIONAL (propias/asignadas)
        "can_execute_ia": True,
        "can_execute_ia_advanced": True,
        "can_view_ia_history": True,
        "can_save_ia_recommendations": True,
        "can_validate_ia": False,
        "can_configure_ia": False,
        # Resultados / Reportes — CONDICIONAL
        "can_view_dashboards": True,
        "can_view_results": True,
        "can_export_pdf": True,
        "can_export_excel": True,
        "can_view_comparativas": True,
        # Administración — DENEGADO
        "can_edit_config_global": False,
        "can_edit_catalogos": False,
        "can_view_audit_global": False,
        "can_view_own_logs": True,
        "can_backup_db": False,
        # Perfil
        "can_edit_own_profile": True,
        "can_change_own_password": True,
    },
    "viewer": {
        # Gestión de usuarios — DENEGADO
        "can_create_users": False,
        "can_edit_users": False,
        "can_toggle_user_status": False,
        "can_assign_roles": False,
        "can_reset_other_passwords": False,
        "can_view_user_list": False,
        # Activos — SOLO LECTURA
        "can_create_activos": False,
        "can_edit_activos": False,
        "can_delete_activos": False,
        "can_import_activos": False,
        "can_view_activos": True,   # Solo compartidas (ABAC)
        # Cuestionarios / Plantillas — DENEGADO
        "can_create_plantillas": False,
        "can_edit_plantillas": False,
        "can_delete_plantillas": False,
        "can_publish_plantillas": False,
        "can_manage_preguntas": False,
        "can_respond_cuestionarios": False,
        "can_view_cuestionarios": True,  # Solo compartidas (ABAC)
        # Evaluaciones — SOLO LECTURA
        "can_create_evaluaciones": False,
        "can_edit_evaluaciones": False,
        "can_delete_evaluaciones": False,
        "can_assign_evaluaciones": False,
        "can_view_evaluaciones": True,   # Solo compartidas (ABAC)
        # IA — DENEGADO
        "can_execute_ia": False,
        "can_execute_ia_advanced": False,
        "can_view_ia_history": True,     # Solo compartidas (ABAC)
        "can_save_ia_recommendations": False,
        "can_validate_ia": False,
        "can_configure_ia": False,
        # Resultados / Reportes — SOLO LECTURA compartidas
        "can_view_dashboards": True,
        "can_view_results": True,
        "can_export_pdf": True,
        "can_export_excel": True,
        "can_view_comparativas": True,
        # Administración — DENEGADO
        "can_edit_config_global": False,
        "can_edit_catalogos": False,
        "can_view_audit_global": False,
        "can_view_own_logs": True,
        "can_backup_db": False,
        # Perfil
        "can_edit_own_profile": True,
        "can_change_own_password": True,
    }
}

# ==================== ESTADOS DE CUENTA ====================
ACCOUNT_STATES = {
    "active": {"label": "Activo", "can_login": True},
    "inactive": {"label": "Inactivo", "can_login": False},
    "blocked": {"label": "Bloqueado", "can_login": False},
    "pending_verification": {"label": "Pendiente verificación", "can_login": False},
    "expired": {"label": "Verificación expirada", "can_login": False},
}

# ==================== POLÍTICA DE CONTRASEÑAS ====================
PASSWORD_POLICY = {
    "min_length": 10,
    "max_length": 128,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "disallow_username": True,
    "max_age_days": 90,
    "history_count": 5,
}

# ==================== PROTECCIÓN BRUTE FORCE ====================
BRUTE_FORCE_CONFIG = {
    "max_attempts": 5,
    "lockout_duration_minutes": 30,
    "progressive_delay": True,
    "delay_base_seconds": 1,
    "rate_limit_per_minute": 10,
    "log_all_failed_attempts": True,
}

# ==================== CONFIGURACIÓN DE COOKIE / SESIÓN ====================
COOKIE_CONFIG = {
    "name": "tita_session",
    "key": "tita_auth_cookie_key_change_in_production",  # Cambiar en producción
    "expiry_days": 1,
}

# ==================== USUARIOS POR DEFECTO (seed inicial) ====================
# Solo se usan para inicializar la BD en primera ejecución.
# Después, toda gestión es vía BD.
DEFAULT_USERS = {
    "credentials": {
        "usernames": {
            "admin": {
                "email": "admin@tita.local",
                "name": "Administrador",
                "password": "$2b$12$K8xX7tZxZxZxZxZxZxZxZeL.kNQZxZxZxZxZxZxZxZxZxZxZ",  # Cambiar
                "role": "admin",
                "status": "active"
            }
        }
    },
    "cookie": COOKIE_CONFIG,
    "preauthorized": {
        "emails": ["admin@tita.local"]
    }
}

def get_auth_config():
    """Retorna la configuración de autenticación"""
    return DEFAULT_USERS


def has_permission(role: str, permission: str) -> bool:
    """Verifica si un rol tiene un permiso específico (RBAC).
    El admin siempre tiene acceso total a todas las funciones."""
    if role == "admin":
        return True
    if role not in ROLE_PERMISSIONS:
        return False
    return ROLE_PERMISSIONS[role].get(permission, False)


def get_role_info(role: str) -> dict:
    """Retorna metadata del rol (label, descripción, icono)"""
    return ROLES.get(role, {"label": role, "description": "", "icon": "❓"})


def get_all_permissions_for_role(role: str) -> dict:
    """Retorna todos los permisos de un rol"""
    return ROLE_PERMISSIONS.get(role, {})


def is_admin(role: str) -> bool:
    """Verifica si el rol es administrador"""
    return role == "admin"


def can_login(status: str) -> bool:
    """Verifica si un estado de cuenta permite iniciar sesión"""
    state = ACCOUNT_STATES.get(status, {})
    return state.get("can_login", False)

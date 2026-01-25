"""
Configuración de autenticación para Proyecto TITA
"""
import yaml
from pathlib import Path

# Usuarios y contraseñas (en producción usar hashing real)
# Contraseña hasheada con bcrypt o similar
DEFAULT_USERS = {
    'credentials': {
        'usernames': {
            'admin': {
                'email': 'admin@tita.local',
                'name': 'Administrador',
                'password': '$2b$12$K8xX7tZxZxZxZxZxZxZxZeL.kNQZxZxZxZxZxZxZxZxZxZxZ',  # "admin123"
                'role': 'admin'
            },
            'analista': {
                'email': 'analista@tita.local',
                'name': 'Analista de Riesgos',
                'password': '$2b$12$K8xX7tZxZxZxZxZxZxZxZeL.kNQZxZxZxZxZxZxZxZxZxZxZ',  # "analista123"
                'role': 'analyst'
            },
            'auditor': {
                'email': 'auditor@tita.local',
                'name': 'Auditor',
                'password': '$2b$12$K8xX7tZxZxZxZxZxZxZxZeL.kNQZxZxZxZxZxZxZxZxZxZxZ',  # "auditor123"
                'role': 'auditor'
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'tita_auth_cookie_key_change_in_production',
        'name': 'tita_auth_cookie'
    },
    'preauthorized': {
        'emails': ['admin@tita.local']
    }
}

# Permisos por rol
ROLE_PERMISSIONS = {
    'admin': {
        'can_create_evaluations': True,
        'can_edit_evaluations': True,
        'can_delete_evaluations': True,
        'can_view_all': True,
        'can_generate_ia': True,
        'can_view_dashboards': True,
        'can_compare': True,
        'can_manage_users': True
    },
    'analyst': {
        'can_create_evaluations': True,
        'can_edit_evaluations': True,
        'can_delete_evaluations': False,
        'can_view_all': True,
        'can_generate_ia': True,
        'can_view_dashboards': True,
        'can_compare': True,
        'can_manage_users': False
    },
    'auditor': {
        'can_create_evaluations': False,
        'can_edit_evaluations': False,
        'can_delete_evaluations': False,
        'can_view_all': True,
        'can_generate_ia': False,
        'can_view_dashboards': True,
        'can_compare': True,
        'can_manage_users': False
    }
}

def get_auth_config():
    """Retorna la configuración de autenticación"""
    return DEFAULT_USERS

def has_permission(role: str, permission: str) -> bool:
    """Verifica si un rol tiene un permiso específico"""
    if role not in ROLE_PERMISSIONS:
        return False
    return ROLE_PERMISSIONS[role].get(permission, False)

def save_auth_config(config_path: Path = None):
    """Guarda la configuración de autenticación en un archivo YAML"""
    if config_path is None:
        config_path = Path(__file__).parent / 'auth.yaml'
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(DEFAULT_USERS, f, default_flow_style=False, allow_unicode=True)

def load_auth_config(config_path: Path = None) -> dict:
    """Carga la configuración de autenticación desde un archivo YAML"""
    if config_path is None:
        config_path = Path(__file__).parent / 'auth.yaml'
    
    if not config_path.exists():
        return DEFAULT_USERS
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

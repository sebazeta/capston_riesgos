"""
COMPONENTE DE LOGIN - PROYECTO TITA
=====================================
Interfaz de inicio de sesión, perfil y gestión de usuarios.
Diseño inspirado en estilo corporativo oscuro con acentos teal.
"""
import streamlit as st
import datetime as dt
from services.auth_service import (
    init_auth_tables, seed_default_users,
    authenticate, change_own_password, update_own_profile,
    create_user, get_all_users, get_user_by_id, update_user,
    toggle_user_status, admin_reset_password, delete_user,
    get_auth_logs, log_auth_event
)
from config.auth_config import ROLES, has_permission, get_role_info


# ==================== INICIALIZACIÓN ====================

def init_auth():
    """Inicializa tablas y usuarios por defecto"""
    init_auth_tables()
    seed_default_users()


def is_authenticated() -> bool:
    """Verifica si el usuario está autenticado"""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict:
    """Retorna datos del usuario actual"""
    if not is_authenticated():
        return None
    return st.session_state.get("user_data", None)


def logout():
    """Cierra sesión"""
    user = get_current_user()
    if user:
        log_auth_event("LOGOUT", user_id=user.get("id"), username=user.get("username"))
    for key in ["authenticated", "user_data", "login_error"]:
        if key in st.session_state:
            del st.session_state[key]


# ==================== CSS LOGIN ====================

LOGIN_CSS = """
<style>
/* ===== FONDO Y CONTENEDOR LOGIN ===== */
[data-testid="stApp"] > div:first-child {
    background: linear-gradient(160deg, #0a1628 0%, #0f2027 30%, #1a3a4a 70%, #0f2027 100%);
}

[data-testid="column"]:nth-child(2) > [data-testid="stVerticalBlockBorderWrapper"] > div {
    max-width: 480px;
    margin: 0 auto;
    padding: 2.5rem 2rem;
}

/* ===== HEADER ===== */
.login-header {
    text-align: center;
    margin-bottom: 2rem;
}

.login-header h1 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #e0e8f0;
    letter-spacing: 3px;
    padding: 0.8rem 2rem;
    background: rgba(26, 82, 118, 0.45);
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 0.5rem;
}

.login-subtitle {
    color: #7eb8c9;
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

/* ===== TOGGLE PERSONA/COMERCIO ===== */
.role-toggle {
    display: flex;
    justify-content: center;
    margin: 1.5rem 0 2rem 0;
}

.role-toggle-inner {
    display: inline-flex;
    border: 2px solid #2ec4b6;
    border-radius: 30px;
    overflow: hidden;
    background: rgba(46, 196, 182, 0.08);
}

.role-btn {
    padding: 0.55rem 1.8rem;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #2ec4b6;
    background: transparent;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
}

.role-btn.active {
    background: #2ec4b6;
    color: #0a1628;
}

.role-btn svg {
    width: 18px;
    height: 18px;
}

/* ===== LABELS DE CAMPO ===== */
.field-label {
    text-align: center;
    color: #c8d8e4;
    font-size: 0.95rem;
    font-weight: 500;
    margin-bottom: 0.3rem;
    text-decoration: underline;
    text-underline-offset: 4px;
    text-decoration-color: rgba(200, 216, 228, 0.4);
}

/* ===== INPUTS ===== */
[data-testid="column"]:nth-child(2) input[type="text"],
[data-testid="column"]:nth-child(2) input[type="password"],
[data-testid="column"]:nth-child(2) .stTextInput input {
    background: #f5f5f5 !important;
    border: 2px solid #2ec4b6 !important;
    border-radius: 25px !important;
    padding: 0.7rem 1.2rem !important;
    font-size: 1rem !important;
    color: #1a1a2e !important;
    text-align: center !important;
    width: 100% !important;
}

[data-testid="column"]:nth-child(2) .stTextInput input:focus {
    border-color: #26a69a !important;
    box-shadow: 0 0 8px rgba(46, 196, 182, 0.3) !important;
}

/* Ocultar labels nativos streamlit dentro del login */
[data-testid="column"]:nth-child(2) .stTextInput label,
[data-testid="column"]:nth-child(2) .stSelectbox label {
    display: none !important;
}

/* ===== BOTÓN LOGIN ===== */
[data-testid="column"]:nth-child(2) .stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #2ec4b6 0%, #1a9e94 100%) !important;
    color: #0a1628 !important;
    border: none !important;
    border-radius: 25px !important;
    padding: 0.75rem 2rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    margin-top: 1rem !important;
}

[data-testid="column"]:nth-child(2) .stButton > button:hover {
    background: linear-gradient(135deg, #26a69a 0%, #158a80 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(46, 196, 182, 0.35) !important;
}

/* ===== MENSAJES ===== */
.login-error {
    background: rgba(255, 82, 82, 0.15);
    border-left: 4px solid #ff5252;
    color: #ff8a80;
    padding: 0.7rem 1rem;
    border-radius: 6px;
    margin-top: 1rem;
    font-size: 0.9rem;
    text-align: center;
}

.login-info {
    background: rgba(46, 196, 182, 0.1);
    border-left: 4px solid #2ec4b6;
    color: #7eb8c9;
    padding: 0.6rem 1rem;
    border-radius: 6px;
    margin-top: 1.2rem;
    font-size: 0.8rem;
    text-align: center;
}

/* ===== FOOTER ===== */
.login-footer {
    text-align: center;
    color: #4a6a7a;
    font-size: 0.75rem;
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(46, 196, 182, 0.15);
}

/* ===== OCULTAR ELEMENTOS DE STREAMLIT EN LOGIN ===== */
.login-page header[data-testid="stHeader"],
.login-page [data-testid="stSidebar"],
.login-page footer,
.login-page #MainMenu {
    display: none !important;
}
</style>
"""

# ==================== PANTALLA DE LOGIN ====================

def render_login_page():
    """Renderiza la pantalla de inicio de sesión"""

    # Ocultar sidebar y header en login
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { background: transparent !important; }
        footer { display: none !important; }
        #MainMenu { display: none !important; }
        [data-testid="stApp"] > div:first-child {
            background: linear-gradient(160deg, #0a1628 0%, #0f2027 30%, #1a3a4a 70%, #0f2027 100%);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # Espaciado superior
    st.markdown("<br>", unsafe_allow_html=True)

    # Contenedor principal
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:


        st.markdown("""
        <div class="login-header">
            <h1>INICIO DE SESIÓN</h1>
            <p class="login-subtitle">Sistema de Gestión de Riesgos TITA</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            # Campo usuario
            st.markdown('<p class="field-label">Nombre de Usuario</p>', unsafe_allow_html=True)
            username = st.text_input("Usuario", key="login_username", label_visibility="collapsed",
                                      placeholder="Ingresa tu usuario")

            # Campo contraseña
            st.markdown('<p class="field-label">Contraseña</p>', unsafe_allow_html=True)
            password = st.text_input("Contraseña", type="password", key="login_password",
                                      label_visibility="collapsed", placeholder="Ingresa tu contraseña")

            # Botón login
            submitted = st.form_submit_button("INICIAR SESIÓN", type="primary", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.session_state["login_error"] = "Ingresa usuario y contraseña"
                else:
                    success, user_data, message = authenticate(username.strip(), password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["user_data"] = user_data
                        st.session_state["login_error"] = None
                        st.rerun()
                    else:
                        st.session_state["login_error"] = message

        # Error message
        if st.session_state.get("login_error"):
            st.markdown(
                f'<div class="login-error">⚠ {st.session_state["login_error"]}</div>',
                unsafe_allow_html=True
            )

        # Footer
        st.markdown("""
        <div class="login-footer">
            TITA v2.5 — Evaluación de Riesgos MAGERIT + ISO/IEC 27002:2022<br>
            Proyecto Capstone · 2026
        </div>
        """, unsafe_allow_html=True)




# ==================== BADGE DE USUARIO (SIDEBAR) ====================

def render_sidebar_user():
    """Renderiza info del usuario y botón logout en el sidebar"""
    user = get_current_user()
    if not user:
        return

    role_info = get_role_info(user["role"])

    st.sidebar.markdown(f"""
    <div style="
        padding: 12px 16px;
        background: linear-gradient(135deg, #1a3a4a 0%, #0f2027 100%);
        border: 1px solid rgba(46, 196, 182, 0.3);
        border-radius: 10px;
        margin-bottom: 12px;
    ">
        <p style="margin: 0; font-size: 15px; color: #e0e8f0; font-weight: 600;">
            {role_info['icon']} {user['full_name']}
        </p>
        <p style="margin: 2px 0 0 0; font-size: 12px; color: #2ec4b6;">
            {role_info['label']} &middot; @{user['username']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Cerrar Sesión", use_container_width=True, key="btn_logout"):
        logout()
        st.rerun()


# ==================== PESTAÑA MI PERFIL ====================

def render_mi_perfil():
    """Renderiza la pestaña de perfil del usuario"""
    user = get_current_user()
    if not user:
        st.error("No autenticado")
        return

    st.header("Mi Perfil")

    role_info = get_role_info(user["role"])

    # Styled profile card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(46,196,182,0.08) 0%, rgba(12,26,46,0.4) 100%);
                border: 1px solid rgba(46,196,182,0.15); border-radius:14px;
                padding:1.5rem; margin-bottom:1.2rem;">
        <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
            <div style="width:56px; height:56px; background: linear-gradient(135deg, #2ec4b6, #1a9e94);
                        border-radius:50%; display:flex; align-items:center; justify-content:center;
                        font-size:1.6rem; color:#0a1628; font-weight:800;">
                {user['full_name'][0].upper()}
            </div>
            <div>
                <h3 style="color:#e0eff8; margin:0; font-size:1.2rem; border:none; padding:0;">{user['full_name']}</h3>
                <span style="color:#2ec4b6; font-size:0.85rem;">{role_info['icon']} {role_info['label']}</span>
                <span style="color:#5a8898; font-size:0.85rem;"> · @{user['username']}</span>
            </div>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.6rem;">
            <div style="background:rgba(10,22,40,0.5); border-radius:8px; padding:0.6rem 0.8rem;">
                <span style="color:#5a8898; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px;">Email</span><br>
                <span style="color:#c0ccd8; font-size:0.88rem;">{user['email']}</span>
            </div>
            <div style="background:rgba(10,22,40,0.5); border-radius:8px; padding:0.6rem 0.8rem;">
                <span style="color:#5a8898; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px;">Último Acceso</span><br>
                <span style="color:#c0ccd8; font-size:0.88rem;">{user.get('last_login', 'N/A')}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Editar Perfil")
        with st.form("form_edit_profile"):
            new_name = st.text_input("Nombre completo", value=user["full_name"])
            new_email = st.text_input("Email", value=user["email"])
            if st.form_submit_button("Guardar cambios"):
                ok, msg = update_own_profile(user["id"], new_name, new_email)
                if ok:
                    st.success(msg)
                    st.session_state["user_data"]["full_name"] = new_name
                    st.session_state["user_data"]["email"] = new_email
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()
    st.subheader("Cambiar Contraseña")

    with st.form("form_change_password"):
        current_pw = st.text_input("Contraseña actual", type="password")
        new_pw = st.text_input("Nueva contraseña", type="password")
        confirm_pw = st.text_input("Confirmar nueva contraseña", type="password")

        if st.form_submit_button("Cambiar contraseña"):
            if not current_pw or not new_pw:
                st.error("Completa todos los campos")
            elif new_pw != confirm_pw:
                st.error("Las contraseñas no coinciden")
            elif len(new_pw) < 6:
                st.error("Mínimo 6 caracteres")
            else:
                ok, msg = change_own_password(user["id"], current_pw, new_pw)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


# ==================== PESTAÑA GESTIÓN USUARIOS (ADMIN) ====================

def render_gestion_usuarios():
    """Renderiza la pestaña de gestión de usuarios (solo Admin)"""
    user = get_current_user()
    if not user or user["role"] != "admin":
        st.error("Acceso restringido a administradores")
        return

    st.header("Gestión de Usuarios")

    # ---- Crear usuario ----
    with st.expander("Crear nuevo usuario", expanded=False):
        with st.form("form_create_user"):
            c1, c2 = st.columns(2)
            with c1:
                new_username = st.text_input("Nombre de usuario*")
                new_fullname = st.text_input("Nombre completo*")
            with c2:
                new_email = st.text_input("Email*")
                new_password = st.text_input("Contraseña*", type="password")

            new_role = st.selectbox("Rol", ["operator", "viewer", "admin"],
                                    format_func=lambda r: f"{get_role_info(r)['icon']} {get_role_info(r)['label']}")

            if st.form_submit_button("Crear usuario", type="primary"):
                if not all([new_username, new_fullname, new_email, new_password]):
                    st.error("Completa todos los campos obligatorios")
                elif len(new_password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    ok, msg = create_user(
                        new_username.strip(), new_email.strip(), new_password,
                        new_fullname.strip(), new_role, user["id"]
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.divider()

    # ---- Lista de usuarios ----
    users = get_all_users()
    if not users:
        st.info("No hay usuarios registrados")
        return

    st.subheader(f"Usuarios registrados ({len(users)})")

    for u in users:
        role_info = get_role_info(u["role"])
        status_icon = {"active": "●", "inactive": "○", "blocked": "⨯"}.get(u["status"], "-")
        status_label = {"active": "Activo", "inactive": "Inactivo", "blocked": "Bloqueado"}.get(u["status"], u["status"])

        with st.expander(f"{role_info['icon']} {u['full_name']} — @{u['username']} {status_icon} {status_label}"):
            info_col, action_col = st.columns([2, 1])

            with info_col:
                st.markdown(f"""
                | Campo | Valor |
                |-------|-------|
                | **Usuario** | @{u['username']} |
                | **Nombre** | {u['full_name']} |
                | **Email** | {u['email']} |
                | **Rol** | {role_info['icon']} {role_info['label']} |
                | **Estado** | {status_icon} {status_label} |
                | **Último acceso** | {u.get('last_login', 'Nunca')} |
                | **Creado** | {u['created_at'][:16]} |
                """)

            with action_col:
                st.markdown("**Acciones:**")

                # Cambiar rol
                new_role_edit = st.selectbox(
                    "Rol", ["admin", "operator", "viewer"],
                    index=["admin", "operator", "viewer"].index(u["role"]),
                    format_func=lambda r: f"{get_role_info(r)['icon']} {get_role_info(r)['label']}",
                    key=f"role_{u['id']}"
                )
                if new_role_edit != u["role"]:
                    if st.button("Guardar rol", key=f"save_role_{u['id']}"):
                        ok, msg = update_user(u["id"], {"role": new_role_edit}, user["id"])
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                st.markdown("---")

                # Activar/Desactivar
                if u["status"] == "active":
                    if st.button("Desactivar", key=f"deact_{u['id']}"):
                        ok, msg = toggle_user_status(u["id"], "inactive", user["id"])
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    if st.button("Activar", key=f"act_{u['id']}"):
                        ok, msg = toggle_user_status(u["id"], "active", user["id"])
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                # Reset password
                new_pw_reset = st.text_input("Nueva contraseña", type="password",
                                              key=f"pw_{u['id']}", placeholder="Nueva contraseña")
                if st.button("Reset Password", key=f"reset_{u['id']}"):
                    if new_pw_reset and len(new_pw_reset) >= 6:
                        ok, msg = admin_reset_password(u["id"], new_pw_reset, user["id"])
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.error("Ingresa una contraseña de al menos 6 caracteres")

                # Eliminar (con confirmación)
                if u["id"] != user["id"]:  # No puede eliminarse a sí mismo
                    if st.button("Eliminar", key=f"del_{u['id']}", type="secondary"):
                        st.session_state[f"confirm_del_{u['id']}"] = True

                    if st.session_state.get(f"confirm_del_{u['id']}"):
                        st.warning(f"¿Eliminar a **{u['username']}**?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Sí", key=f"yes_del_{u['id']}"):
                                ok, msg = delete_user(u["id"], user["id"])
                                if ok:
                                    st.success(msg)
                                    st.session_state[f"confirm_del_{u['id']}"] = False
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with c2:
                            if st.button("No", key=f"no_del_{u['id']}"):
                                st.session_state[f"confirm_del_{u['id']}"] = False
                                st.rerun()


# ==================== PESTAÑA LOGS AUTH (ADMIN) ====================

def render_auth_logs():
    """Renderiza los logs de autenticación"""
    user = get_current_user()
    if not user or user["role"] != "admin":
        st.error("Acceso restringido")
        return

    st.header("Logs de Autenticación")

    col1, col2, col3 = st.columns(3)
    with col1:
        event_filter = st.selectbox("Filtrar por evento", [
            "Todos", "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT",
            "ACCOUNT_LOCKED", "USER_CREATED", "USER_UPDATED",
            "USER_DELETED", "USER_STATUS_CHANGED", "PASSWORD_RESET",
            "PASSWORD_CHANGE"
        ])
    with col2:
        limit = st.number_input("Máximo registros", min_value=10, max_value=500,
                                value=50, step=10)
    with col3:
        st.metric("", "")  # placeholder

    event_type = None if event_filter == "Todos" else event_filter
    logs = get_auth_logs(limit=limit, event_type=event_type)

    if not logs:
        st.info("No hay registros")
        return

    import pandas as pd
    df = pd.DataFrame(logs)
    cols_show = ["created_at", "event_type", "username", "result", "details_json"]
    cols_available = [c for c in cols_show if c in df.columns]
    df_show = df[cols_available].copy()
    df_show.columns = ["Fecha", "Evento", "Usuario", "Resultado", "Detalles"][:len(cols_available)]

    st.dataframe(df_show, use_container_width=True, hide_index=True)

"""
SERVICIO DE AUTENTICACIÓN - PROYECTO TITA
==========================================
Gestión de usuarios, autenticación y sesiones.
Almacenamiento en SQLite (tabla USERS).
Hashing con bcrypt.
Roles: admin, operator, viewer.
"""
import sqlite3
import uuid
import bcrypt
import datetime as dt
from typing import Optional, Tuple, List, Dict
from services.database_service import get_connection

# ==================== INICIALIZACIÓN ====================

def init_auth_tables():
    """Crea las tablas de autenticación si no existen"""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS USERS (
                id              TEXT PRIMARY KEY,
                username        TEXT UNIQUE NOT NULL,
                email           TEXT UNIQUE NOT NULL,
                password_hash   TEXT NOT NULL,
                full_name       TEXT NOT NULL,
                role            TEXT NOT NULL DEFAULT 'viewer',
                status          TEXT NOT NULL DEFAULT 'active',
                failed_attempts INTEGER DEFAULT 0,
                locked_until    TEXT,
                last_login      TEXT,
                must_change_password INTEGER DEFAULT 0,
                created_by      TEXT,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                CHECK (role IN ('admin', 'operator', 'viewer')),
                CHECK (status IN ('active', 'inactive', 'blocked'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AUDIT_AUTH_LOG (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type      TEXT NOT NULL,
                user_id         TEXT,
                username        TEXT,
                target_user_id  TEXT,
                target_resource TEXT,
                resource_type   TEXT,
                details_json    TEXT,
                result          TEXT DEFAULT 'success',
                created_at      TEXT NOT NULL
            )
        """)

        conn.commit()


def seed_default_users():
    """Crea usuarios por defecto si la tabla está vacía"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM USERS")
        count = cursor.fetchone()[0]

        if count == 0:
            now = dt.datetime.now().isoformat()
            users = [
                {
                    "id": str(uuid.uuid4()),
                    "username": "admin",
                    "email": "admin@tita.local",
                    "password_hash": hash_password("Admin.2026"),
                    "full_name": "Administrador TITA",
                    "role": "admin",
                    "status": "active",
                    "created_by": "system",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": str(uuid.uuid4()),
                    "username": "analista",
                    "email": "analista@tita.local",
                    "password_hash": hash_password("Analista.2026"),
                    "full_name": "Analista de Riesgos",
                    "role": "operator",
                    "status": "active",
                    "created_by": "system",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": str(uuid.uuid4()),
                    "username": "consulta",
                    "email": "consulta@tita.local",
                    "password_hash": hash_password("Consulta.2026"),
                    "full_name": "Usuario Consulta",
                    "role": "viewer",
                    "status": "active",
                    "created_by": "system",
                    "created_at": now,
                    "updated_at": now,
                },
            ]

            for u in users:
                cursor.execute("""
                    INSERT INTO USERS (id, username, email, password_hash, full_name,
                                       role, status, created_by, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    u["id"], u["username"], u["email"], u["password_hash"],
                    u["full_name"], u["role"], u["status"],
                    u["created_by"], u["created_at"], u["updated_at"]
                ))

            conn.commit()
            return True
    return False


# ==================== HASHING ====================

def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


# ==================== AUTENTICACIÓN ====================

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 30


def authenticate(username: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Autentica un usuario.
    Retorna: (éxito, datos_usuario, mensaje)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE username = ?", (username,))
        row = cursor.fetchone()

        if not row:
            log_auth_event("LOGIN_FAILED", username=username, details={"reason": "user_not_found"}, result="denied")
            return False, None, "Credenciales inválidas"

        user = dict(row)

        # Verificar estado
        if user["status"] == "inactive":
            log_auth_event("LOGIN_FAILED", user_id=user["id"], username=username,
                           details={"reason": "inactive"}, result="denied")
            return False, None, "Cuenta desactivada. Contacta al administrador."

        if user["status"] == "blocked":
            # Verificar si ya pasó el tiempo de bloqueo
            if user.get("locked_until"):
                locked = dt.datetime.fromisoformat(user["locked_until"])
                if dt.datetime.now() < locked:
                    remaining = (locked - dt.datetime.now()).seconds // 60
                    log_auth_event("LOGIN_FAILED", user_id=user["id"], username=username,
                                   details={"reason": "blocked", "minutes_remaining": remaining}, result="denied")
                    return False, None, f"Cuenta bloqueada. Intenta en {remaining + 1} minutos."
                else:
                    # Desbloquear
                    cursor.execute("""
                        UPDATE USERS SET status = 'active', failed_attempts = 0, locked_until = NULL,
                        updated_at = ? WHERE id = ?
                    """, (dt.datetime.now().isoformat(), user["id"]))
                    conn.commit()
                    user["status"] = "active"
                    user["failed_attempts"] = 0

        # Verificar password
        if not verify_password(password, user["password_hash"]):
            failed = user.get("failed_attempts", 0) + 1
            if failed >= MAX_FAILED_ATTEMPTS:
                locked_until = (dt.datetime.now() + dt.timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
                cursor.execute("""
                    UPDATE USERS SET failed_attempts = ?, status = 'blocked', locked_until = ?,
                    updated_at = ? WHERE id = ?
                """, (failed, locked_until, dt.datetime.now().isoformat(), user["id"]))
                log_auth_event("ACCOUNT_LOCKED", user_id=user["id"], username=username,
                               details={"attempts": failed})
                conn.commit()
                return False, None, f"Cuenta bloqueada por {LOCKOUT_MINUTES} minutos (máximo de intentos alcanzado)."
            else:
                cursor.execute("""
                    UPDATE USERS SET failed_attempts = ?, updated_at = ? WHERE id = ?
                """, (failed, dt.datetime.now().isoformat(), user["id"]))
                conn.commit()
                remaining = MAX_FAILED_ATTEMPTS - failed
                log_auth_event("LOGIN_FAILED", user_id=user["id"], username=username,
                               details={"reason": "wrong_password", "attempts": failed}, result="denied")
                return False, None, f"Credenciales inválidas. ({remaining} intento(s) restante(s))"

        # Login exitoso
        now = dt.datetime.now().isoformat()
        cursor.execute("""
            UPDATE USERS SET failed_attempts = 0, last_login = ?, updated_at = ? WHERE id = ?
        """, (now, now, user["id"]))
        conn.commit()

        log_auth_event("LOGIN_SUCCESS", user_id=user["id"], username=username)

        user_data = {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "status": user["status"],
            "last_login": now,
        }
        return True, user_data, "Inicio de sesión exitoso"


# ==================== GESTIÓN DE USUARIOS (ADMIN) ====================

def create_user(username: str, email: str, password: str, full_name: str,
                role: str = "viewer", created_by: str = "admin") -> Tuple[bool, str]:
    """Crea un nuevo usuario"""
    now = dt.datetime.now().isoformat()
    user_id = str(uuid.uuid4())

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verificar duplicados
            cursor.execute("SELECT id FROM USERS WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "El nombre de usuario ya existe"

            cursor.execute("SELECT id FROM USERS WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "El email ya está registrado"

            cursor.execute("""
                INSERT INTO USERS (id, username, email, password_hash, full_name,
                                   role, status, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """, (user_id, username, email, hash_password(password),
                  full_name, role, created_by, now, now))
            conn.commit()

            log_auth_event("USER_CREATED", user_id=created_by, username=created_by,
                           target_user_id=user_id,
                           details={"new_username": username, "new_role": role})

            return True, f"Usuario '{username}' creado exitosamente"
    except sqlite3.IntegrityError as e:
        return False, f"Error de integridad: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def get_all_users() -> List[Dict]:
    """Retorna todos los usuarios (sin password_hash)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, full_name, role, status,
                   failed_attempts, last_login, created_at, updated_at
            FROM USERS ORDER BY created_at
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Obtiene un usuario por ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, full_name, role, status,
                   failed_attempts, last_login, created_at, updated_at
            FROM USERS WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user(user_id: str, updates: Dict, updated_by: str = "admin") -> Tuple[bool, str]:
    """Actualiza datos de un usuario (admin)"""
    allowed_fields = {"full_name", "email", "role", "status"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered:
        return False, "No hay campos válidos para actualizar"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verificar email único si se cambia
            if "email" in filtered:
                cursor.execute("SELECT id FROM USERS WHERE email = ? AND id != ?",
                               (filtered["email"], user_id))
                if cursor.fetchone():
                    return False, "El email ya está en uso"

            sets = ", ".join(f"{k} = ?" for k in filtered)
            values = list(filtered.values())
            values.extend([dt.datetime.now().isoformat(), user_id])

            cursor.execute(f"UPDATE USERS SET {sets}, updated_at = ? WHERE id = ?", values)
            conn.commit()

            log_auth_event("USER_UPDATED", user_id=updated_by,
                           target_user_id=user_id,
                           details={"fields": list(filtered.keys())})

            return True, "Usuario actualizado"
    except Exception as e:
        return False, f"Error: {str(e)}"


def toggle_user_status(user_id: str, new_status: str, admin_id: str = "admin") -> Tuple[bool, str]:
    """Activa o desactiva un usuario"""
    if new_status not in ("active", "inactive", "blocked"):
        return False, "Estado inválido"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            now = dt.datetime.now().isoformat()

            extra = ""
            params = [new_status, now, user_id]
            if new_status == "active":
                extra = ", failed_attempts = 0, locked_until = NULL"

            cursor.execute(f"UPDATE USERS SET status = ?{extra}, updated_at = ? WHERE id = ?", params)
            conn.commit()

            log_auth_event("USER_STATUS_CHANGED", user_id=admin_id,
                           target_user_id=user_id,
                           details={"new_status": new_status})

            return True, f"Estado cambiado a '{new_status}'"
    except Exception as e:
        return False, f"Error: {str(e)}"


def admin_reset_password(user_id: str, new_password: str, admin_id: str = "admin") -> Tuple[bool, str]:
    """Admin resetea contraseña de un usuario"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE USERS SET password_hash = ?, failed_attempts = 0,
                status = 'active', locked_until = NULL, updated_at = ?
                WHERE id = ?
            """, (hash_password(new_password), dt.datetime.now().isoformat(), user_id))
            conn.commit()

            log_auth_event("PASSWORD_RESET", user_id=admin_id,
                           target_user_id=user_id,
                           details={"method": "admin_reset"})

            return True, "Contraseña reseteada exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"


def change_own_password(user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Usuario cambia su propia contraseña"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM USERS WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Usuario no encontrado"

        if not verify_password(current_password, row["password_hash"]):
            return False, "Contraseña actual incorrecta"

        if len(new_password) < 6:
            return False, "La nueva contraseña debe tener al menos 6 caracteres"

        try:
            cursor.execute("""
                UPDATE USERS SET password_hash = ?, updated_at = ? WHERE id = ?
            """, (hash_password(new_password), dt.datetime.now().isoformat(), user_id))
            conn.commit()

            log_auth_event("PASSWORD_CHANGE", user_id=user_id,
                           details={"method": "self_change"})

            return True, "Contraseña actualizada exitosamente"
        except Exception as e:
            return False, f"Error: {str(e)}"


def update_own_profile(user_id: str, full_name: str, email: str) -> Tuple[bool, str]:
    """Usuario actualiza su propio perfil"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM USERS WHERE email = ? AND id != ?", (email, user_id))
            if cursor.fetchone():
                return False, "El email ya está en uso"

            cursor.execute("""
                UPDATE USERS SET full_name = ?, email = ?, updated_at = ? WHERE id = ?
            """, (full_name, email, dt.datetime.now().isoformat(), user_id))
            conn.commit()
            return True, "Perfil actualizado"
    except Exception as e:
        return False, f"Error: {str(e)}"


def delete_user(user_id: str, admin_id: str = "admin") -> Tuple[bool, str]:
    """Elimina un usuario (solo admin, no puede eliminarse a sí mismo)"""
    if user_id == admin_id:
        return False, "No puedes eliminarte a ti mismo"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM USERS WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Usuario no encontrado"

            cursor.execute("DELETE FROM USERS WHERE id = ?", (user_id,))
            conn.commit()

            log_auth_event("USER_DELETED", user_id=admin_id,
                           target_user_id=user_id,
                           details={"deleted_username": row["username"]})

            return True, f"Usuario '{row['username']}' eliminado"
    except Exception as e:
        return False, f"Error: {str(e)}"


# ==================== AUDITORÍA ====================

def log_auth_event(event_type: str, user_id: str = None, username: str = None,
                   target_user_id: str = None, target_resource: str = None,
                   resource_type: str = None, details: Dict = None,
                   result: str = "success"):
    """Registra un evento de autenticación/autorización"""
    import json
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO AUDIT_AUTH_LOG
                (event_type, user_id, username, target_user_id, target_resource,
                 resource_type, details_json, result, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_type, user_id, username, target_user_id, target_resource,
                resource_type, json.dumps(details or {}, ensure_ascii=False),
                result, dt.datetime.now().isoformat()
            ))
            conn.commit()
    except Exception as e:
        print(f"[AUDIT ERROR] {event_type}: {e}")


def get_auth_logs(limit: int = 100, event_type: str = None, user_id: str = None) -> List[Dict]:
    """Obtiene logs de autenticación"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM AUDIT_AUTH_LOG WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if user_id:
            query += " AND (user_id = ? OR target_user_id = ?)"
            params.extend([user_id, user_id])

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

# PROPUESTA RBAC — PERFILES, PERMISOS Y SEGURIDAD
## Proyecto TITA — Sistema de Gestión y Evaluación de Riesgos

**Versión:** 1.0  
**Fecha:** 2026-02-10  
**Autor:** Arquitectura de Software  

---

## SUPOSICIONES TÉCNICAS

| Aspecto | Decisión |
|---------|----------|
| **Frontend** | Streamlit (actual) — las protecciones CSRF/CORS no aplican directamente; se controla mediante session_state |
| **Backend** | Python, servicios internos (no REST API externa por ahora) |
| **Base de datos** | SQLite (actual, `tita_riesgos.db`) |
| **Autenticación** | `streamlit-authenticator` + tablas SQLite para persistencia de usuarios |
| **Hashing** | bcrypt (ya referenciado en auth_config.py); se recomienda migrar a Argon2id |
| **Sesiones** | Cookie firmada via `streamlit-authenticator` con expiración configurable |
| **Auditoría** | Tabla `AUDITORIA_CAMBIOS` existente; se extiende con tabla `AUDIT_AUTH_LOG` |

---

## 1. DEFINICIÓN DE ROLES

### 1.1 Admin — Administrador del Sistema

| Campo | Detalle |
|-------|---------|
| **Código** | `admin` |
| **Descripción** | Superusuario con control total del sistema |
| **Responsabilidades** | Gestión de usuarios, configuración global, catálogos maestros, auditoría completa, asignación de evaluaciones |
| **Alcance** | Global — todas las evaluaciones, todos los activos, todos los usuarios |
| **Cantidad esperada** | 1–2 por instancia |

**Capacidades clave:**
- CRUD completo de usuarios (crear, editar, activar/desactivar, resetear contraseñas, asignar roles)
- Configuración global del sistema (parámetros Ollama, timeouts, modelos IA)
- CRUD total de catálogos maestros (amenazas MAGERIT, controles ISO 27002, criterios de valoración)
- CRUD total de plantillas de cuestionarios, bancos de preguntas, pesos y opciones
- Visualización completa de auditoría y logs del sistema
- Asignación de evaluaciones a usuarios/equipos
- Eliminación de información crítica (evaluaciones, activos, resultados)
- Acceso a todas las funcionalidades de Operator y Viewer

---

### 1.2 Operator — Usuario Operador / Analista

| Campo | Detalle |
|-------|---------|
| **Código** | `operator` |
| **Descripción** | Analista de riesgos con permisos amplios de operación diaria |
| **Responsabilidades** | Crear y gestionar evaluaciones propias, registrar activos, responder cuestionarios, ejecutar análisis IA, generar reportes |
| **Alcance** | Restringido a evaluaciones propias o asignadas (ABAC por evaluación) |
| **Cantidad esperada** | 3–20 por instancia |

**Capacidades clave:**
- Crear evaluaciones nuevas
- Crear, editar activos dentro de sus evaluaciones
- Importar activos masivamente (Excel/CSV) en sus evaluaciones
- Responder y completar cuestionarios asociados
- Ejecutar análisis con IA (amenazas, riesgos, recomendaciones, resumen)
- Guardar y gestionar recomendaciones generadas por IA
- Ver dashboards y resultados de sus evaluaciones
- Exportar reportes PDF/Excel de sus evaluaciones
- Ver historial de análisis IA propios

**Restricciones explícitas:**
- NO puede crear, editar, eliminar o gestionar usuarios
- NO puede asignar roles ni resetear contraseñas de terceros
- NO puede modificar configuración global del sistema
- NO puede editar catálogos maestros (amenazas, controles, criterios)
- NO puede editar plantillas de cuestionarios maestras
- NO puede ver auditoría global del sistema (solo logs propios)
- NO puede eliminar evaluaciones de otros usuarios
- NO puede ver evaluaciones no asignadas a su usuario

---

### 1.3 Viewer — Usuario de Consulta

| Campo | Detalle |
|-------|---------|
| **Código** | `viewer` |
| **Descripción** | Usuario de solo lectura para consulta de resultados |
| **Responsabilidades** | Consultar dashboards, resultados y reportes compartidos |
| **Alcance** | Solo evaluaciones explícitamente compartidas/asignadas como viewer |
| **Cantidad esperada** | 5–50 por instancia |

**Capacidades clave:**
- Iniciar sesión y gestionar su propio perfil (nombre, email, contraseña)
- Visualizar dashboards de evaluaciones compartidas
- Visualizar resultados y análisis de evaluaciones compartidas
- Descargar reportes PDF/Excel de evaluaciones compartidas (permitido)

**Restricciones explícitas:**
- NO puede crear evaluaciones
- NO puede crear, editar ni eliminar activos
- NO puede responder cuestionarios
- NO puede ejecutar análisis con IA
- NO puede modificar ningún dato del sistema
- NO puede ver evaluaciones no compartidas con su usuario
- NO puede acceder a auditoría del sistema
- NO puede gestionar usuarios, configuración ni catálogos

---

## 2. MATRIZ DE PERMISOS RBAC

### 2.1 Gestión de Usuarios

| Acción | Admin | Operator | Viewer |
|--------|:-----:|:--------:|:------:|
| Crear usuario | ✅ | ❌ | ❌ |
| Editar usuario (de terceros) | ✅ | ❌ | ❌ |
| Activar / desactivar cuentas | ✅ | ❌ | ❌ |
| Asignar / cambiar roles | ✅ | ❌ | ❌ |
| Reset contraseña de terceros | ✅ | ❌ | ❌ |
| Editar perfil propio (nombre, email) | ✅ | ✅ | ✅ |
| Cambiar contraseña propia | ✅ | ✅ | ✅ |
| Ver listado de usuarios | ✅ | ❌ | ❌ |

### 2.2 Activos (Inventario)

| Acción | Admin | Operator | Viewer |
|--------|:-----:|:--------:|:------:|
| Crear activo | ✅ | 🔶 Propias | ❌ |
| Editar activo | ✅ | 🔶 Propias | ❌ |
| Eliminar activo | ✅ | 🔶 Propias | ❌ |
| Importar activos (Excel/CSV) | ✅ | 🔶 Propias | ❌ |
| Ver listado de activos | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |
| Ver detalle de activo | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |

> 🔶 **Condicional (ABAC):** Restringido a evaluaciones creadas por el usuario o asignadas explícitamente.

### 2.3 Cuestionarios / Plantillas

| Acción | Admin | Operator | Viewer |
|--------|:-----:|:--------:|:------:|
| Crear plantilla de cuestionario | ✅ | ❌ | ❌ |
| Editar plantilla de cuestionario | ✅ | ❌ | ❌ |
| Eliminar plantilla de cuestionario | ✅ | ❌ | ❌ |
| Publicar / despublicar plantilla | ✅ | ❌ | ❌ |
| Gestionar preguntas/secciones/pesos | ✅ | ❌ | ❌ |
| Responder cuestionario (evaluación) | ✅ | 🔶 Propias/Asignadas | ❌ |
| Ver cuestionarios respondidos | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |

### 2.4 Evaluaciones

| Acción | Admin | Operator | Viewer |
|--------|:-----:|:--------:|:------:|
| Crear evaluación | ✅ | ✅ | ❌ |
| Editar evaluación | ✅ | 🔶 Propias | ❌ |
| Eliminar evaluación | ✅ | ❌ | ❌ |
| Asignar activos a evaluación | ✅ | 🔶 Propias | ❌ |
| Asignar evaluación a usuarios | ✅ | ❌ | ❌ |
| Responder cuestionarios | ✅ | 🔶 Propias/Asignadas | ❌ |
| Ver estado de evaluación | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |

### 2.5 Inteligencia Artificial (IA)

| Acción | Admin | Operator | Viewer |
|--------|:-----:|:--------:|:------:|
| Ejecutar análisis IA (riesgos) | ✅ | 🔶 Propias/Asignadas | ❌ |
| Ejecutar análisis IA avanzado | ✅ | 🔶 Propias/Asignadas | ❌ |
| Ver historial de análisis IA | ✅ | 🔶 Propios | 🔶 Compartidas |
| Guardar recomendaciones IA | ✅ | 🔶 Propias/Asignadas | ❌ |
| Aprobar/rechazar recomendaciones IA | ✅ | 🔶 Propias/Asignadas | ❌ |
| Validar IA (canary, variabilidad) | ✅ | ❌ | ❌ |
| Configurar modelo/endpoint IA | ✅ | ❌ | ❌ |

### 2.6 Resultados / Reportes

| Acción | Admin | Operator | Viewer |
|--------|:-----:|:--------:|:------:|
| Ver dashboards globales | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |
| Ver resultados por evaluación | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |
| Ver mapa de riesgos | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |
| Ver matriz de riesgos | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |
| Exportar PDF | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |
| Exportar Excel | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |
| Ver comparativas entre evaluaciones | ✅ | 🔶 Propias/Asignadas | 🔶 Compartidas |

### 2.7 Administración del Sistema

| Acción | Admin | Operator | Viewer |
|--------|:-----:|:--------:|:------:|
| Configuración global (Ollama, modelos, timeouts) | ✅ | ❌ | ❌ |
| CRUD catálogos amenazas MAGERIT | ✅ | ❌ | ❌ |
| CRUD catálogos controles ISO 27002 | ✅ | ❌ | ❌ |
| CRUD criterios de valoración | ✅ | ❌ | ❌ |
| CRUD banco de preguntas | ✅ | ❌ | ❌ |
| Ver auditoría global del sistema | ✅ | ❌ | ❌ |
| Ver logs de autenticación | ✅ | ❌ | ❌ |
| Ver logs propios | ✅ | ✅ | ✅ |
| Backup / restaurar BD | ✅ | ❌ | ❌ |

---

## 3. CONTROL DE ACCESO ABAC (Attribute-Based)

Además del RBAC por rol, se aplica **ABAC** para restringir el alcance de Operators y Viewers:

### 3.1 Atributos de Contexto

```
Atributo               Descripción                                  Aplica a
─────────────────────────────────────────────────────────────────────────────
user.id                ID del usuario autenticado                   Todos
user.role              Rol del usuario (admin/operator/viewer)      Todos
evaluacion.owner_id    ID del usuario que creó la evaluación        Operator
evaluacion.assigned[]  Lista de user IDs asignados                  Operator, Viewer
evaluacion.shared[]    Lista de user IDs con acceso de lectura      Viewer
```

### 3.2 Reglas de Acceso Combinadas

```
REGLA 1: Admin — Acceso Total
  SI user.role == "admin" → PERMITIR toda acción

REGLA 2: Operator — Solo evaluaciones propias o asignadas
  SI user.role == "operator" Y (
    evaluacion.owner_id == user.id 
    O user.id EN evaluacion.assigned[]
  ) → PERMITIR operaciones de escritura

REGLA 3: Viewer — Solo evaluaciones compartidas, solo lectura
  SI user.role == "viewer" Y (
    user.id EN evaluacion.shared[]
    O user.id EN evaluacion.assigned[]
  ) → PERMITIR solo lectura

REGLA 4: Denegación por defecto
  SI ninguna regla anterior aplica → DENEGAR
```

---

## 4. ESTADOS DE CUENTA DE USUARIO

```
┌──────────────┐    Verificar email     ┌──────────────┐
│  PENDIENTE   │ ─────────────────────► │    ACTIVO     │
│ VERIFICACIÓN │                        │               │
└──────────────┘                        └──────┬───────┘
       │                                       │
       │ Expiración (72h)              Admin desactiva
       ▼                               o autoserv.
┌──────────────┐                        │
│  EXPIRADO    │                        ▼
│              │                 ┌──────────────┐
└──────────────┘                 │   INACTIVO   │
                                 │              │
                                 └──────┬───────┘
                                        │
                                 Admin reactiva
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │    ACTIVO     │
                                 └──────────────┘

                                 [Paralelo]
                                 ┌──────────────┐
                                 │  BLOQUEADO   │ ◄── 5 intentos fallidos
                                 │              │ ──► ACTIVO (tras timeout
                                 └──────────────┘     o reset admin)
```

| Estado | Descripción | Puede iniciar sesión | Acciones posibles |
|--------|-------------|:--------------------:|-------------------|
| `pending_verification` | Registro completado, email no verificado | ❌ | Reenviar email de verificación |
| `active` | Cuenta operativa | ✅ | Todas según rol |
| `inactive` | Desactivada por admin o autoservicio | ❌ | Admin puede reactivar |
| `blocked` | Bloqueada por intentos fallidos (brute force) | ❌ | Desbloqueo automático (30 min) o admin |
| `expired` | Verificación de email expirada (72h) | ❌ | Re-registro o admin activa manualmente |

---

## 5. FLUJOS DE AUTENTICACIÓN

### 5.1 Flujo de Registro de Usuario

```
USUARIO                           SISTEMA                         BD
  │                                  │                              │
  ├─── Llenar formulario ──────────► │                              │
  │    (nombre, email, password)     │                              │
  │                                  ├─── Validar datos ──────────► │
  │                                  │    - Email único             │
  │                                  │    - Password cumple política│
  │                                  │    - Campos obligatorios     │
  │                                  │                              │
  │                                  ├─── Hash password ───────────►│
  │                                  │    (bcrypt/argon2id)         │
  │                                  │                              │
  │                                  ├─── Crear usuario ───────────►│
  │                                  │    status=pending_verif.     │
  │                                  │    role=viewer (por defecto) │
  │                                  │                              │
  │                                  ├─── Enviar email verif. ─────►│ (Opcional)
  │                                  │    (token con expiración)    │
  │                                  │                              │
  │ ◄── Mensaje: "Revisa tu email" ──┤                              │
  │                                  │                              │
  │     [Click en link verif.]       │                              │
  ├──────────────────────────────────►├─── Validar token ──────────►│
  │                                  │    status → active           │
  │ ◄── "Cuenta verificada" ─────────┤                              │
  │                                  │                              │
  │     NOTA: Si no hay email        │                              │
  │     el admin activa manualmente  │                              │
```

### 5.2 Flujo de Inicio de Sesión

```
USUARIO                           SISTEMA                         BD
  │                                  │                              │
  ├─── username + password ─────────►│                              │
  │                                  ├─── Buscar usuario ──────────►│
  │                                  │                              │
  │                          ┌───────┤◄── Usuario encontrado ──────┤
  │                          │       │                              │
  │                          │  [NO existe]                         │
  │ ◄── "Credenciales        │       │                              │
  │      inválidas" ─────────┘       │                              │
  │                                  │                              │
  │                          [Existe]│                              │
  │                                  ├─── Verificar status ────────►│
  │                                  │                              │
  │                          [blocked/inactive/pending]             │
  │ ◄── "Cuenta no disponible" ──────┤                              │
  │                                  │                              │
  │                          [active]│                              │
  │                                  ├─── Verificar password ──────►│
  │                                  │    (bcrypt.checkpw)          │
  │                                  │                              │
  │                          [Incorrecto]                           │
  │                                  ├─── Incrementar intentos ────►│
  │                                  │    (≥5 → status=blocked)     │
  │ ◄── "Credenciales inválidas" ────┤                              │
  │                                  │                              │
  │                          [Correcto]                             │
  │                                  ├─── Reset intentos fallidos ─►│
  │                                  ├─── Crear sesión (cookie) ───►│
  │                                  ├─── Log: LOGIN_SUCCESS ──────►│
  │                                  │                              │
  │ ◄── Redirigir a app ────────────┤                              │
  │     (session_state cargado)      │                              │
  │     (cookie firmada emitida)     │                              │
```

### 5.3 Flujo de Recuperación de Contraseña

```
USUARIO                           SISTEMA                         BD
  │                                  │                              │
  ├─── "Olvidé mi contraseña" ──────►│                              │
  │    + email                       │                              │
  │                                  ├─── Buscar por email ────────►│
  │                                  │                              │
  │                          [Existe o no — mismo mensaje]          │
  │ ◄── "Si existe una cuenta, ──────┤                              │
  │      recibirás un email"         │                              │
  │                                  │                              │
  │                          [Si existe]                            │
  │                                  ├─── Generar token reset ─────►│
  │                                  │    (UUID + expiración 1h)    │
  │                                  ├─── Enviar email con link ───►│
  │                                  ├─── Log: RESET_REQUESTED ───►│
  │                                  │                              │
  │     [Click en link reset]        │                              │
  ├──────────────────────────────────►│                              │
  │                                  ├─── Validar token ───────────►│
  │                                  │    (no expirado, no usado)   │
  │                                  │                              │
  │ ◄── Formulario nueva password ───┤                              │
  │                                  │                              │
  ├─── Nueva password ──────────────►│                              │
  │                                  ├─── Validar política ────────►│
  │                                  ├─── Hash nueva password ─────►│
  │                                  ├─── Actualizar BD ───────────►│
  │                                  ├─── Invalidar token ─────────►│
  │                                  ├─── Invalidar sesiones ──────►│
  │                                  ├─── Log: PASSWORD_RESET ─────►│
  │                                  │                              │
  │ ◄── "Contraseña actualizada" ────┤                              │
  │                                  │                              │

  ALTERNATIVA SIN EMAIL (Streamlit local):
  ─────────────────────────────────────────
  El Admin usa el panel de gestión para:
    Admin → Gestión Usuarios → Seleccionar usuario → Reset Password
    Se genera contraseña temporal que el usuario debe cambiar al ingresar.
```

### 5.4 Flujo de Autorización por Acción

```
USUARIO                           MIDDLEWARE AUTH                  SERVICIO
  │                                  │                              │
  ├─── Acción (ej: ejecutar IA) ────►│                              │
  │                                  ├─── ¿Sesión válida? ────────►│
  │                                  │                              │
  │                          [NO]    │                              │
  │ ◄── Redirigir a login ──────────┤                              │
  │                                  │                              │
  │                          [SÍ]    │                              │
  │                                  ├─── Obtener user.role ──────►│
  │                                  ├─── Obtener permiso requerido│
  │                                  │    (ej: can_generate_ia)    │
  │                                  │                              │
  │                                  ├─── RBAC: ¿Rol permite? ───►│
  │                                  │                              │
  │                          [NO]    │                              │
  │ ◄── "Sin permisos" ─────────────┤                              │
  │                                  │                              │
  │                          [SÍ]    │                              │
  │                                  ├─── ABAC: ¿Ámbito válido? ─►│
  │                                  │    (¿Es su evaluación?      │
  │                                  │     ¿Está asignado?)        │
  │                                  │                              │
  │                          [NO]    │                              │
  │ ◄── "No tiene acceso a ─────────┤                              │
  │      este recurso"               │                              │
  │                                  │                              │
  │                          [SÍ]    │                              │
  │                                  ├─── Log: ACCION_EJECUTADA ──►│
  │                                  ├─── Ejecutar servicio ──────►│
  │                                  │                              │
  │ ◄── Resultado ───────────────────┤                              │
```

---

## 6. REGLAS DE AUTORIZACIÓN (PSEUDOREGLAS)

```python
# ══════════════════════════════════════════════════════════════════
# REGLAS DE GESTIÓN DE USUARIOS
# ══════════════════════════════════════════════════════════════════

RULE "Solo Admin puede crear usuarios"
  WHEN action == "user.create"
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Acción reservada para administradores"

RULE "Solo Admin puede asignar roles"
  WHEN action == "user.assign_role"
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Solo un administrador puede cambiar roles"

RULE "Solo Admin puede resetear contraseñas de terceros"
  WHEN action == "user.reset_password" AND target_user != current_user
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Solo un administrador puede resetear contraseñas ajenas"

RULE "Cualquier usuario autenticado puede cambiar su propia contraseña"
  WHEN action == "user.change_own_password" AND target_user == current_user
  THEN ALLOW

RULE "Solo Admin puede activar/desactivar cuentas"
  WHEN action == "user.toggle_status"
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Acción reservada para administradores"

# ══════════════════════════════════════════════════════════════════
# REGLAS DE EVALUACIONES
# ══════════════════════════════════════════════════════════════════

RULE "Operator puede crear evaluaciones"
  WHEN action == "evaluacion.create"
  THEN REQUIRE user.role IN ["admin", "operator"]
  ELSE DENY "Rol sin permisos para crear evaluaciones"

RULE "Operator solo edita evaluaciones propias o asignadas"
  WHEN action == "evaluacion.edit"
  THEN REQUIRE (
    user.role == "admin"
    OR (user.role == "operator" AND (
      evaluacion.owner_id == user.id
      OR user.id IN evaluacion.assigned_users
    ))
  )
  ELSE DENY "No tiene acceso a esta evaluación"

RULE "Solo Admin puede eliminar evaluaciones"
  WHEN action == "evaluacion.delete"
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Solo un administrador puede eliminar evaluaciones"

RULE "Solo Admin puede asignar evaluaciones a usuarios"
  WHEN action == "evaluacion.assign_users"
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Asignación reservada para administradores"

# ══════════════════════════════════════════════════════════════════
# REGLAS DE ACTIVOS
# ══════════════════════════════════════════════════════════════════

RULE "Operator puede CRUD activos en sus evaluaciones"
  WHEN action IN ["activo.create", "activo.edit", "activo.delete", "activo.import"]
  THEN REQUIRE (
    user.role == "admin"
    OR (user.role == "operator" AND evaluacion_del_activo.owner_id == user.id)
    OR (user.role == "operator" AND user.id IN evaluacion_del_activo.assigned_users)
  )
  ELSE DENY "No tiene permisos sobre activos de esta evaluación"

RULE "Viewer puede ver activos de evaluaciones compartidas"
  WHEN action == "activo.view"
  THEN REQUIRE (
    user.role == "admin"
    OR (user.role == "operator" AND tiene_acceso_evaluacion(user, evaluacion))
    OR (user.role == "viewer" AND user.id IN evaluacion.shared_users)
  )
  ELSE DENY "Sin acceso a estos activos"

# ══════════════════════════════════════════════════════════════════
# REGLAS DE IA
# ══════════════════════════════════════════════════════════════════

RULE "Operator puede ejecutar IA solo en evaluaciones asignadas"
  WHEN action IN ["ia.ejecutar_analisis", "ia.ejecutar_avanzado"]
  THEN REQUIRE (
    user.role == "admin"
    OR (user.role == "operator" AND tiene_acceso_evaluacion(user, evaluacion))
  )
  ELSE DENY "No puede ejecutar IA en evaluaciones ajenas"

RULE "Viewer no puede ejecutar IA"
  WHEN action IN ["ia.ejecutar_analisis", "ia.ejecutar_avanzado"]
  AND user.role == "viewer"
  THEN DENY "Rol de consulta no puede ejecutar análisis IA"

RULE "Solo Admin puede validar IA (canary, variabilidad)"
  WHEN action == "ia.validar"
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Validación de IA reservada para administradores"

# ══════════════════════════════════════════════════════════════════
# REGLAS DE CUESTIONARIOS / PLANTILLAS
# ══════════════════════════════════════════════════════════════════

RULE "Solo Admin puede gestionar plantillas maestras"
  WHEN action IN ["plantilla.create", "plantilla.edit", "plantilla.delete", 
                   "plantilla.publish", "plantilla.manage_questions"]
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Gestión de plantillas reservada para administradores"

RULE "Operator puede responder cuestionarios de sus evaluaciones"
  WHEN action == "cuestionario.respond"
  THEN REQUIRE (
    user.role == "admin"
    OR (user.role == "operator" AND tiene_acceso_evaluacion(user, evaluacion))
  )
  ELSE DENY "No puede responder cuestionarios de evaluaciones ajenas"

# ══════════════════════════════════════════════════════════════════
# REGLAS DE REPORTES / EXPORTACIÓN
# ══════════════════════════════════════════════════════════════════

RULE "Viewer puede ver y exportar reportes de evaluaciones compartidas"
  WHEN action IN ["reporte.view", "reporte.export_pdf", "reporte.export_excel"]
  THEN REQUIRE (
    user.role == "admin"
    OR (user.role == "operator" AND tiene_acceso_evaluacion(user, evaluacion))
    OR (user.role == "viewer" AND user.id IN evaluacion.shared_users)
  )
  ELSE DENY "Sin acceso a reportes de esta evaluación"

# ══════════════════════════════════════════════════════════════════
# REGLAS DE ADMINISTRACIÓN / CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════

RULE "Solo Admin puede modificar configuración global"
  WHEN action IN ["config.edit", "catalogo.edit", "criterio.edit", "backup.execute"]
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Configuración del sistema reservada para administradores"

RULE "Solo Admin puede ver auditoría global"
  WHEN action == "audit.view_global"
  THEN REQUIRE user.role == "admin"
  ELSE DENY "Auditoría global reservada para administradores"

RULE "Cualquier usuario puede ver sus propios logs"
  WHEN action == "audit.view_own"
  THEN REQUIRE user.is_authenticated AND audit_log.user_id == user.id
  ELSE DENY "Solo puede ver sus propios registros"
```

---

## 7. MODELO DE DATOS — TABLAS DE AUTENTICACIÓN

### 7.1 Tabla `USERS`

```sql
CREATE TABLE IF NOT EXISTS USERS (
    id              TEXT PRIMARY KEY,           -- UUID
    username        TEXT UNIQUE NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,              -- bcrypt/argon2id
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'viewer',  -- admin/operator/viewer
    status          TEXT NOT NULL DEFAULT 'pending_verification',
    failed_attempts INTEGER DEFAULT 0,
    locked_until    TEXT,                       -- ISO datetime o NULL
    email_verified  INTEGER DEFAULT 0,         -- 0=no, 1=sí
    verification_token TEXT,
    verification_expires TEXT,
    reset_token     TEXT,
    reset_expires   TEXT,
    last_login      TEXT,
    last_password_change TEXT,
    must_change_password INTEGER DEFAULT 0,    -- 1=cambio obligatorio
    created_by      TEXT,                      -- user_id del admin que lo creó
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    
    CHECK (role IN ('admin', 'operator', 'viewer')),
    CHECK (status IN ('active', 'inactive', 'blocked', 'pending_verification', 'expired'))
);
```

### 7.2 Tabla `USER_SESSIONS`

```sql
CREATE TABLE IF NOT EXISTS USER_SESSIONS (
    id              TEXT PRIMARY KEY,           -- UUID
    user_id         TEXT NOT NULL,
    session_token   TEXT UNIQUE NOT NULL,
    ip_address      TEXT,
    user_agent      TEXT,
    created_at      TEXT NOT NULL,
    expires_at      TEXT NOT NULL,
    is_active       INTEGER DEFAULT 1,
    
    FOREIGN KEY (user_id) REFERENCES USERS(id)
);
```

### 7.3 Tabla `EVALUACION_ACCESS` (ABAC)

```sql
CREATE TABLE IF NOT EXISTS EVALUACION_ACCESS (
    id              TEXT PRIMARY KEY,
    evaluacion_id   TEXT NOT NULL,
    user_id         TEXT NOT NULL,
    access_level    TEXT NOT NULL DEFAULT 'viewer',  -- operator/viewer
    assigned_by     TEXT NOT NULL,                   -- user_id del admin
    assigned_at     TEXT NOT NULL,
    
    UNIQUE(evaluacion_id, user_id),
    CHECK (access_level IN ('operator', 'viewer')),
    FOREIGN KEY (evaluacion_id) REFERENCES EVALUACIONES(ID_Evaluacion),
    FOREIGN KEY (user_id) REFERENCES USERS(id),
    FOREIGN KEY (assigned_by) REFERENCES USERS(id)
);
```

### 7.4 Tabla `AUDIT_AUTH_LOG`

```sql
CREATE TABLE IF NOT EXISTS AUDIT_AUTH_LOG (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      TEXT NOT NULL,           -- LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT,
                                             -- PASSWORD_CHANGE, PASSWORD_RESET,
                                             -- ACCOUNT_CREATED, ACCOUNT_DISABLED,
                                             -- ROLE_CHANGED, PERMISSION_DENIED,
                                             -- IA_EXECUTED, EXPORT_GENERATED,
                                             -- EVALUACION_CREATED, ACTIVO_DELETED...
    user_id         TEXT,
    username        TEXT,
    target_user_id  TEXT,                    -- Para acciones sobre otros usuarios
    target_resource TEXT,                    -- ID del recurso afectado
    resource_type   TEXT,                    -- evaluacion/activo/cuestionario/user
    ip_address      TEXT,
    details_json    TEXT,                    -- JSON con detalles adicionales
    result          TEXT DEFAULT 'success',  -- success/denied/error
    created_at      TEXT NOT NULL
);
```

---

## 8. AUDITORÍA — EVENTOS OBLIGATORIOS A REGISTRAR

| Categoría | Evento | Datos mínimos |
|-----------|--------|---------------|
| **Autenticación** | LOGIN_SUCCESS | user_id, IP, timestamp |
| | LOGIN_FAILED | username intentado, IP, timestamp, intentos acumulados |
| | LOGOUT | user_id, duración sesión |
| | PASSWORD_CHANGE | user_id, método (propio/admin) |
| | PASSWORD_RESET_REQUEST | email, IP |
| | PASSWORD_RESET_COMPLETE | user_id |
| | ACCOUNT_LOCKED | user_id, motivo, intentos |
| **Usuarios** | USER_CREATED | user_id nuevo, rol, creado_por |
| | USER_UPDATED | user_id, campos modificados |
| | USER_ROLE_CHANGED | user_id, rol anterior, rol nuevo, cambiado_por |
| | USER_STATUS_CHANGED | user_id, status anterior, status nuevo |
| **Evaluaciones** | EVALUACION_CREATED | eval_id, owner_id |
| | EVALUACION_DELETED | eval_id, eliminado_por |
| | EVALUACION_ASSIGNED | eval_id, user_id asignado, access_level |
| **Activos** | ACTIVO_CREATED | activo_id, eval_id |
| | ACTIVO_DELETED | activo_id, eval_id, eliminado_por |
| | ACTIVO_IMPORT | eval_id, cantidad importada |
| **IA** | IA_ANALYSIS_EXECUTED | eval_id, activo_id, modelo, latencia |
| | IA_RECOMMENDATION_SAVED | eval_id, activo_id |
| **Reportes** | REPORT_EXPORTED | eval_id, formato (PDF/Excel), user_id |
| **Sistema** | CONFIG_CHANGED | parámetro, valor anterior, valor nuevo |
| | CATALOG_MODIFIED | catálogo, operación, registros afectados |
| **Autorización** | PERMISSION_DENIED | user_id, acción intentada, recurso |

---

## 9. RECOMENDACIONES DE SEGURIDAD

### 9.1 Hashing de Contraseñas

| Aspecto | Recomendación |
|---------|---------------|
| **Algoritmo primario** | **Argon2id** (ganador de Password Hashing Competition) |
| **Alternativa aceptable** | bcrypt (ya en uso en el proyecto, mínimo 12 rounds) |
| **Parámetros Argon2id** | memory=65536 KB, iterations=3, parallelism=4 |
| **Nunca usar** | MD5, SHA-1, SHA-256 sin sal, texto plano |

```python
# Ejemplo con argon2-cffi (recomendado)
from argon2 import PasswordHasher
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
hash = ph.hash("password")
ph.verify(hash, "password")  # True o excepción

# Alternativa con bcrypt (actual)
import bcrypt
hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt(rounds=12))
bcrypt.checkpw("password".encode(), hash)  # True/False
```

### 9.2 Sesiones vs JWT

| Criterio | Cookie/Sesión (Recomendado para TITA) | JWT |
|----------|:--------------------------------------:|:---:|
| **Complejidad** | Baja (streamlit-authenticator lo maneja) | Media-Alta |
| **Revocación** | Fácil (borrar de BD/session_state) | Difícil (requiere blacklist) |
| **Escalabilidad** | Suficiente (app monolítica Streamlit) | Necesario en microservicios |
| **Seguridad** | Cookie firmada + httpOnly + secure | Vulnerable si se almacena en localStorage |
| **Recomendación** | **Usar para TITA** | No necesario en esta arquitectura |

**Configuración de cookie recomendada:**

```python
COOKIE_CONFIG = {
    "name": "tita_session",
    "key": "CAMBIAR_POR_SECRET_KEY_SEGURA_32_CHARS",  # Generar con secrets.token_hex(32)
    "expiry_days": 1,       # Reducido de 30 a 1 día
    "httponly": True,        # Previene acceso desde JavaScript
    "secure": True,          # Solo HTTPS (desactivar en desarrollo local)
    "samesite": "Lax"        # Protección CSRF básica
}
```

### 9.3 Política de Contraseñas

```python
PASSWORD_POLICY = {
    "min_length": 10,
    "max_length": 128,
    "require_uppercase": True,    # Al menos 1 mayúscula
    "require_lowercase": True,    # Al menos 1 minúscula
    "require_digit": True,        # Al menos 1 número
    "require_special": True,      # Al menos 1 carácter especial
    "disallow_username": True,    # No puede contener el username
    "disallow_common": True,      # Revisar contra lista de passwords comunes
    "max_age_days": 90,           # Expiración cada 90 días (opcional)
    "history_count": 5            # No repetir últimas 5 contraseñas
}
```

### 9.4 Protección contra Brute Force

```python
BRUTE_FORCE_CONFIG = {
    "max_attempts": 5,                  # Intentos antes de bloqueo
    "lockout_duration_minutes": 30,     # Duración del bloqueo
    "progressive_delay": True,          # Delay incremental entre intentos
    "delay_base_seconds": 1,            # 1s, 2s, 4s, 8s...
    "rate_limit_per_minute": 10,        # Max requests por IP por minuto
    "notify_admin_on_lockout": True,    # Alertar al admin
    "log_all_failed_attempts": True     # Registrar cada intento fallido
}
```

### 9.5 Protecciones Adicionales (Web)

| Protección | Aplica a TITA | Implementación |
|------------|:-------------:|----------------|
| **CSRF** | Parcial | Streamlit maneja internamente; la cookie SameSite=Lax mitiga |
| **XSS** | Sí | Evitar `unsafe_allow_html=True` con datos de usuario; sanitizar inputs |
| **CORS** | No aplica | App monolítica, no hay API REST cross-origin |
| **Rate Limiting** | Sí | Implementar en capa de login (contador en BD) |
| **Input Validation** | Sí | Validar todos los inputs: SQL injection, path traversal |
| **Session Fixation** | Sí | Regenerar session ID tras login exitoso |
| **Secure Headers** | Parcial | Streamlit los gestiona; agregar CSP si se despliega con proxy |

### 9.6 Registro y Monitoreo de Eventos

```python
# Eventos que requieren ALERTA INMEDIATA
ALERT_EVENTS = [
    "ACCOUNT_LOCKED",           # Posible brute force
    "MULTIPLE_LOGIN_FAILED",    # 3+ fallos en 5 min
    "ROLE_CHANGED",             # Cambio de privilegios
    "ADMIN_CREATED",            # Nuevo admin → revisar
    "BULK_DELETE",              # Eliminación masiva
    "CONFIG_CHANGED",           # Cambio de configuración
    "PERMISSION_DENIED_REPEAT"  # Intentos repetidos de acceso no autorizado
]

# Retención de logs
LOG_RETENTION = {
    "auth_logs": "365 days",      # 1 año
    "action_logs": "180 days",    # 6 meses
    "system_logs": "90 days"      # 3 meses
}
```

---

## 10. CHECKLIST DE IMPLEMENTACIÓN

### 10.1 Backend — Base de Datos y Servicios

```
PRIORIDAD ALTA (Semana 1-2):
──────────────────────────────────────────────────────────────────
☐ 1.  Crear tabla USERS en database_service.py
☐ 2.  Crear tabla USER_SESSIONS en database_service.py
☐ 3.  Crear tabla EVALUACION_ACCESS en database_service.py
☐ 4.  Crear tabla AUDIT_AUTH_LOG en database_service.py
☐ 5.  Crear services/auth_service.py:
      ☐ register_user(username, email, password, full_name)
      ☐ authenticate_user(username, password) → session_token
      ☐ logout_user(session_token)
      ☐ change_password(user_id, old_password, new_password)
      ☐ reset_password_request(email) → token
      ☐ reset_password_confirm(token, new_password)
      ☐ validate_password_policy(password) → (bool, errors)
      ☐ hash_password(password) → hash
      ☐ verify_password(password, hash) → bool
☐ 6.  Crear services/user_management_service.py:
      ☐ create_user(admin_id, user_data) → user_id
      ☐ update_user(admin_id, user_id, updates)
      ☐ toggle_user_status(admin_id, user_id, new_status)
      ☐ assign_role(admin_id, user_id, new_role)
      ☐ admin_reset_password(admin_id, user_id) → temp_password
      ☐ list_users(filters) → List[User]
      ☐ get_user(user_id) → User
☐ 7.  Crear services/authorization_service.py:
      ☐ check_permission(user_id, action, resource_id) → bool
      ☐ check_evaluacion_access(user_id, evaluacion_id) → access_level
      ☐ assign_evaluacion_access(admin_id, user_id, eval_id, level)
      ☐ revoke_evaluacion_access(admin_id, user_id, eval_id)
      ☐ get_accessible_evaluaciones(user_id) → List[str]

PRIORIDAD ALTA (Semana 2-3):
──────────────────────────────────────────────────────────────────
☐ 8.  Actualizar config/auth_config.py:
      ☐ Reemplazar DEFAULT_USERS hardcodeados por consultas a BD
      ☐ Actualizar ROLE_PERMISSIONS con la matriz completa
      ☐ Agregar PASSWORD_POLICY, BRUTE_FORCE_CONFIG, COOKIE_CONFIG
☐ 9.  Actualizar utils/auth_helpers.py:
      ☐ require_permission() → usar authorization_service
      ☐ require_evaluacion_access(eval_id) → decorador ABAC
      ☐ get_current_user() → consultar BD
      ☐ audit_action(event_type, details) → registrar en AUDIT_AUTH_LOG
☐ 10. Crear services/audit_auth_service.py:
      ☐ log_event(event_type, user_id, details, result)
      ☐ get_auth_logs(filters, pagination)
      ☐ get_user_activity(user_id, date_range)
      ☐ get_failed_logins(time_window)
      ☐ check_brute_force(username_or_ip)
☐ 11. Agregar columna owner_id a tabla EVALUACIONES:
      ☐ ALTER TABLE EVALUACIONES ADD COLUMN owner_id TEXT
      ☐ Migrar evaluaciones existentes (asignar a admin)
```

### 10.2 Backend — Integración con Servicios Existentes

```
PRIORIDAD MEDIA (Semana 3-4):
──────────────────────────────────────────────────────────────────
☐ 12. Actualizar evaluacion_service.py:
      ☐ crear_evaluacion() → incluir owner_id del usuario actual
      ☐ obtener_evaluaciones() → filtrar por acceso del usuario
      ☐ eliminar_evaluacion() → verificar rol admin
☐ 13. Actualizar activo_service.py:
      ☐ crear_activo() → verificar acceso a la evaluación
      ☐ editar_activo() → verificar acceso a la evaluación
      ☐ eliminar_activo() → verificar permisos
☐ 14. Actualizar cuestionario_service.py:
      ☐ generar_cuestionario() → verificar acceso
      ☐ guardar_respuestas() → verificar acceso y registrar auditoría
☐ 15. Actualizar ollama_magerit_service.py:
      ☐ analizar_activo() → verificar permiso can_generate_ia + acceso eval
☐ 16. Actualizar export_service.py:
      ☐ exportar_pdf/excel() → verificar acceso + registrar auditoría
☐ 17. Actualizar auditoria_service.py:
      ☐ Integrar con AUDIT_AUTH_LOG
      ☐ Filtrar por usuario actual (operator/viewer solo ven propios)
```

### 10.3 Frontend — UI de Autenticación

```
PRIORIDAD ALTA (Semana 2-3):
──────────────────────────────────────────────────────────────────
☐ 18. Crear components/login_ui.py:
      ☐ Formulario de login (username + password)
      ☐ Link "Olvidé mi contraseña"
      ☐ Link "Registrarse" (si se permite auto-registro)
      ☐ Mensajes de error genéricos (no revelar si usuario existe)
☐ 19. Crear components/register_ui.py:
      ☐ Formulario de registro (nombre, email, username, password)
      ☐ Validación de política de contraseña en tiempo real
      ☐ Mensaje de confirmación / pendiente verificación
☐ 20. Crear components/profile_ui.py:
      ☐ Ver/editar nombre, email
      ☐ Cambiar contraseña (pide contraseña actual)
      ☐ Ver historial de sesiones propias
☐ 21. Crear components/user_management_ui.py (solo Admin):
      ☐ Tabla de usuarios con filtros
      ☐ Crear usuario nuevo  
      ☐ Editar usuario (nombre, email, rol, status)
      ☐ Activar/desactivar cuenta
      ☐ Reset contraseña de terceros
      ☐ Asignar evaluaciones a usuarios
```

### 10.4 Frontend — Integración con App Principal

```
PRIORIDAD ALTA (Semana 3-4):
──────────────────────────────────────────────────────────────────
☐ 22. Modificar app_final.py:
      ☐ Agregar gate de login al inicio (antes de renderizar tabs)
      ☐ Mostrar badge de usuario en sidebar
      ☐ Filtrar tabs visibles según rol
      ☐ Agregar tab "👤 Mi Perfil" para todos los roles
      ☐ Agregar tab "👥 Gestión Usuarios" solo para Admin
      ☐ Inyectar user_id en todas las operaciones
☐ 23. Modificar app_matriz.py:
      ☐ Agregar gate de login
      ☐ Filtrar evaluaciones por acceso del usuario
      ☐ Deshabilitar acciones según permisos del rol
☐ 24. Implementar filtro global de evaluaciones:
      ☐ Admin → ve todas
      ☐ Operator → ve propias + asignadas
      ☐ Viewer → ve compartidas (solo lectura)
☐ 25. Agregar protección en cada acción sensible:
      ☐ Envolver botones con check_permission()
      ☐ Verificar acceso antes de ejecutar operaciones
      ☐ Registrar en auditoría tras cada acción

PRIORIDAD BAJA (Semana 4-5):
──────────────────────────────────────────────────────────────────
☐ 26. Panel de auditoría mejorado (solo Admin):
      ☐ Filtros por tipo de evento, usuario, fecha
      ☐ Exportar logs a CSV
      ☐ Dashboard de actividad (logins, acciones por día)
☐ 27. Implementar 2FA (opcional):
      ☐ TOTP (Google Authenticator / Authy)
      ☐ Tabla USERS: agregar totp_secret, totp_enabled
      ☐ UI de configuración en perfil del usuario
☐ 28. Implementar verificación de email (opcional):
      ☐ Integrar servicio de email (SMTP)
      ☐ Template de email de verificación
      ☐ Template de email de reset de contraseña
```

### 10.5 Testing

```
☐ 29. Tests unitarios:
      ☐ test_auth_service.py (login, registro, reset, política passwords)
      ☐ test_authorization_service.py (RBAC + ABAC por evaluación)
      ☐ test_user_management.py (CRUD usuarios, cambio roles)
☐ 30. Tests de integración:
      ☐ test_login_flow.py (flujo completo login → acción → logout)
      ☐ test_permission_enforcement.py (operator no puede borrar evals)
      ☐ test_brute_force.py (bloqueo tras 5 intentos)
☐ 31. Tests de seguridad:
      ☐ Verificar que passwords nunca se loguean en texto plano
      ☐ Verificar que tokens de reset expiran correctamente
      ☐ Verificar que sesiones se invalidan tras cambio de contraseña
```

---

## 11. RESUMEN DE PERMISOS — VISTA RÁPIDA

```
╔══════════════════════════════════════════════════════════════════╗
║                    ADMIN          OPERATOR        VIEWER        ║
╠══════════════════════════════════════════════════════════════════╣
║ Gestión usuarios    ✅ CRUD        ❌              ❌           ║
║ Config. global      ✅             ❌              ❌           ║
║ Catálogos maestros  ✅ CRUD        ❌ Solo ver     ❌           ║
║ Plantillas cuest.   ✅ CRUD        ❌              ❌           ║
║ Crear evaluación    ✅             ✅              ❌           ║
║ Editar evaluación   ✅ Todas       🔶 Propias      ❌           ║
║ Eliminar evaluación ✅             ❌              ❌           ║
║ Asignar evaluación  ✅             ❌              ❌           ║
║ CRUD activos        ✅ Todos       🔶 Sus evals    ❌           ║
║ Responder cuest.    ✅             🔶 Sus evals    ❌           ║
║ Ejecutar IA         ✅             🔶 Sus evals    ❌           ║
║ Ver dashboards      ✅ Todos       🔶 Sus evals    🔶 Compartidas║
║ Exportar reportes   ✅ Todos       🔶 Sus evals    🔶 Compartidas║
║ Auditoría global    ✅             ❌              ❌           ║
║ Auditoría propia    ✅             ✅              ✅           ║
║ Perfil propio       ✅             ✅              ✅           ║
║ Cambiar password    ✅             ✅              ✅           ║
╚══════════════════════════════════════════════════════════════════╝

Leyenda:  ✅ = Permitido   ❌ = Denegado   🔶 = Condicional (ABAC)
```

---

## 12. DIAGRAMA DE ARQUITECTURA DE SEGURIDAD

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                 │
│                     (Browser/Streamlit)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE AUTENTICACIÓN                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Login Form  │  │  Register    │  │  Password Recovery   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         ▼                 ▼                      ▼              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              auth_service.py                             │   │
│  │  • authenticate_user()    • register_user()              │   │
│  │  • validate_password()    • reset_password()             │   │
│  │  • check_brute_force()    • hash_password()              │   │
│  └──────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE AUTORIZACIÓN                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           authorization_service.py                       │   │
│  │  ┌─────────────┐        ┌──────────────┐                │   │
│  │  │    RBAC     │        │     ABAC     │                │   │
│  │  │ check_role()│        │ check_scope()│                │   │
│  │  │  admin?     │───────►│  owner?      │                │   │
│  │  │  operator?  │        │  assigned?   │                │   │
│  │  │  viewer?    │        │  shared?     │                │   │
│  │  └─────────────┘        └──────────────┘                │   │
│  └──────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE SERVICIOS                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Activos  │ │ Cuestion.│ │ Análisis │ │ Reportes/Export  │   │
│  │ Service  │ │ Service  │ │ IA Serv. │ │ Service          │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘   │
│       │            │            │                 │             │
│       └────────────┴────────────┴─────────────────┘             │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              audit_auth_service.py                       │   │
│  │  • log_event()  • get_logs()  • check_alerts()           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BASE DE DATOS (SQLite)                       │
│  ┌────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │ USERS  │ │USER_SESSIONS│ │EVALUACION_   │ │AUDIT_AUTH_  │  │
│  │        │ │             │ │ACCESS        │ │LOG          │  │
│  └────────┘ └─────────────┘ └──────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. PRIORIDAD DE IMPLEMENTACIÓN

| Fase | Componentes | Esfuerzo | Impacto |
|------|-------------|:--------:|:-------:|
| **Fase 1** | Tablas BD (USERS, SESSIONS, ACCESS, AUDIT_AUTH), auth_service.py, login UI | 2 semanas | Crítico |
| **Fase 2** | authorization_service.py (RBAC+ABAC), user_management, integración app_final | 2 semanas | Crítico |
| **Fase 3** | Integración servicios existentes, filtro evaluaciones, auditoría | 1-2 semanas | Alto |
| **Fase 4** | Tests, 2FA, verificación email, panel auditoría avanzado | 1-2 semanas | Medio |

**Tiempo total estimado:** 6-8 semanas con un desarrollador.

---

*Documento generado como especificación de requerimientos. Cada sección es implementable de forma incremental siguiendo el checklist de la Sección 10.*

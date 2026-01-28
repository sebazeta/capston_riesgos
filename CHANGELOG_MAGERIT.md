# CAMBIOS IMPLEMENTADOS - Alineación MAGERIT Marco Teórico
## Fecha: Enero 2025

---

## ACTUALIZACIÓN: UI de Degradación (Enero 2025)

### Nueva Pestaña: ⚙️ Degradación

Se agregó una nueva pestaña en la aplicación para gestionar manualmente la degradación por (activo, amenaza).

#### Ubicación en el Flujo:
```
Evaluaciones → Activos → Cuestionarios → Evaluación IA → ⚙️ DEGRADACIÓN → Dashboard → Madurez
```

#### Funcionalidades:

| Funcionalidad | Descripción |
|--------------|-------------|
| **Selector de Activo** | Dropdown para elegir activo de la evaluación actual |
| **Tabla de Amenazas** | Lista expandible de amenazas con estado de degradación |
| **Sliders de Degradación** | Controles deslizantes para Deg_D, Deg_I, Deg_C con niveles descriptivos |
| **Preview en Tiempo Real** | Muestra cálculo de Impacto y Riesgo antes de guardar |
| **Guardar Manual** | Guarda degradación con fuente="manual" |
| **Sugerir IA** | Genera sugerencia basada en tipo de amenaza/activo |
| **Sugerir TODAS IA** | Acción masiva para pendientes |
| **Validar Trazabilidad** | Verifica cadena completa activo→riesgo→amenaza→control |

#### Estados de Degradación:

| Estado | Icono | Descripción |
|--------|-------|-------------|
| Pendiente | 🔴 | Sin degradación → Riesgo NO calculado |
| Manual | 🟢 | Degradación ingresada por usuario |
| IA | 🔵 | Degradación sugerida por sistema |

#### Niveles de Degradación (Dropdown):

| Nivel | Valor Float |
|-------|-------------|
| Muy Bajo | 0.1 |
| Bajo | 0.3 |
| Medio | 0.5 |
| Alto | 0.7 |
| Muy Alto | 0.9 |
| Total | 1.0 |

#### Archivos Creados:

| Archivo | Descripción |
|---------|-------------|
| `components/degradacion_ui.py` | Componente UI completo |

#### Archivos Modificados:

| Archivo | Cambio |
|---------|--------|
| `app_final.py` | Import + nueva tab `tab_deg` |

---

## 1. MIGRACIÓN DE BASE DE DATOS

### 1.1 Nueva Tabla: DEGRADACION_AMENAZAS
```sql
CREATE TABLE DEGRADACION_AMENAZAS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT NOT NULL,
    ID_Activo TEXT NOT NULL,
    Codigo_Amenaza TEXT NOT NULL,
    Degradacion_D REAL DEFAULT 0.5,  -- [0.0 - 1.0]
    Degradacion_I REAL DEFAULT 0.5,  -- [0.0 - 1.0]
    Degradacion_C REAL DEFAULT 0.5,  -- [0.0 - 1.0]
    Justificacion TEXT,
    Fuente TEXT DEFAULT 'manual',     -- "manual" o "IA"
    Fecha_Registro TEXT,
    UNIQUE(ID_Evaluacion, ID_Activo, Codigo_Amenaza)
);
```

### 1.2 Campos Nuevos en EVALUACIONES
| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `Limite_Riesgo` | REAL | 7.0 | Límite de riesgo aceptable por evaluación |
| `Factor_Objetivo` | REAL | 0.5 | Factor para calcular riesgo objetivo |

### 1.3 Campos Nuevos en RESULTADOS_MAGERIT
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `Criticidad` | INTEGER | MAX(D, I, C) del activo |
| `Riesgo_Promedio` | REAL | Promedio de riesgos de todas las amenazas |
| `Riesgo_Maximo` | REAL | Máximo de riesgos de todas las amenazas |
| `Riesgo_Objetivo` | REAL | Riesgo_Actual × Factor_Objetivo |
| `Supera_Limite` | INTEGER | 1 si Riesgo > Límite, 0 si no |

### 1.4 Nueva Tabla: VULNERABILIDADES
```sql
CREATE TABLE VULNERABILIDADES (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT NOT NULL,
    ID_Activo TEXT NOT NULL,
    Codigo_Vulnerabilidad TEXT,
    Descripcion TEXT NOT NULL,
    Amenazas_Asociadas TEXT,
    Fecha_Identificacion TEXT,
    Fuente TEXT DEFAULT 'manual'
);
```

---

## 2. NUEVO MÓDULO: degradacion_service.py

### 2.1 Ubicación
`services/degradacion_service.py`

### 2.2 Funciones Principales

#### CRUD Degradación
| Función | Descripción |
|---------|-------------|
| `obtener_degradacion(eval_id, activo_id, codigo_amenaza)` | Obtiene degradación específica |
| `guardar_degradacion(deg: DegradacionAmenaza)` | Guarda o actualiza degradación |
| `obtener_degradaciones_activo(eval_id, activo_id)` | Lista todas las degradaciones de un activo |
| `eliminar_degradacion(eval_id, activo_id, codigo_amenaza)` | Elimina una degradación |

#### Cálculos MAGERIT
| Función | Fórmula |
|---------|---------|
| `calcular_impacto_con_degradacion(criticidad, deg)` | CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C) |
| `calcular_riesgo_activo_dual(riesgos)` | Retorna `{promedio, maximo}` |
| `calcular_riesgo_objetivo(riesgo, factor)` | Riesgo × Factor |
| `supera_limite(riesgo, limite)` | Riesgo > Límite |

#### Configuración
| Función | Descripción |
|---------|-------------|
| `obtener_limite_evaluacion(eval_id)` | Obtiene límite configurado (default 7.0) |
| `actualizar_limite_evaluacion(eval_id, limite)` | Actualiza límite |
| `obtener_factor_objetivo(eval_id)` | Obtiene factor objetivo (default 0.5) |

#### Sugerencia IA
| Función | Descripción |
|---------|-------------|
| `sugerir_degradacion_ia(tipo_activo, codigo_amenaza, tipo_amenaza)` | Genera degradación sugerida |

#### Validación
| Función | Descripción |
|---------|-------------|
| `validar_trazabilidad_completa(eval_id, activo_id)` | Valida cadena completa |

---

## 3. MODIFICACIONES EN magerit_engine.py

### 3.1 Imports Agregados
```python
from services.degradacion_service import (
    obtener_degradacion, obtener_degradaciones_activo, guardar_degradacion,
    sugerir_degradacion_ia, DegradacionAmenaza,
    calcular_impacto_con_degradacion, calcular_riesgo_activo_dual,
    calcular_riesgo_objetivo, supera_limite, obtener_limite_evaluacion
)
```

### 3.2 Cambios en evaluar_activo_magerit()

#### ANTES (Incorrecto):
```python
# Impacto directo de la dimensión
if dimension == "D":
    impacto_amenaza = impacto.disponibilidad
elif dimension == "I":
    impacto_amenaza = impacto.integridad
# ...
riesgo_inherente = probabilidad_ia * impacto_amenaza
```

#### AHORA (Correcto - Marco Teórico):
```python
# Calcular CRITICIDAD
criticidad_activo = impacto.impacto_global  # MAX(D, I, C)

# Obtener o sugerir DEGRADACIÓN
degradacion = obtener_degradacion(eval_id, activo_id, codigo)
if degradacion is None:
    degradacion = sugerir_degradacion_ia(tipo_activo, codigo, tipo_amenaza)
    guardar_degradacion(degradacion)

# FÓRMULA CORRECTA: IMPACTO = CRITICIDAD × MAX(Deg)
impacto_amenaza = criticidad_activo * degradacion.degradacion_maxima

# RIESGO = FRECUENCIA × IMPACTO
riesgo_inherente = probabilidad_ia * impacto_amenaza
```

### 3.3 Cambios en Agregación de Riesgos

#### ANTES:
```python
riesgo_inherente_global = max(riesgos_inherentes)
riesgo_residual_global = max(riesgos_residuales)
```

#### AHORA:
```python
# Ambas agregaciones disponibles
riesgos_inh = calcular_riesgo_activo_dual(riesgos_inherentes)
riesgos_res = calcular_riesgo_activo_dual(riesgos_residuales)

riesgo_inherente_global = riesgos_inh["promedio"]  # Usar promedio por defecto
riesgo_inherente_maximo = riesgos_inh["maximo"]    # También disponible

# Calcular objetivo y límite
riesgo_objetivo = calcular_riesgo_objetivo(riesgo_residual_global, 0.5)
sobre_limite = supera_limite(riesgo_residual_global, limite)
```

### 3.4 Cambios en guardar_resultado_magerit()

Ahora guarda los campos adicionales:
- `Criticidad`
- `Riesgo_Promedio`
- `Riesgo_Maximo`
- `Riesgo_Objetivo`
- `Supera_Limite`

---

## 4. FÓRMULAS IMPLEMENTADAS

### 4.1 Según Marco Teórico MAGERIT

| Fórmula | Implementación |
|---------|----------------|
| CRITICIDAD | `MAX(D, I, C)` |
| MAX_DEGRADACIÓN | `MAX(Deg_D, Deg_I, Deg_C)` |
| IMPACTO | `CRITICIDAD × MAX_DEGRADACIÓN` |
| RIESGO_AMENAZA | `FRECUENCIA × IMPACTO` |
| RIESGO_ACTIVO_PROMEDIO | `PROMEDIO(riesgos_amenazas)` |
| RIESGO_ACTIVO_MÁXIMO | `MAX(riesgos_amenazas)` |
| RIESGO_OBJETIVO | `RIESGO_RESIDUAL × 0.5` (configurable) |
| SUPERA_LÍMITE | `RIESGO > 7.0` (configurable) |

### 4.2 Ejemplo de Cálculo

```
Activo: Servidor Principal
Valoración DIC: D=3, I=5, C=4

CRITICIDAD = MAX(3, 5, 4) = 5

Amenaza: A.24 - Ataque DoS
Degradación: Deg_D=0.8, Deg_I=0.3, Deg_C=0.1
Frecuencia: 3

MAX_DEGRADACIÓN = MAX(0.8, 0.3, 0.1) = 0.8
IMPACTO = 5 × 0.8 = 4.0
RIESGO_INHERENTE = 3 × 4.0 = 12.0

Nivel: ALTO (≥12)
```

---

## 5. FLUJO DE DEGRADACIÓN

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DE DEGRADACIÓN                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Al identificar amenaza para un activo:                  │
│     ┌──────────────────────────────────────┐                │
│     │ ¿Existe degradación manual guardada? │                │
│     └──────────────────────────────────────┘                │
│              │                    │                          │
│              SÍ                   NO                         │
│              │                    │                          │
│              ▼                    ▼                          │
│     ┌────────────────┐   ┌─────────────────┐                │
│     │ Usar valores   │   │ Generar         │                │
│     │ guardados      │   │ sugerencia IA   │                │
│     │ Fuente=manual  │   │ Fuente=IA       │                │
│     └────────────────┘   └─────────────────┘                │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │ Guardar en      │                │
│                          │ DEGRADACION_    │                │
│                          │ AMENAZAS        │                │
│                          └─────────────────┘                │
│                                                              │
│  2. Usuario puede editar en cualquier momento:              │
│     - Ver sugerencia IA                                     │
│     - Modificar valores Deg_D, Deg_I, Deg_C                │
│     - Guardar como manual                                   │
│                                                              │
│  3. Recálculo automático de riesgo al guardar               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. TRAZABILIDAD COMPLETA

```
ACTIVO
  │
  ├── Valoración DIC (D, I, C)
  │     └── CRITICIDAD = MAX(D, I, C)
  │
  ├── AMENAZAS (varias por activo)
  │     │
  │     ├── Código (del catálogo MAGERIT)
  │     ├── Frecuencia (1-5)
  │     │
  │     └── DEGRADACIÓN (por amenaza)
  │           ├── Deg_D [0.0-1.0]
  │           ├── Deg_I [0.0-1.0]
  │           ├── Deg_C [0.0-1.0]
  │           ├── Fuente (IA/manual)
  │           │
  │           └── IMPACTO = CRITICIDAD × MAX(Deg)
  │                 │
  │                 └── RIESGO_INHERENTE = Frecuencia × Impacto
  │                       │
  │                       ├── CONTROLES_EXISTENTES
  │                       │     └── Efectividad
  │                       │
  │                       └── RIESGO_RESIDUAL
  │
  └── RIESGO_ACTIVO
        ├── Promedio (de todas las amenazas)
        ├── Máximo (peor caso)
        ├── Objetivo (Residual × 0.5)
        └── Supera_Limite (> 7.0)
```

---

## 7. ARCHIVOS MODIFICADOS/CREADOS

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `migrate_magerit_v2.py` | Nuevo | Script de migración de BD |
| `services/degradacion_service.py` | Nuevo | Módulo de degradación |
| `services/magerit_engine.py` | Modificado | Motor con fórmulas correctas |
| `verificar_magerit_v2.py` | Nuevo | Script de verificación |
| `CHANGELOG_MAGERIT.md` | Nuevo | Esta documentación |

---

## 8. PRÓXIMOS PASOS SUGERIDOS

1. **UI para Degradación**: Crear interfaz en Streamlit para:
   - Ver/editar degradación por amenaza
   - Comparar sugerencia IA vs valores actuales
   
2. **Configuración de Límite**: Agregar en panel de evaluación:
   - Configurar Limite_Riesgo por evaluación
   - Configurar Factor_Objetivo
   
3. **Reportes**: Actualizar reportes para mostrar:
   - Criticidad del activo
   - Degradación por amenaza
   - Ambas métricas (promedio y máximo)
   - Indicador de supera límite
   
4. **Re-evaluación**: Recalcular riesgos de evaluaciones existentes con nuevas fórmulas

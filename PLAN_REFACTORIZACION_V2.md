# PLAN DE REFACTORIZACIÓN INTEGRAL - TITA MAGERIT
## Versión 2.0 - Alineación Completa con Modelo MAGERIT

> **Estado:** ✅ IMPLEMENTADO (27-Enero-2026)

---

## 📊 RESUMEN DE IMPLEMENTACIÓN

### FASE 1: Modelo de Datos ✅ COMPLETADA
- 5 nuevas tablas creadas (VULNERABILIDADES_ACTIVO, HISTORIAL_EVALUACIONES, TRATAMIENTO_RIESGOS, AUDITORIA_CAMBIOS, CONFIGURACION_EVALUACION)
- 10 nuevas columnas en INVENTARIO_ACTIVOS
- Índices de rendimiento creados

### FASE 2: Servicios ✅ COMPLETADA
- `vulnerabilidad_service.py` - CRUD completo + sugerencias IA heurísticas
- `tratamiento_service.py` - CRUD + sugerencias automáticas por nivel de riesgo
- `comparativa_service.py` - Comparación entre evaluaciones con deltas
- `auditoria_service.py` - Trazabilidad completa de cambios

### FASE 3: UI ✅ COMPLETADA
- `vulnerabilidades_ui.py` - Tab de gestión de vulnerabilidades
- `tratamiento_ui.py` - Tab de tratamiento de riesgos (Mitigar/Aceptar/Transferir/Evitar)
- `comparativa_ui.py` - Tab de comparativas mejorado con tendencias
- `auditoria_ui.py` - Tab de auditoría y trazabilidad

### FASE 4: Integración ✅ COMPLETADA
- 14 tabs en app_final.py
- Nuevos tabs: 🔓 Vulnerabilidades, 🛡️ Tratamiento, 📊 Comparativas, 📋 Auditoría

---

## 1. DIAGNÓSTICO ACTUAL

### 1.1 Estado de la Base de Datos (SQLite)
| Elemento | Estado | Registros |
|----------|--------|-----------|
| EVALUACIONES | ✅ Existe | 2 |
| INVENTARIO_ACTIVOS | ✅ Existe | 144 |
| CATALOGO_AMENAZAS_MAGERIT | ✅ Existe | 52 |
| CATALOGO_CONTROLES_ISO27002 | ✅ Existe | 93 |
| RESULTADOS_MAGERIT | ✅ Existe | 144 |
| DEGRADACION_AMENAZAS | ✅ Creada | 0 (nueva) |
| VULNERABILIDADES | ✅ Creada | 0 (nueva) |
| CRITERIOS_* | ✅ Existen | 5 cada uno |

### 1.2 Servicios Existentes (17 archivos)
```
services/
├── database_service.py      ✅ Core SQLite
├── magerit_engine.py        ⚠️ Parcialmente alineado
├── degradacion_service.py   ✅ Nuevo (Marco Teórico)
├── ollama_service.py        ✅ IA Local
├── ollama_magerit_service.py ✅ IA MAGERIT
├── evaluacion_service.py    ✅ CRUD Evaluaciones
├── activo_service.py        ✅ CRUD Activos
├── cuestionario_service.py  ✅ Cuestionarios DIC
└── ... (otros)
```

### 1.3 Brechas Identificadas

| Brecha | Descripción | Prioridad |
|--------|-------------|-----------|
| GAP-01 | Activos sin atributos extendidos (host, ubicación, etc.) | ALTA |
| GAP-02 | Vulnerabilidades sin poblar ni vincular | ALTA |
| GAP-03 | Degradación creada pero no integrada en flujo UI | MEDIA |
| GAP-04 | Falta validación de dependencias VM → Host | MEDIA |
| GAP-05 | Carga masiva no ajustada a modelo extendido | MEDIA |
| GAP-06 | Histórico de reevaluaciones incompleto | BAJA |

---

## 2. ARQUITECTURA OBJETIVO

### 2.1 Principios No Negociables
1. ✅ SQLite como única base de datos
2. ✅ IA 100% local (Ollama)
3. ✅ Sin servicios externos
4. ✅ Persistencia completa
5. ✅ Trazabilidad y auditoría

### 2.2 Flujo MAGERIT Obligatorio
```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO MAGERIT COMPLETO                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CRITERIOS DE VALORACIÓN (Configuración inicial)            │
│     └── Escalas D, I, C, Frecuencia (1-5)                      │
│                                                                 │
│  2. EVALUACIÓN (Contenedor principal)                          │
│     └── ID, Nombre, Fecha, Estado, Límite_Riesgo               │
│                                                                 │
│  3. ACTIVOS (Solo dentro de evaluación)                        │
│     ├── Tipo: Físico / Virtual                                 │
│     ├── Atributos extendidos:                                  │
│     │   - Ubicación física/lógica                              │
│     │   - Host físico (si VM)                                  │
│     │   - Servicio/Aplicación                                  │
│     │   - Propietario                                          │
│     │   - Nivel de exposición                                  │
│     └── Dependencias                                           │
│                                                                 │
│  4. VALORACIÓN DIC (Por activo)                                │
│     ├── Disponibilidad (1-5)                                   │
│     ├── Integridad (1-5)                                       │
│     ├── Confidencialidad (1-5)                                 │
│     └── CRITICIDAD = MAX(D, I, C)                              │
│                                                                 │
│  5. VULNERABILIDADES (Por activo)                              │
│     ├── Código / Descripción                                   │
│     ├── Fuente (Manual / Escáner / IA)                         │
│     └── Amenazas asociadas                                     │
│                                                                 │
│  6. AMENAZAS (Del catálogo MAGERIT)                            │
│     ├── Código MAGERIT (ej: A.24)                              │
│     ├── Tipo de amenaza                                        │
│     ├── Dimensiones afectadas                                  │
│     └── Frecuencia (1-5)                                       │
│                                                                 │
│  7. DEGRADACIÓN (Por activo + amenaza)                         │
│     ├── Deg_D, Deg_I, Deg_C ∈ [0.0 - 1.0]                     │
│     ├── Fuente: Manual / IA                                    │
│     └── Justificación                                          │
│                                                                 │
│  8. IMPACTO (Calculado)                                        │
│     └── IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)       │
│                                                                 │
│  9. RIESGO (Calculado)                                         │
│     ├── RIESGO_AMENAZA = FRECUENCIA × IMPACTO                 │
│     ├── RIESGO_ACTIVO_PROM = PROMEDIO(riesgos)                │
│     └── RIESGO_ACTIVO_MAX = MAX(riesgos)                      │
│                                                                 │
│  10. SALVAGUARDAS / CONTROLES                                  │
│      ├── Del catálogo ISO 27002                                │
│      ├── Estado: Implementado / Planificado / No aplica       │
│      └── Efectividad (%)                                       │
│                                                                 │
│  11. RIESGO RESIDUAL                                           │
│      └── RIESGO × (1 - Efectividad_Controles)                 │
│                                                                 │
│  12. TRATAMIENTO                                               │
│      ├── Mitigar / Aceptar / Transferir / Evitar              │
│      └── Riesgo_Objetivo = Riesgo × 0.5                       │
│                                                                 │
│  13. REEVALUACIÓN (Comparar con evaluación anterior)          │
│      └── Mostrar mejora/deterioro                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. TAREAS DE REFACTORIZACIÓN

### FASE 1: MODELO DE DATOS (PRIORIDAD ALTA)

#### T1.1 - Extender tabla INVENTARIO_ACTIVOS
```sql
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Ubicacion_Fisica TEXT;
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Ubicacion_Logica TEXT;
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Host_Fisico TEXT;
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Servicio_Aplicacion TEXT;
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Propietario TEXT;
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Nivel_Exposicion TEXT DEFAULT 'Interno';
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Dependencias_JSON TEXT;
```

#### T1.2 - Crear tabla VULNERABILIDADES_ACTIVO
```sql
CREATE TABLE VULNERABILIDADES_ACTIVO (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT NOT NULL,
    ID_Activo TEXT NOT NULL,
    Codigo_Vulnerabilidad TEXT,
    Descripcion TEXT NOT NULL,
    Severidad TEXT DEFAULT 'Media',
    Amenazas_Asociadas TEXT,  -- JSON array de códigos MAGERIT
    Fuente TEXT DEFAULT 'manual',
    Fecha_Identificacion TEXT,
    Estado TEXT DEFAULT 'Abierta',
    UNIQUE(ID_Evaluacion, ID_Activo, Codigo_Vulnerabilidad)
);
```

#### T1.3 - Crear tabla HISTORIAL_EVALUACIONES
```sql
CREATE TABLE HISTORIAL_EVALUACIONES (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion_Origen TEXT NOT NULL,
    ID_Evaluacion_Destino TEXT NOT NULL,
    Fecha_Comparacion TEXT,
    Resumen_Cambios TEXT,
    Delta_Riesgo_Promedio REAL,
    Delta_Riesgo_Maximo REAL,
    Mejoras_JSON TEXT,
    Deterioros_JSON TEXT
);
```

### FASE 2: SERVICIOS (PRIORIDAD ALTA)

#### T2.1 - Refactorizar activo_service.py
- Agregar campos extendidos en CRUD
- Validar dependencia VM → Host físico
- Validar duplicados por (Nombre + Evaluación)

#### T2.2 - Crear vulnerabilidad_service.py
- CRUD completo de vulnerabilidades
- Vincular con amenazas MAGERIT
- Sugerencia IA de vulnerabilidades

#### T2.3 - Actualizar magerit_engine.py
- Verificar que usa degradación correctamente ✅ (ya hecho)
- Agregar validación de vulnerabilidades previas
- Bloquear cálculo si faltan datos obligatorios

### FASE 3: UI (PRIORIDAD MEDIA)

#### T3.1 - Formulario de Activos Extendido
- Agregar campos nuevos al formulario
- Selector de Host físico (solo si tipo=Virtual)
- Nivel de exposición (Interno/DMZ/Externo)

#### T3.2 - Pestaña de Vulnerabilidades
- CRUD de vulnerabilidades por activo
- Vincular con amenazas del catálogo
- Sugerencia IA

#### T3.3 - Refactorizar Carga Masiva
- Nueva plantilla Excel con campos extendidos
- Validación de relaciones
- Preview antes de importar

### FASE 4: IA LOCAL (PRIORIDAD MEDIA)

#### T4.1 - Validar respuestas IA
- Si falta contexto: "Información insuficiente"
- Guardar siempre: modelo, timestamp, justificación
- No inventar valores

#### T4.2 - Sugerencias IA por entidad
- Degradación por amenaza ✅ (ya implementado)
- Vulnerabilidades por activo
- Controles recomendados por riesgo

### FASE 5: REPORTES Y COMPARATIVAS (PRIORIDAD BAJA)

#### T5.1 - Comparativa entre evaluaciones
- Mostrar delta de riesgos
- Identificar mejoras/deterioros
- Gráfico de evolución

#### T5.2 - Matriz de Riesgos Mejorada
- Mantener visualización actual
- Agregar filtros por tipo de activo
- Exportar a PDF

---

## 4. ORDEN DE IMPLEMENTACIÓN

```
SEMANA 1: FASE 1 (Modelo de Datos)
├── T1.1 Extender INVENTARIO_ACTIVOS
├── T1.2 Crear VULNERABILIDADES_ACTIVO  
└── T1.3 Crear HISTORIAL_EVALUACIONES

SEMANA 2: FASE 2 (Servicios)
├── T2.1 Refactorizar activo_service.py
├── T2.2 Crear vulnerabilidad_service.py
└── T2.3 Actualizar magerit_engine.py

SEMANA 3: FASE 3 (UI)
├── T3.1 Formulario de Activos Extendido
├── T3.2 Pestaña de Vulnerabilidades
└── T3.3 Refactorizar Carga Masiva

SEMANA 4: FASE 4 + 5 (IA + Reportes)
├── T4.1 Validar respuestas IA
├── T4.2 Sugerencias IA
├── T5.1 Comparativa entre evaluaciones
└── T5.2 Matriz de Riesgos Mejorada
```

---

## 5. VERIFICACIÓN DE CUMPLIMIENTO

### Restricciones No Negociables

| # | Restricción | Estado | Verificación |
|---|-------------|--------|--------------|
| 1 | SQLite como BD | ✅ | tita_database.db único |
| 2 | IA 100% local | ✅ | Ollama sin Internet |
| 3 | Sin servicios externos | ✅ | No HTTP externo |
| 4 | Persistencia completa | ✅ | Todo en SQLite |
| 5 | Trazabilidad | ⚠️ | Falta auditoría de cambios |

### Flujo MAGERIT

| Paso | Elemento | Estado | Observación |
|------|----------|--------|-------------|
| 1 | Criterios | ✅ | Tablas CRITERIOS_* |
| 2 | Evaluación | ✅ | EVALUACIONES con Limite_Riesgo |
| 3 | Activos | ⚠️ | Falta atributos extendidos |
| 4 | Valoración DIC | ✅ | Via cuestionarios |
| 5 | Vulnerabilidades | ❌ | Tabla vacía, sin UI |
| 6 | Amenazas | ✅ | Catálogo + identificación IA |
| 7 | Degradación | ✅ | Tabla + UI + IA |
| 8 | Impacto | ✅ | Fórmula correcta |
| 9 | Riesgo | ✅ | Dual (promedio + max) |
| 10 | Salvaguardas | ✅ | Catálogo ISO 27002 |
| 11 | Riesgo Residual | ✅ | Calculado |
| 12 | Tratamiento | ⚠️ | Falta UI de decisión |
| 13 | Reevaluación | ⚠️ | Falta comparativa |

---

## 6. PRÓXIMO PASO

¿Desea que proceda con:

**OPCIÓN A**: Implementar FASE 1 completa (Modelo de Datos)
- Migración de BD con campos extendidos
- Crear tablas faltantes

**OPCIÓN B**: Implementar incrementalmente por tarea
- Una tarea a la vez con validación

**OPCIÓN C**: Generar script de migración completo para revisión
- Revisar antes de ejecutar

Por favor confirme la opción preferida.

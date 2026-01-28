# 🛡️ Guía de Flujo del Sistema TITA - Matriz de Riesgos MAGERIT

**Documento de Referencia para el Usuario**  
*Última actualización: 27 Enero 2026*

---

## Tabla de Contenidos

1. [Resumen del Sistema](#1-resumen-del-sistema)
2. [Flujo Secuencial de Trabajo](#2-flujo-secuencial-de-trabajo)
3. [Detalle de Cada Tab](#3-detalle-de-cada-tab)
4. [Comparativa con la Matriz Excel](#4-comparativa-con-la-matriz-excel)
5. [Fórmulas del Modelo](#5-fórmulas-del-modelo)
6. [Reglas de Negocio](#6-reglas-de-negocio)

---

## 1. Resumen del Sistema

TITA es un sistema web que replica la funcionalidad de tu matriz de riesgos Excel pero con las ventajas de:

- ✅ Base de datos persistente (SQLite)
- ✅ Cálculos automáticos
- ✅ Visualizaciones interactivas
- ✅ Exportación a Excel
- ✅ Múltiples evaluaciones

### Arquitectura de 8 Tabs

| Tab | Nombre | Propósito Principal |
|-----|--------|-------------------|
| 1 | Criterios | Definir escalas de medición |
| 2 | Activos | Inventario de infraestructura |
| 3 | Valoración D/I/C | Valorar activos y calcular criticidad |
| 4 | Vulnerabilidades | Identificar amenazas y calcular impacto |
| 5 | Riesgo | Asignar frecuencia y calcular riesgo |
| 6 | Mapa Riesgos | Visualización matriz Impacto vs Frecuencia |
| 7 | Riesgo Activos | Agregación: Actual, Objetivo, Límite |
| 8 | Salvaguardas | Controles recomendados |

---

## 2. Flujo Secuencial de Trabajo

**⚠️ IMPORTANTE:** El flujo es SECUENCIAL. Debes completar cada paso antes de continuar.

```
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 0: Crear/Seleccionar Evaluación (Sidebar izquierdo)          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 1: Tab "Criterios" - Revisar las escalas (solo lectura)      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 2: Tab "Activos" - Agregar todos los activos a evaluar       │
│  (individual o carga masiva JSON/Excel)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 3: Tab "Valoración D/I/C" - Para cada activo:                │
│  • Asignar Disponibilidad (N/B/M/A)                                 │
│  • Asignar Integridad (N/B/M/A)                                     │
│  • Asignar Confidencialidad (N/B/M/A)                               │
│  → RESULTADO: Se calcula CRITICIDAD = MAX(D, I, C)                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 4: Tab "Vulnerabilidades" - Para cada activo:                │
│  • Agregar vulnerabilidades identificadas                          │
│  • Especificar amenaza asociada                                    │
│  • Asignar degradación D, I, C (0.0 a 1.0)                         │
│  → RESULTADO: Se calcula IMPACTO = Criticidad × MAX(Deg)           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 5: Tab "Riesgo" - Para cada vulnerabilidad/amenaza:          │
│  • Asignar FRECUENCIA (0.1=Nula, 1=Baja, 2=Media, 3=Alta)          │
│  → RESULTADO: Se calcula RIESGO = Frecuencia × Impacto             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 6: Tab "Mapa Riesgos" - Click "Generar Mapa"                 │
│  → RESULTADO: Visualización scatter Impacto vs Frecuencia          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 7: Tab "Riesgo Activos" - Click "Recalcular Todos"           │
│  → RESULTADO: Agregación por activo:                                │
│    • Riesgo Actual = PROMEDIO de todos los riesgos                 │
│    • Riesgo Objetivo = Actual × 0.5                                │
│    • Comparación con Límite (6)                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PASO 8: Tab "Salvaguardas" - Para activos urgentes:               │
│  • Agregar controles/salvaguardas recomendadas                     │
│  • Asignar responsable y prioridad                                 │
│  • Dar seguimiento al estado                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  EXPORTAR: Sidebar → "Descargar Excel"                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detalle de Cada Tab

### 📏 Tab 1: Criterios de Valoración

**Propósito:** Referencia de las escalas de medición usadas en todo el modelo.

**¿Qué ve el usuario?**
- Escala de Disponibilidad (D)
- Escala de Integridad (I)
- Escala de Confidencialidad (C)
- Escala de Criticidad
- Escala de Frecuencia
- Escala de Degradación
- Fórmulas del modelo

**¿Qué ingresa el usuario?**
- **NADA** - Esta pestaña es solo de consulta/referencia.

**Escalas definidas:**

| Nivel | Valor | Ejemplo Disponibilidad |
|-------|-------|----------------------|
| N - Nula | 0 | No afecta la operación |
| B - Baja | 1 | Afecta operaciones menores |
| M - Media | 2 | Afecta operaciones importantes |
| A - Alta | 3 | Crítico para la operación |

---

### 📦 Tab 2: Activos

**Propósito:** Inventario de activos de TI que serán evaluados.

**¿Qué ingresa el usuario?**

| Campo | Tipo | Obligatorio | Opciones |
|-------|------|-------------|----------|
| Nombre del Activo | Texto | ✅ Sí | Texto libre |
| Tipo de Activo | Selectbox | ✅ Sí | Servidor Físico, Servidor Virtual, Equipo de Red, Almacenamiento, UPS, Otro |
| Ubicación | Selectbox | ✅ Sí | Granados, UdlaPark |
| Área Responsable | Selectbox | ✅ Sí | Infraestructura, Seguridad de la información, Soporte IT |
| Finalidad de Uso | Texto | ✅ Sí | Texto libre (ej: "Base de datos ERP") |
| Aplicación Crítica | Texto | No | Texto libre |

**Formas de ingreso:**
1. **Individual:** Formulario campo por campo
2. **Carga Masiva JSON:** Subir archivo .json con estructura de activos
3. **Carga Masiva Excel:** Subir archivo .xlsx con columnas correspondientes

---

### ⚖️ Tab 3: Valoración D/I/C

**Propósito:** Valorar cada activo en las 3 dimensiones y calcular su criticidad.

**¿Qué ingresa el usuario?**

| Campo | Tipo | Obligatorio | Opciones/Rango |
|-------|------|-------------|----------------|
| Dueño/Responsable | Texto | No | Texto libre |
| Valor Monetario ($) | Número | No | ≥ 0 |
| Usuarios Afectados | Número | No | ≥ 0 |
| Disponibilidad (D) | Selectbox | ✅ Sí | N-Nula, B-Baja, M-Media, A-Alta |
| Integridad (I) | Selectbox | ✅ Sí | N-Nula, B-Baja, M-Media, A-Alta |
| Confidencialidad (C) | Selectbox | ✅ Sí | N-Nula, B-Baja, M-Media, A-Alta |

**Cálculo automático:**
```
CRITICIDAD = MAX(Valor_D, Valor_I, Valor_C)

Donde:
- N = 0, B = 1, M = 2, A = 3
```

**Resultado visible:**
- Valor numérico D (0-3)
- Valor numérico I (0-3)
- Valor numérico C (0-3)
- CRITICIDAD con nivel (Nula/Baja/Media/Alta)

---

### 🔓 Tab 4: Vulnerabilidades y Amenazas

**Propósito:** Identificar vulnerabilidades y sus amenazas asociadas, calcular degradación e impacto.

**¿Qué ingresa el usuario?**

| Campo | Tipo | Obligatorio | Opciones/Rango |
|-------|------|-------------|----------------|
| Vulnerabilidad | Texto | ✅ Sí | Texto libre (ej: "Falta de respaldo eléctrico") |
| Amenaza | Texto | ✅ Sí | Texto libre (ej: "Daños por falta de energía") |
| Código Amenaza | Texto | No | Formato MAGERIT (ej: N.1, E.2, A.24) |
| Degradación D | Slider | ✅ Sí | 0.0 a 1.0 (pasos de 0.1) |
| Degradación I | Slider | ✅ Sí | 0.0 a 1.0 (pasos de 0.1) |
| Degradación C | Slider | ✅ Sí | 0.0 a 1.0 (pasos de 0.1) |

**Significado de la degradación:**
- `0.0` = La amenaza no afecta esta dimensión
- `0.5` = Afectación moderada (50%)
- `1.0` = Afectación total (100%)

**Cálculo automático:**
```
IMPACTO = CRITICIDAD × MAX(Degradación_D, Degradación_I, Degradación_C)
```

**Ejemplo:**
- Criticidad del activo = 3 (Alta)
- Degradación D = 0.7, I = 0.3, C = 0.0
- IMPACTO = 3 × 0.7 = 2.1

---

### ⚡ Tab 5: Riesgo

**Propósito:** Asignar frecuencia a cada amenaza y calcular el riesgo.

**¿Qué ingresa el usuario?**

| Campo | Tipo | Opciones |
|-------|------|----------|
| Frecuencia | Slider/Select | 0.1 (Nula/cada años), 1 (Baja/anual), 2 (Media/mensual), 3 (Alta/diario) |

**Cálculo automático:**
```
RIESGO = FRECUENCIA × IMPACTO
```

**Clasificación de riesgo:**
| Rango | Nivel | Color |
|-------|-------|-------|
| 0 - 2 | Bajo | 🟢 Verde |
| 2 - 4 | Medio | 🟡 Amarillo |
| 4 - 6 | Alto | 🟠 Naranja |
| > 6 | Crítico | 🔴 Rojo |

---

### 🗺️ Tab 6: Mapa de Riesgos

**Propósito:** Visualización gráfica de la matriz de riesgos.

**¿Qué ingresa el usuario?**
- **Solo un click** en "Generar/Actualizar Mapa de Riesgos"

**¿Qué obtiene?**
- Gráfico de dispersión (scatter plot) con:
  - Eje X: Frecuencia
  - Eje Y: Impacto
  - Puntos: Cada par activo-amenaza
  - Colores por zona de riesgo
- Tabla detallada del mapa

---

### 📊 Tab 7: Riesgo por Activos

**Propósito:** Agregar todos los riesgos a nivel de activo para tomar decisiones.

**¿Qué ingresa el usuario?**
- **Solo un click** en "Recalcular Todos los Riesgos"

**Cálculos automáticos:**
```
RIESGO_ACTUAL = PROMEDIO(todos los riesgos de ese activo)
RIESGO_OBJETIVO = RIESGO_ACTUAL × 0.5
LÍMITE = 6 (constante organizacional)
```

**Estados resultantes:**
| Condición | Estado |
|-----------|--------|
| Riesgo_Actual > Límite | 🔴 Tratamiento Urgente |
| Riesgo_Actual > Objetivo | 🟡 Atención Requerida |
| Riesgo_Actual ≤ Objetivo | 🟢 Aceptable |

---

### 🛡️ Tab 8: Salvaguardas

**Propósito:** Definir controles y acciones para mitigar riesgos identificados.

**¿Qué ingresa el usuario?**

| Campo | Tipo | Obligatorio |
|-------|------|-------------|
| Vulnerabilidad relacionada | Selectbox | No |
| Salvaguarda / Control | Texto área | ✅ Sí |
| Prioridad | Selectbox | ✅ Sí (Alta/Media/Baja) |
| Responsable | Texto | No |
| Fecha Límite | Date picker | No |

**Estados de salvaguarda:**
- ⏳ Pendiente
- 🔄 En Proceso
- ✅ Implementada

---

## 4. Comparativa con la Matriz Excel

### Correspondencia de Hojas

| # | Hoja Excel | Tab TITA | Similitudes | Diferencias |
|---|------------|----------|-------------|-------------|
| 1 | **CRITERIOS DE VALORACIÓN** | 📏 Criterios | ✅ Mismas escalas D/I/C, criticidad, frecuencia, degradación | En TITA es solo consulta, en Excel puedes editar las escalas |
| 2 | **ACTIVOS** | 📦 Activos | ✅ Mismos campos (nombre, tipo, ubicación, responsable, servicio) | TITA tiene carga masiva JSON/Excel; Excel es entrada manual |
| 3 | **IDENTIFICACION_VALORACION** | ⚖️ Valoración D/I/C | ✅ Misma lógica: D, I, C → Criticidad = MAX | TITA calcula automáticamente; Excel usa fórmulas que puedes romper |
| 4 | **VULNERABILIDADES_AMENAZAS** | 🔓 Vulnerabilidades | ✅ Mismos campos: vulnerabilidad, amenaza, degradación D/I/C | TITA calcula impacto automáticamente; Excel requiere fórmulas |
| 5 | **RIESGO** | ⚡ Riesgo | ✅ Misma fórmula: Frecuencia × Impacto | TITA tiene slider visual para frecuencia |
| 6 | **MAPA_RIESGOS** | 🗺️ Mapa Riesgos | ✅ Misma matriz Impacto vs Frecuencia | TITA genera gráfico interactivo; Excel es estático |
| 7 | **RIESGO_ACTIVOS** | 📊 Riesgo Activos | ✅ Mismos cálculos: Actual, Objetivo, Límite | TITA recalcula con un click; Excel depende de fórmulas |
| 8 | **SALVAGUARDAS** | 🛡️ Salvaguardas | ✅ Mismos campos: control, prioridad, responsable | TITA tiene seguimiento de estados |

### Ventajas de TITA sobre Excel

| Aspecto | Excel | TITA |
|---------|-------|------|
| **Persistencia** | Un archivo .xlsx que puede perderse | Base de datos SQLite persistente |
| **Cálculos** | Fórmulas que pueden romperse | Cálculos programados, no editables |
| **Multi-evaluación** | Un archivo por evaluación | Todas en una base de datos |
| **Visualización** | Gráficos estáticos | Gráficos interactivos Plotly |
| **Carga de datos** | Manual celda por celda | Carga masiva JSON/Excel |
| **Exportación** | Ya es Excel | Exporta a Excel cuando necesites |
| **Colaboración** | Un usuario a la vez | Puede escalar a web compartida |

### Similitudes Clave

1. **Misma metodología:** MAGERIT v3
2. **Mismas escalas:** 4 niveles (N/B/M/A = 0/1/2/3)
3. **Mismas fórmulas:**
   - Criticidad = MAX(D, I, C)
   - Impacto = Criticidad × MAX(Degradación)
   - Riesgo = Frecuencia × Impacto
4. **Mismo límite:** 6 como umbral organizacional
5. **Mismo factor:** 50% de reducción objetivo

---

## 5. Fórmulas del Modelo

### Fórmulas Principales

```
┌─────────────────────────────────────────────────────────────┐
│  CRITICIDAD = MAX(Valor_D, Valor_I, Valor_C)                │
│                                                             │
│  IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)            │
│                                                             │
│  RIESGO = FRECUENCIA × IMPACTO                              │
│                                                             │
│  RIESGO_ACTUAL = PROMEDIO(todos los riesgos del activo)     │
│                                                             │
│  RIESGO_OBJETIVO = RIESGO_ACTUAL × 0.5                      │
└─────────────────────────────────────────────────────────────┘
```

### Constantes Organizacionales

| Constante | Valor | Descripción |
|-----------|-------|-------------|
| LÍMITE_RIESGO | 6 | Umbral aceptable de riesgo |
| FACTOR_REDUCCIÓN | 0.5 (50%) | Meta de reducción objetivo |

### Mapeo de Niveles a Valores

| Nivel | Letra | Valor Numérico |
|-------|-------|----------------|
| Nula | N | 0 |
| Baja | B | 1 |
| Media | M | 2 |
| Alta | A | 3 |

### Mapeo de Frecuencia

| Frecuencia | Valor | Descripción |
|------------|-------|-------------|
| Nula | 0.1 | Cada varios años |
| Baja | 1 | Anual |
| Media | 2 | Mensual |
| Alta | 3 | Diario |

---

## 6. Reglas de Negocio

### Validaciones

1. **Activos:**
   - Nombre es obligatorio
   - No pueden existir duplicados (mismo nombre + ubicación + servicio)

2. **Valoración:**
   - Un activo debe existir antes de valorarlo
   - D, I, C son obligatorios

3. **Vulnerabilidades:**
   - Un activo debe tener valoración D/I/C antes de agregar vulnerabilidades
   - Vulnerabilidad y Amenaza son campos obligatorios

4. **Riesgo:**
   - Debe existir al menos una vulnerabilidad para calcular riesgo
   - La frecuencia no puede ser 0 (mínimo 0.1)

### Flujo de Dependencias

```
EVALUACIÓN (contenedor)
    │
    └── ACTIVOS
            │
            └── VALORACIÓN D/I/C → calcula CRITICIDAD
                    │
                    └── VULNERABILIDADES → calcula IMPACTO
                            │
                            └── RIESGO → calcula RIESGO
                                    │
                                    ├── MAPA RIESGOS (visualización)
                                    │
                                    └── RIESGO ACTIVOS (agregación)
                                            │
                                            └── SALVAGUARDAS (tratamiento)
```

---

## Resumen Visual del Flujo de Datos

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE DATOS TITA                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ENTRADA (Usuario)              PROCESO                SALIDA       │
│   ─────────────────              ───────                ──────       │
│                                                                      │
│   Nombre, Tipo, Ubicación   →   Tab 2: Activos    →   ID_Activo     │
│                                                                      │
│   D, I, C (N/B/M/A)         →   Tab 3: Valoración →   CRITICIDAD    │
│                                                                      │
│   Vulnerabilidad, Amenaza   →   Tab 4: Vulns      →   IMPACTO       │
│   Degradación D/I/C                                                  │
│                                                                      │
│   Frecuencia (0.1-3)        →   Tab 5: Riesgo     →   RIESGO        │
│                                                                      │
│   [Click botón]             →   Tab 6: Mapa       →   GRÁFICO       │
│                                                                      │
│   [Click botón]             →   Tab 7: Agregado   →   ACTUAL/OBJ    │
│                                                                      │
│   Control, Responsable      →   Tab 8: Salvaguardas → SEGUIMIENTO   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

**Documento generado para el Proyecto TITA**  
*Sistema de Evaluación de Riesgos MAGERIT v3*

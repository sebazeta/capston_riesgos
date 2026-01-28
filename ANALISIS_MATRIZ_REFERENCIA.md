# 📊 ANÁLISIS COMPLETO DE LA MATRIZ DE REFERENCIA
## CALIFICACION_MANUAL_UPS.xlsx

**Fecha de análisis:** 27 de enero de 2026  
**Analista:** Arquitecto de Ciberseguridad  
**Propósito:** Comprender la lógica de la matriz para adaptarla al sistema TITA

---

## 📑 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis Hoja por Hoja](#análisis-hoja-por-hoja)
3. [Flujo Completo del Modelo](#flujo-completo-del-modelo)
4. [Glosario de Conceptos Clave](#glosario-de-conceptos-clave)
5. [Relación con Proyecto TITA](#relación-con-proyecto-tita)
6. [Diferencias Conceptuales](#diferencias-conceptuales)
7. [Validación de Entendimiento](#validación-de-entendimiento)

---

## 📌 RESUMEN EJECUTIVO

La matriz **CALIFICACION_MANUAL_UPS.xlsx** implementa un modelo **MAGERIT clásico** con las siguientes características:

| Característica | Valor |
|----------------|-------|
| **Escala DIC** | 0-3 (Nula, Baja, Media, Alta) |
| **Escala Frecuencia** | 0.1-3 (Cada varios años → Diario) |
| **Cálculo Criticidad** | MAX(D, I, C) |
| **Cálculo Impacto** | Suma de degradaciones D+I+C |
| **Cálculo Riesgo** | Frecuencia × Impacto |
| **Agregación por Activo** | PROMEDIO de todos sus riesgos |
| **Límite de Riesgo** | 7 (constante organizacional) |
| **Objetivo de Reducción** | 50% del riesgo actual |

### Hojas del Excel

```
1. CRITERIOS DE VALORACIÓN    → Escalas de medición
2. ACTIVOS                    → Inventario de infraestructura
3. IDENTIFICACION_VALORACION  → Valoración D, I, C + Criticidad
4. VULNERABILIDADES_AMENAZAS  → Amenazas + Degradación + Impacto
5. RIESGO                     → Frecuencia × Impacto por amenaza
6. MAPA_RIESGOS_UPS          → Visualización matriz de riesgos
7. RIESGO_ACTIVOS            → Agregación: Actual, Objetivo, Límite
8. SALVAGUARDAS              → Controles recomendados
```

---

## 📋 ANÁLISIS HOJA POR HOJA

### 1️⃣ HOJA: CRITERIOS DE VALORACIÓN

**Propósito:** Define las escalas de medición para todo el modelo.

#### Escala de Disponibilidad (D)
| Nivel | Valor | Descripción |
|-------|-------|-------------|
| Alta (A) | 3 | Inaccesibilidad de 1 hora impide actividades |
| Media (M) | 2 | Inaccesibilidad de 1 jornada impide actividades |
| Baja (B) | 1 | Inaccesibilidad de 1 semana ocasiona perjuicio |
| Nula (N) | 0 | Inaccesibilidad no afecta actividad normal |

#### Escala de Integridad (I)
| Nivel | Valor | Descripción |
|-------|-------|-------------|
| Alta (A) | 3 | Modificación no autorizada no puede repararse |
| Media (M) | 2 | Modificación difícil de reparar, perjuicio significativo |
| Baja (B) | 1 | Modificación reparable, perjuicio menor |
| Nula (N) | 0 | Modificación reparable fácilmente, sin afectación |

#### Escala de Confidencialidad (C)
| Nivel | Valor | Descripción |
|-------|-------|-------------|
| Alta (A) | 3 | Solo grupo muy reducido, divulgación = perjuicio |
| Media (M) | 2 | Solo quienes necesitan para su trabajo |
| Baja (B) | 1 | Todos los empleados de la empresa |
| Nula (N) | 0 | Cualquier persona dentro o fuera de la empresa |

#### Escala de Criticidad
| Nivel | Valor | Criterio |
|-------|-------|----------|
| Alta (A) | 3 | Si MAX(D,I,C) = 3 |
| Media (M) | 2 | Si MAX(D,I,C) = 2 |
| Baja (B) | 1 | Si MAX(D,I,C) = 1 |
| Nula (N) | 0 | Si todos son 0 |

#### Escala de Frecuencia
| Nivel | Valor | Descripción |
|-------|-------|-------------|
| Alta (A) | 3 | A diario |
| Media (M) | 2 | Mensualmente |
| Baja (B) | 1 | 1 vez al año |
| Nula (N) | 0.1 | Cada varios años |

**Entradas:** Ninguna (es hoja de referencia)  
**Salidas:** Escalas para las demás hojas

---

### 2️⃣ HOJA: ACTIVOS

**Propósito:** Inventario detallado de activos físicos/virtuales.

#### Campos capturados

| Categoría | Campos |
|-----------|--------|
| **Identificación** | #, Nombre Activo, ID, Modelo, Serial |
| **Descripción técnica** | Descripción hardware, Fabricante |
| **Contexto operacional** | Área responsable, Vigencia tecnológica, Finalidad de uso |
| **Información de soporte** | Fecha instalación, Garantía, Proveedor mantenimiento |
| **Administración** | Número de administradores, Ubicación física, Rack |
| **Características técnicas** | Virtualización (SI/NO), Sistema operativo, Licenciamiento |
| **Observaciones** | Dependencias con otros activos |

#### Activos del ejemplo

| # | Activo | Fabricante | Ubicación |
|---|--------|------------|-----------|
| 1 | UPS TRIPP-LITE (80 KVA) | TRIPP-LITE | Datacenter Subsuelo |
| 2 | GRUPO ELECTROGENO | SDMO | Sala Generador |
| 3 | AIRE ACONDICIONADO LIEBERT | LIEBERT | Datacenter Subsuelo |

**Entradas:** Registro manual del inventario  
**Salidas:** Lista de activos para valoración

---

### 3️⃣ HOJA: IDENTIFICACION_VALORACION

**Propósito:** Valorar cada activo en D, I, C y calcular su criticidad.

#### Estructura

```
# | Activo | Dueño | Valor_Monetario | Usuarios_Afectados | D | Valor_D | I | Valor_I | C | Valor_C | CRITICIDAD
```

#### Fórmula de Criticidad

```
CRITICIDAD = MAX(Valor_D, Valor_I, Valor_C)
```

#### Datos del ejemplo

| Activo | D | I | C | Criticidad |
|--------|---|---|---|------------|
| UPS TRIPP-LITE | Media (2) | Nula (0) | Baja (1) | **2** |
| GRUPO ELECTROGENO | Alta (3) | Baja (1) | Nula (0) | **3** |
| AA LIEBERT | Alta (3) | Baja (1) | Nula (0) | **3** |

**Entradas:** Selección de nivel D, I, C por activo  
**Salidas:** Criticidad calculada para cada activo

---

### 4️⃣ HOJA: VULNERABILIDADES_AMENAZAS

**Propósito:** Identificar vulnerabilidades, amenazas y calcular DEGRADACIÓN e IMPACTO.

#### Estructura

```
Activo | Criticidad | VULNERABILIDAD | AMENAZA | Degradación_D | Degradación_I | Degradación_C | IMPACTO
```

#### Fórmula de Impacto

```
IMPACTO = CRITICIDAD × MAX(Degradación_D, Degradación_I, Degradación_C)
```

> **Nota:** El impacto se calcula multiplicando la criticidad del activo por la degradación máxima entre las tres dimensiones. Esto pondera el daño según la importancia del activo.

#### Escala de Degradación

- **0.0** = Sin degradación
- **0.1 - 0.3** = Degradación baja
- **0.4 - 0.6** = Degradación media
- **0.7 - 0.9** = Degradación alta
- **1.0** = Degradación total

#### Datos del ejemplo (UPS TRIPP-LITE)

| Vulnerabilidad | Amenaza | Deg_D | Deg_I | Deg_C | IMPACTO |
|----------------|---------|-------|-------|-------|---------|
| Posibilidad de incendios | Daños por fuego | 0.9 | 0.2 | 0.2 | **1.8** |
| Falta protección inundación | Daños por agua | 0.9 | 0.2 | 0.2 | **1.8** |
| Problemas estructurales | Desastres naturales | 1.0 | 0.2 | 0.2 | **2.0** |
| Falta energía eléctrica | Daños equipos escritorio | 1.0 | 0.2 | 0.0 | **2.0** |
| Falta capacitación | Errores de usuario | 0.5 | 0.5 | 0.2 | **1.0** |
| Sin repuestos | Daños hardware | 1.0 | 0.2 | 0.0 | **2.0** |
| Sin procedimientos contingencia | Imposibilidad recuperación | 1.0 | 0.2 | 0.2 | **2.0** |
| Sin soporte técnico | Daños por falta mantenimiento | 1.0 | 0.5 | 0.0 | **2.0** |

**Entradas:** Vulnerabilidades y amenazas identificadas + degradación estimada  
**Salidas:** Impacto total por cada par vulnerabilidad-amenaza

---

### 5️⃣ HOJA: RIESGO

**Propósito:** Calcular el riesgo por cada par activo-amenaza.

#### Estructura

```
Activo | Amenaza | FRECUENCIA | IMPACTO_TOTAL | RIESGO
```

#### Fórmula de Riesgo

```
RIESGO = FRECUENCIA × IMPACTO_TOTAL
```

#### Tabla de Frecuencia (referencia)

| Valor | Significado |
|-------|-------------|
| 3 | A diario |
| 2 | Mensualmente |
| 1 | 1 vez al año |
| 0.1 | Cada varios años |

#### Datos del ejemplo (UPS TRIPP-LITE)

| Amenaza | Frecuencia | Impacto | RIESGO |
|---------|------------|---------|--------|
| Daños por fuego | 0.1 | 1.8 | **0.18** |
| Daños por agua | 0.1 | 1.8 | **0.18** |
| Desastres naturales | 0.1 | 2.0 | **0.20** |
| Daños equipos escritorio | 2.0 | 2.0 | **4.00** |
| Errores de usuario | 1.0 | 1.0 | **1.00** |
| Daños hardware | 2.0 | 2.0 | **4.00** |
| Imposibilidad recuperación | 1.0 | 2.0 | **2.00** |
| Daños falta mantenimiento | 2.0 | 2.0 | **4.00** |

**Entradas:** Frecuencia + Impacto (de hoja anterior)  
**Salidas:** Riesgo por cada amenaza

---

### 6️⃣ HOJA: MAPA_RIESGOS_UPS

**Propósito:** Matriz visual de riesgos para representación gráfica (Impacto vs Frecuencia).

#### Estructura

```
Riesgo_ID | Impacto | Frecuencia | Descripción_Amenaza
```

#### Datos del ejemplo

| ID | Impacto | Frecuencia | Amenaza |
|----|---------|------------|---------|
| R1 | 1.8 | 0.1 | Daños ocasionados por fuego |
| R2 | 1.8 | 0.1 | Daños ocasionados por agua |
| R3 | 2.0 | 0.1 | Daños por desastres naturales |
| R4 | 2.0 | 2.0 | Daños falta energía eléctrica |
| R5 | 1.0 | 1.0 | Errores de usuario |
| R6 | 2.0 | 2.0 | Daños hardware |
| R7 | 2.0 | 1.0 | Imposibilidad recuperación |
| R8 | 2.0 | 2.0 | Daños falta mantenimiento |

**Entradas:** Datos consolidados de hoja RIESGO  
**Salidas:** Datos para visualización en matriz 2D

---

### 7️⃣ HOJA: RIESGO_ACTIVOS

**Propósito:** AGREGACIÓN del riesgo a nivel de activo. **Esta es la hoja más importante.**

#### Estructura

```
ACTIVO | RIESGO_ACTUAL | RIESGO_OBJETIVO | LIMITE | OBSERVACIÓN
```

#### Fórmulas

```python
RIESGO_ACTUAL  = PROMEDIO(todos los riesgos del activo)
RIESGO_OBJETIVO = RIESGO_ACTUAL × 0.5   # Reducción del 50%
LIMITE = 7                               # Constante organizacional
```

#### Datos del ejemplo

| Activo | Actual | Objetivo | Límite | Observación |
|--------|--------|----------|--------|-------------|
| UPS TRIPP-LITE | 1.945 | 0.9725 | 7 | Reducción 50% recomendada |
| GRUPO ELECTROGENO | 1.633 | 0.8167 | 7 | - |
| AA LIEBERT | 2.644 | 1.3222 | 7 | - |

#### Interpretación

- **ACTUAL < LIMITE**: El activo está dentro del umbral aceptable ✅
- **ACTUAL > LIMITE**: El activo requiere tratamiento urgente ⚠️
- **OBJETIVO**: Meta a alcanzar después de implementar salvaguardas

**Entradas:** Riesgos individuales de hoja RIESGO  
**Salidas:** Riesgo agregado + objetivo + límite

---

### 8️⃣ HOJA: SALVAGUARDAS

**Propósito:** Recomendaciones de controles/salvaguardas para mitigar riesgos.

#### Estructura

```
Activo | Riesgo_ID | VULNERABILIDAD | AMENAZA | SALVAGUARDA
```

#### Datos del ejemplo

| Activo | Riesgo | Vulnerabilidad | Salvaguarda |
|--------|--------|----------------|-------------|
| UPS TRIPP-LITE | R8 | Sin soporte técnico | Contar con soporte y mantenimientos periódicos |
| UPS TRIPP-LITE | R4 | Falta energía equipos | Soporte técnico y mantenimientos periódicos |
| GRUPO ELECTROGENO | R2 | Falta protección inundación | Impermeabilización estructura + seguimiento |
| AA LIEBERT | R2 | Componentes defectuosos | Impermeabilización estructura datacenter |
| AA LIEBERT | R4 | Sin repuestos | Mantenimientos periódicos UPS y generador |
| AA LIEBERT | R5 | Sin procedimientos | Mantenimientos periódicos AA |
| AA LIEBERT | R9 | Problemas estructurales | Mantenimientos periódicos AA |

**Entradas:** Riesgos identificados  
**Salidas:** Recomendaciones de tratamiento

---

## 🔄 FLUJO COMPLETO DEL MODELO

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO MAGERIT DE LA MATRIZ                            │
└─────────────────────────────────────────────────────────────────────────────────┘

   CRITERIOS DE VALORACIÓN (Escalas 0-3)
              │
              ▼
   ┌─────────────────┐
   │    ACTIVOS      │  ◄── Inventario de infraestructura
   └────────┬────────┘
            │
            ▼
   ┌─────────────────────────────┐
   │ IDENTIFICACION_VALORACION   │  ◄── Valoración D, I, C
   │                             │
   │  Criticidad = MAX(D, I, C)  │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────────────┐
   │    VULNERABILIDADES_AMENAZAS        │
   │                                     │
   │  Por cada activo:                   │
   │  - Identificar vulnerabilidades     │
   │  - Asociar amenazas                 │
   │  - Estimar degradación D, I, C      │
   │                                     │
   │  IMPACTO = CRITICIDAD ×             │
   │            MAX(Deg_D, Deg_I, Deg_C)  │
   └────────────────┬────────────────────┘
                    │
                    ▼
   ┌─────────────────────────────────────┐
   │           RIESGO                    │
   │                                     │
   │  Por cada par (activo, amenaza):    │
   │                                     │
   │  RIESGO = FRECUENCIA × IMPACTO      │
   └────────────────┬────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
┌─────────────────┐   ┌─────────────────────┐
│ MAPA_RIESGOS    │   │  RIESGO_ACTIVOS     │
│                 │   │                     │
│ Visualización   │   │ AGREGACIÓN:         │
│ Impacto vs      │   │ Riesgo_Actual =     │
│ Frecuencia      │   │   PROMEDIO(riesgos) │
│                 │   │                     │
│                 │   │ Riesgo_Objetivo =   │
│                 │   │   Actual × 0.5      │
│                 │   │                     │
│                 │   │ Límite = 7          │
└─────────────────┘   └──────────┬──────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     SALVAGUARDAS        │
                    │                         │
                    │ Controles recomendados  │
                    │ para reducir riesgo     │
                    │ al nivel OBJETIVO       │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    RE-EVALUACIÓN        │
                    │    (Siguiente ciclo)    │
                    └─────────────────────────┘
```

### Flujo Resumido (Fórmulas)

```
1. CRITICIDAD     = MAX(D, I, C)
2. IMPACTO        = CRITICIDAD × MAX(Degradación_D, Degradación_I, Degradación_C)
3. RIESGO_AMENAZA = FRECUENCIA × IMPACTO
4. RIESGO_ACTIVO  = PROMEDIO(RIESGO_AMENAZA₁, RIESGO_AMENAZA₂, ..., RIESGO_AMENAZAₙ)
5. OBJETIVO       = RIESGO_ACTIVO × 0.5
6. DECISIÓN       = SI RIESGO_ACTIVO > LIMITE ENTONCES "Tratamiento Urgente"
```

### Flujo Completo (13 Pasos)

```
1.  Definir CRITERIOS DE VALORACIÓN (escalas 0-3)
2.  Registrar ACTIVOS (inventario de infraestructura)
3.  Valorar D, I, C por cada activo
4.  CRITICIDAD = MAX(D, I, C)

5.  Identificar VULNERABILIDADES por activo
6.  Asociar AMENAZAS a cada vulnerabilidad
7.  Estimar degradación D/I/C por cada amenaza

8.  IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)
9.  RIESGO = FRECUENCIA × IMPACTO

10. MAPA DE RIESGOS (visualización Impacto vs Frecuencia)

11. RIESGO_ACTIVO:
    - Riesgo_Actual = PROMEDIO(todos los riesgos del activo)
    - Riesgo_Objetivo = Riesgo_Actual × 0.5
    - Límite = umbral organizacional definido

12. SALVAGUARDAS:
    - Identificar controles para reducir el riesgo al objetivo

13. REEVALUACIÓN:
    - Ajustar valoraciones según controles implementados
    - Evidenciar reducción del riesgo
    - Repetir ciclo
```

---

## 📖 GLOSARIO DE CONCEPTOS CLAVE

| Concepto | Definición | Fórmula/Valor |
|----------|------------|---------------|
| **Disponibilidad (D)** | Importancia de que el activo esté accesible cuando se necesita | Escala 0-3 |
| **Integridad (I)** | Importancia de que los datos no sean modificados sin autorización | Escala 0-3 |
| **Confidencialidad (C)** | Importancia de que la información no sea divulgada a no autorizados | Escala 0-3 |
| **Criticidad** | Nivel de importancia máximo del activo considerando D, I, C | MAX(D, I, C) |
| **Vulnerabilidad** | Debilidad en un activo que puede ser explotada por una amenaza | Texto descriptivo |
| **Amenaza** | Evento potencial que puede explotar una vulnerabilidad y causar daño | Texto descriptivo |
| **Degradación** | Porcentaje de daño que la amenaza causa a cada dimensión (D, I, C) | 0.0 - 1.0 |
| **Impacto** | Daño total si la amenaza se materializa | CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C) |
| **Frecuencia** | Probabilidad/frecuencia de ocurrencia de la amenaza | 0.1 - 3.0 |
| **Riesgo (por amenaza)** | Nivel de riesgo de un par específico activo-amenaza | Frecuencia × Impacto |
| **Riesgo Actual (por activo)** | Riesgo consolidado del activo considerando todas sus amenazas | PROMEDIO(riesgos) |
| **Riesgo Objetivo** | Meta de riesgo a alcanzar después de aplicar controles | Riesgo_Actual × 0.5 |
| **Límite de Riesgo** | Umbral máximo de riesgo aceptable por la organización | Constante = 7 |
| **Salvaguarda** | Control, medida o contramedida para reducir el riesgo | Texto recomendación |
| **Reevaluación** | Nuevo ciclo de análisis para verificar efectividad de controles | Proceso periódico |

---

## 🔗 RELACIÓN CON PROYECTO TITA

### Mapeo: Hojas Excel → Módulos TITA

| Hoja Excel | Equivalente en TITA | Estado |
|------------|---------------------|--------|
| CRITERIOS DE VALORACIÓN | `CRITERIOS_VALORACION` (catálogo) | ✅ Existe (escala 1-5) |
| ACTIVOS | `INVENTARIO_ACTIVOS` | ✅ Existe |
| IDENTIFICACION_VALORACION | Cuestionarios + `Impacto_C, Impacto_I, Impacto_D` | ✅ Existe (cálculo diferente) |
| VULNERABILIDADES_AMENAZAS | `CATALOGO_AMENAZAS` + `magerit_engine.py` | ⚠️ Parcial |
| RIESGO | `RESULTADOS_MAGERIT.Riesgo_Inherente` | ✅ Existe (fórmula diferente) |
| MAPA_RIESGOS_UPS | `dashboard_magerit.py` | ✅ Existe |
| RIESGO_ACTIVOS | `RESULTADOS_MAGERIT` | ⚠️ Parcial (sin promedio) |
| SALVAGUARDAS | `CATALOGO_CONTROLES` + `controles_recomendados` | ✅ Existe |

### Componentes por Estado

#### ✅ Ya existe y funciona igual
- Inventario de activos
- Catálogo de amenazas MAGERIT
- Catálogo de controles ISO 27002
- Visualización de riesgos (dashboard)
- Recomendación de salvaguardas automática

#### ⚠️ Existe pero funciona diferente

| Aspecto | Matriz Excel | TITA Actual |
|---------|--------------|-------------|
| Escala DIC | 0-3 | 1-5 |
| Criticidad | MAX(D,I,C) | Calculado por cuestionario |
| Degradación | Manual por amenaza (0-1) | Automática basada en tipo activo |
| Impacto | Suma de degradaciones | Valor del activo (1-5) |
| Frecuencia | 0.1-3 | 1-5 (Probabilidad) |
| Riesgo | Frecuencia × Impacto | Probabilidad × Impacto |
| Agregación | PROMEDIO por activo | Riesgo único por activo |
| Riesgo Objetivo | Actual × 0.5 | Riesgo_Residual (con controles) |

#### ❌ No existe aún en TITA

| Concepto | Descripción |
|----------|-------------|
| **Límite de Riesgo** | Umbral máximo aceptable definido por organización |
| **Riesgo Objetivo** | Meta de reducción porcentual (50%) |
| **Degradación granular** | Especificar degradación D, I, C por cada amenaza |
| **Múltiples riesgos por activo** | Vista de N riesgos (uno por amenaza) |
| **Promedio de riesgos** | Agregación matemática a nivel activo |
| **Vulnerabilidades explícitas** | Captura formal de vulnerabilidades |

---

## ⚖️ DIFERENCIAS CONCEPTUALES

### 1. Diferencias de Escala

| Concepto | Matriz Excel | TITA Actual | Impacto |
|----------|--------------|-------------|---------|
| D, I, C | 0, 1, 2, 3 | 1, 2, 3, 4, 5 | Rango diferente |
| Frecuencia | 0.1, 1, 2, 3 | 1, 2, 3, 4, 5 | Valores no equivalentes |
| Degradación | 0.0 - 1.0 | No existe | Concepto nuevo |

### 2. Diferencias de Cálculo

| Fórmula | Matriz Excel | TITA Actual |
|---------|--------------|-------------|
| **Impacto** | CRITICIDAD × MAX(Deg) | max(Impacto_C, Impacto_I, Impacto_D) |
| **Riesgo** | Frecuencia × Impacto | Probabilidad × Valor_Activo |
| **Riesgo Residual** | Riesgo × 0.5 (objetivo fijo) | Riesgo × (1 - eficacia_controles) |
| **Riesgo por Activo** | PROMEDIO de riesgos | Único valor calculado |
| **Criticidad** | MAX(D, I, C) | Cuestionario multi-bloque |

### 3. Diferencias de Granularidad

| Aspecto | Matriz Excel | TITA Actual |
|---------|--------------|-------------|
| Amenazas por activo | Múltiples filas (una por cada) | Múltiples en JSON |
| Riesgo por activo | Múltiples → PROMEDIO | Un único valor final |
| Vulnerabilidades | Listadas explícitamente | No se capturan |
| Degradación | Por cada amenaza | Global por tipo activo |

### 4. Diferencias de Enfoque

| Aspecto | Matriz Excel | TITA Actual |
|---------|--------------|-------------|
| Entrada de datos | 100% Manual (celdas) | Semi-automático (cuestionarios + IA) |
| Degradación | Definida por analista | Calculada por heurísticas |
| Frecuencia | Definida por analista | Calculada por exposición/historial |
| Objetivo de riesgo | Reducción fija (50%) | No definido formalmente |
| Salvaguardas | Texto libre | Catálogo ISO 27002 estructurado |

---

## ✅ VALIDACIÓN DE ENTENDIMIENTO

### Preguntas de Verificación

| Pregunta | Respuesta |
|----------|-----------|
| ¿Entiendo completamente cómo funciona la matriz? | **SÍ** |
| ¿Puedo explicar su funcionamiento sin el Excel? | **SÍ** |
| ¿Identifico todas las hojas y su propósito? | **SÍ** |
| ¿Comprendo las fórmulas y su secuencia? | **SÍ** |
| ¿Puedo mapear cada hoja a TITA? | **SÍ** |
| ¿Identifico las diferencias clave? | **SÍ** |
| ¿Estoy listo para la fase de adaptación? | **SÍ** |

### Resumen del Modelo Entendido

El modelo MAGERIT de la matriz sigue este flujo:

1. **Inventariar** activos con sus características
2. **Valorar** cada activo en Disponibilidad, Integridad, Confidencialidad (0-3)
3. **Calcular criticidad** = MAX(D, I, C)
4. **Identificar vulnerabilidades** específicas del activo
5. **Asociar amenazas** que explotan cada vulnerabilidad
6. **Estimar degradación** que cada amenaza causa a D, I, C (0-1)
7. **Calcular impacto** = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)
8. **Estimar frecuencia** de materialización (0.1-3)
9. **Calcular riesgo por amenaza** = Frecuencia × Impacto
10. **Agregar riesgo por activo** = PROMEDIO de sus riesgos
11. **Definir objetivo** = Riesgo × 0.5
12. **Comparar con límite** = 7
13. **Proponer salvaguardas** para alcanzar el objetivo
14. **Reevaluar** en siguiente ciclo

---

## 📌 CONCLUSIONES

### Lo que la matriz hace bien
- Modelo MAGERIT completo y formal
- Trazabilidad desde activo hasta salvaguarda
- Agregación matemática clara (PROMEDIO)
- Objetivo y límite de riesgo definidos
- Degradación granular por dimensión

### Lo que TITA hace bien
- Automatización con cuestionarios
- Integración con IA para análisis
- Catálogos ISO 27002 estructurados
- Dashboard interactivo
- Escalas más granulares (1-5)

### Decisiones Pendientes para Adaptación
1. ¿Mantener escala 1-5 o migrar a 0-3?
2. ¿Implementar degradación manual o mantener automática?
3. ¿Agregar captura de vulnerabilidades?
4. ¿Implementar límite y objetivo de riesgo?
5. ¿Cambiar agregación a PROMEDIO?

---

**Documento generado:** 27/01/2026  
**Estado:** Listo para fase de adaptación

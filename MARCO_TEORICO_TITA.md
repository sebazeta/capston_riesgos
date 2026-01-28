# 📚 MARCO TEÓRICO ÚNICO
## Modelo MAGERIT + ISO 27002
### Proyecto TITA – Comprensión Integral del Sistema

**Versión:** 1.0  
**Fecha:** 27 de enero de 2026  
**Propósito:** Documento de referencia conceptual única para el proyecto TITA

---

## 📑 ÍNDICE

1. [Visión General del Modelo](#1-visión-general-del-modelo)
2. [Flujo Conceptual del Modelo](#2-flujo-conceptual-del-modelo)
3. [Conceptos Fundamentales](#3-conceptos-fundamentales)
4. [Fórmulas del Modelo](#4-fórmulas-del-modelo)
5. [Catálogos de Referencia](#5-catálogos-de-referencia)
6. [Ciclo de Reevaluación](#6-ciclo-de-reevaluación)
7. [Indicadores de Madurez](#7-indicadores-de-madurez)
8. [Niveles de Riesgo](#8-niveles-de-riesgo)
9. [Estrategias de Tratamiento](#9-estrategias-de-tratamiento)
10. [Glosario Completo](#10-glosario-completo)

---

## 1. VISIÓN GENERAL DEL MODELO

### 1.1 Objetivo del Sistema

El proyecto TITA implementa una **matriz de riesgos MAGERIT** alineada a un modelo de referencia institucional, integrada con:

- ✅ Catálogo de amenazas MAGERIT v3
- ✅ Catálogo de salvaguardas/controles ISO 27002:2022
- ✅ Ciclos de reevaluación periódica
- ✅ Indicadores de madurez de ciberseguridad

> **Misión del Sistema:**  
> *Identificar, medir, mitigar y reevaluar riesgos de activos críticos, demostrando mejora real en el tiempo.*

### 1.2 Principios Rectores

| Principio | Descripción |
|-----------|-------------|
| **Trazabilidad** | Cada riesgo es rastreable desde el activo hasta el control |
| **Medibilidad** | Todo cálculo es reproducible y auditable |
| **Comparabilidad** | Los resultados son comparables entre ciclos |
| **Mejora Continua** | El objetivo es demostrar reducción de riesgo |
| **Alineación Normativa** | Cumple con MAGERIT v3 e ISO 27002:2022 |

### 1.3 Alcance del Modelo

```
┌─────────────────────────────────────────────────────────────┐
│                    ALCANCE DEL SISTEMA                       │
├─────────────────────────────────────────────────────────────┤
│  ✓ Activos de TI (servidores físicos y virtuales)           │
│  ✓ Infraestructura de soporte (UPS, generadores, AA)        │
│  ✓ Sistemas de información                                   │
│  ✓ Bases de datos                                            │
│  ✓ Redes y comunicaciones                                    │
│  ✓ Servicios en la nube                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. FLUJO CONCEPTUAL DEL MODELO

### 2.1 Flujo Lógico Inalterable

El modelo sigue un flujo secuencial que **no debe alterarse**:

```
CRITERIOS → ACTIVOS → VALORACIÓN D/I/C → CRITICIDAD
→ VULNERABILIDADES → AMENAZAS → DEGRADACIÓN
→ IMPACTO → RIESGO → SALVAGUARDAS → REEVALUACIÓN
```

### 2.2 Diagrama de Flujo Detallado

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO MAGERIT - PROYECTO TITA                          │
└─────────────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────┐
   │  1. CRITERIOS DE VALORACIÓN │  ◄── Escalas definidas (0-3 o 1-5)
   │     - Disponibilidad        │
   │     - Integridad            │
   │     - Confidencialidad      │
   │     - Frecuencia            │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  2. INVENTARIO DE ACTIVOS   │  ◄── Registro de infraestructura
   │     - Identificación        │
   │     - Tipo (físico/virtual) │
   │     - Ubicación             │
   │     - Responsable           │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  3. VALORACIÓN D, I, C      │  ◄── Por cada activo
   │                             │
   │     Disponibilidad = ?      │
   │     Integridad = ?          │
   │     Confidencialidad = ?    │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  4. CRITICIDAD              │
   │                             │
   │  CRITICIDAD = MAX(D, I, C)  │  ◄── Valor más alto de las 3 dimensiones
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  5. VULNERABILIDADES        │  ◄── Debilidades identificadas
   │     - Por activo            │
   │     - Contexto específico   │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  6. AMENAZAS                │  ◄── Catálogo MAGERIT
   │     - Asociadas a vulner.   │
   │     - Tipo (N/I/E/A)        │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  7. DEGRADACIÓN             │  ◄── Por cada amenaza
   │                             │
   │     Deg_D = 0.0 - 1.0       │
   │     Deg_I = 0.0 - 1.0       │
   │     Deg_C = 0.0 - 1.0       │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  8. IMPACTO                 │
   │                             │
   │  IMPACTO = CRITICIDAD ×     │
   │    MAX(Deg_D, Deg_I, Deg_C) │
   └────────────┬────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  9. RIESGO POR AMENAZA      │
   │                             │
   │  RIESGO = FRECUENCIA ×      │
   │           IMPACTO           │
   └────────────┬────────────────┘
                │
         ┌──────┴──────┐
         ▼             ▼
   ┌───────────┐  ┌─────────────────────┐
   │  10. MAPA │  │  11. RIESGO_ACTIVO  │
   │  RIESGOS  │  │                     │
   │           │  │  Actual = PROMEDIO  │
   │  Impacto  │  │  Objetivo = 50%     │
   │    vs     │  │  Límite = Umbral    │
   │ Frecuencia│  │                     │
   └───────────┘  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  12. SALVAGUARDAS   │
                  │                     │
                  │  Controles ISO 27002│
                  │  para reducir       │
                  │  riesgo al OBJETIVO │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  13. REEVALUACIÓN   │
                  │                     │
                  │  - Nuevo ciclo      │
                  │  - Medir mejora     │
                  │  - Ajustar valores  │
                  └─────────────────────┘
                             │
                             ▼
                     (Volver al paso 3)
```

### 2.3 Los 13 Pasos del Modelo

| Paso | Nombre | Entrada | Salida |
|------|--------|---------|--------|
| 1 | Criterios de Valoración | Definición organizacional | Escalas D, I, C, F |
| 2 | Inventario de Activos | Registro manual | Lista de activos |
| 3 | Valoración D, I, C | Cuestionarios/Análisis | Valores D, I, C por activo |
| 4 | Criticidad | Valores D, I, C | CRITICIDAD = MAX(D, I, C) |
| 5 | Vulnerabilidades | Análisis de debilidades | Lista de vulnerabilidades |
| 6 | Amenazas | Catálogo MAGERIT | Amenazas asociadas |
| 7 | Degradación | Estimación por amenaza | Deg_D, Deg_I, Deg_C |
| 8 | Impacto | Criticidad + Degradación | IMPACTO |
| 9 | Riesgo por Amenaza | Frecuencia + Impacto | RIESGO |
| 10 | Mapa de Riesgos | Todos los riesgos | Visualización 2D |
| 11 | Riesgo por Activo | Promedio de riesgos | Actual, Objetivo, Límite |
| 12 | Salvaguardas | Riesgos a tratar | Controles ISO 27002 |
| 13 | Reevaluación | Controles implementados | Nueva medición |

---

## 3. CONCEPTOS FUNDAMENTALES

### 3.1 Dimensiones de Seguridad (DIC)

Las tres dimensiones fundamentales de la seguridad de la información:

#### 📦 DISPONIBILIDAD (D)
> **Definición:** Garantía de que los usuarios autorizados tienen acceso a la información y a los activos asociados cuando lo requieren.

| Nivel | Valor | Criterio |
|-------|-------|----------|
| Alta | 3 | Inaccesibilidad de 1 hora impide operaciones |
| Media | 2 | Inaccesibilidad de 1 jornada impide operaciones |
| Baja | 1 | Inaccesibilidad de 1 semana causa perjuicio menor |
| Nula | 0 | Inaccesibilidad no afecta operaciones |

#### 🔒 INTEGRIDAD (I)
> **Definición:** Mantenimiento de la exactitud y completitud de la información y sus métodos de procesamiento.

| Nivel | Valor | Criterio |
|-------|-------|----------|
| Alta | 3 | Modificación no autorizada es irreparable |
| Media | 2 | Modificación difícil de reparar, perjuicio significativo |
| Baja | 1 | Modificación reparable, perjuicio menor |
| Nula | 0 | Modificación sin consecuencias |

#### 🔐 CONFIDENCIALIDAD (C)
> **Definición:** Garantía de que la información es accesible solo a quienes están autorizados.

| Nivel | Valor | Criterio |
|-------|-------|----------|
| Alta | 3 | Solo grupo reducido, divulgación = perjuicio grave |
| Media | 2 | Solo quienes necesitan para su trabajo |
| Baja | 1 | Todos los empleados de la organización |
| Nula | 0 | Información pública |

### 3.2 Criticidad

> **Definición:** Valor que representa la importancia máxima del activo considerando las tres dimensiones de seguridad.

```
CRITICIDAD = MAX(Disponibilidad, Integridad, Confidencialidad)
```

**Justificación:** Se usa el máximo porque basta que una dimensión sea crítica para que el activo requiera protección especial.

| Criticidad | Valor | Interpretación |
|------------|-------|----------------|
| Crítica | 3 | Activo esencial para la organización |
| Alta | 2 | Activo importante |
| Baja | 1 | Activo de soporte |
| Nula | 0 | Activo prescindible |

### 3.3 Vulnerabilidad

> **Definición:** Debilidad de un activo o grupo de activos que puede ser explotada por una o más amenazas.

**Ejemplos:**
- Falta de protección contra incendios
- Ausencia de respaldos
- Sin control de acceso físico
- Falta de capacitación del personal
- Componentes obsoletos

### 3.4 Amenaza

> **Definición:** Causa potencial de un incidente no deseado, que puede resultar en daño a un sistema u organización.

**Tipos de Amenazas (MAGERIT):**

| Código | Tipo | Descripción | Ejemplos |
|--------|------|-------------|----------|
| **N** | Naturales | Desastres naturales | Terremotos, inundaciones, incendios |
| **I** | Industriales | Fallos de infraestructura | Cortes eléctricos, fallos de climatización |
| **E** | Errores | Fallos no intencionados | Errores de usuarios, configuración incorrecta |
| **A** | Ataques | Acciones deliberadas | Malware, acceso no autorizado, DoS |

### 3.5 Degradación

> **Definición:** Porcentaje de daño que una amenaza causa a cada dimensión de seguridad si se materializa.

**Escala:**
```
0.0 = Sin degradación (0%)
0.1 - 0.3 = Degradación baja (10-30%)
0.4 - 0.6 = Degradación media (40-60%)
0.7 - 0.9 = Degradación alta (70-90%)
1.0 = Degradación total (100%)
```

**Ejemplo:**
| Amenaza | Deg_D | Deg_I | Deg_C |
|---------|-------|-------|-------|
| Incendio | 1.0 | 0.8 | 0.2 |
| Malware | 0.5 | 0.7 | 0.9 |
| Error usuario | 0.3 | 0.5 | 0.2 |

### 3.6 Impacto

> **Definición:** Consecuencia que produce la materialización de una amenaza sobre un activo.

```
IMPACTO = CRITICIDAD × MAX(Degradación_D, Degradación_I, Degradación_C)
```

**Justificación:**
- Se multiplica por CRITICIDAD porque el mismo daño es más grave en un activo crítico
- Se usa MAX porque el peor escenario (dimensión más degradada) determina el impacto

### 3.7 Frecuencia / Probabilidad

> **Definición:** Tasa de ocurrencia esperada de la amenaza en un período determinado.

| Nivel | Valor | Descripción |
|-------|-------|-------------|
| Muy Alta | 3.0 | A diario |
| Alta | 2.0 | Mensualmente |
| Media | 1.0 | Anualmente |
| Baja | 0.1 | Cada varios años |

### 3.8 Riesgo

> **Definición:** Posibilidad de que una amenaza concreta explote una vulnerabilidad para causar daño.

```
RIESGO = FRECUENCIA × IMPACTO
```

**Tipos de Riesgo:**

| Tipo | Definición | Fórmula |
|------|------------|---------|
| **Riesgo por Amenaza** | Riesgo de un par (activo, amenaza) específico | F × I |
| **Riesgo por Activo** | Riesgo consolidado del activo | PROMEDIO(riesgos) |
| **Riesgo Inherente** | Riesgo sin considerar controles | F × I (inicial) |
| **Riesgo Residual** | Riesgo después de aplicar controles | Riesgo × (1 - eficacia) |
| **Riesgo Objetivo** | Meta de riesgo a alcanzar | Riesgo_Actual × 0.5 |

### 3.9 Límite de Riesgo

> **Definición:** Umbral máximo de riesgo aceptable definido por la organización.

**Decisión basada en límite:**
```
SI Riesgo_Actual > Límite ENTONCES → Tratamiento Urgente
SI Riesgo_Actual ≤ Límite ENTONCES → Aceptable (monitorear)
```

### 3.10 Salvaguarda / Control

> **Definición:** Procedimiento o mecanismo tecnológico que reduce el riesgo.

**Efectos de una salvaguarda:**
1. **Reduce probabilidad:** Hace menos probable la materialización
2. **Reduce impacto:** Limita el daño si se materializa
3. **Ambos:** Combinación de los anteriores

---

## 4. FÓRMULAS DEL MODELO

### 4.1 Fórmulas Principales

```python
# 1. Criticidad del activo
CRITICIDAD = MAX(D, I, C)

# 2. Impacto de una amenaza
IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)

# 3. Riesgo por amenaza
RIESGO_AMENAZA = FRECUENCIA × IMPACTO

# 4. Riesgo agregado por activo
RIESGO_ACTIVO = PROMEDIO(RIESGO_AMENAZA₁, RIESGO_AMENAZA₂, ..., RIESGO_AMENAZAₙ)

# 5. Riesgo objetivo
RIESGO_OBJETIVO = RIESGO_ACTIVO × 0.5

# 6. Riesgo residual (después de controles)
RIESGO_RESIDUAL = RIESGO_INHERENTE × (1 - EFICACIA_CONTROLES)

# 7. Porcentaje de reducción
REDUCCION = ((RIESGO_INICIAL - RIESGO_ACTUAL) / RIESGO_INICIAL) × 100
```

### 4.2 Ejemplo de Cálculo Completo

**Activo:** Servidor de Base de Datos  
**Valoración:** D=3, I=3, C=2

```
Paso 1: CRITICIDAD = MAX(3, 3, 2) = 3

Amenaza: "Malware"
- Degradación: Deg_D=0.8, Deg_I=0.9, Deg_C=0.5
- Frecuencia: 2 (mensual)

Paso 2: IMPACTO = 3 × MAX(0.8, 0.9, 0.5) = 3 × 0.9 = 2.7

Paso 3: RIESGO = 2 × 2.7 = 5.4

Si hay 3 amenazas con riesgos: 5.4, 3.2, 4.0

Paso 4: RIESGO_ACTIVO = (5.4 + 3.2 + 4.0) / 3 = 4.2

Paso 5: RIESGO_OBJETIVO = 4.2 × 0.5 = 2.1

Límite organizacional = 7
Como 4.2 < 7 → Activo dentro del umbral aceptable
Pero debe reducirse a 2.1 con salvaguardas
```

---

## 5. CATÁLOGOS DE REFERENCIA

### 5.1 Catálogo de Amenazas MAGERIT

El catálogo MAGERIT v3 clasifica las amenazas en categorías:

| Categoría | Código | Ejemplos |
|-----------|--------|----------|
| **Desastres Naturales** | N.* | N.1 Fuego, N.2 Inundación, N.3 Terremoto |
| **De Origen Industrial** | I.* | I.1 Corte eléctrico, I.2 Fallo climatización |
| **Errores y Fallos** | E.* | E.1 Errores usuarios, E.2 Errores admin |
| **Ataques Intencionados** | A.* | A.5 Suplantación, A.6 Abuso privilegios, A.11 Acceso no autorizado |

### 5.2 Catálogo de Controles ISO 27002:2022

La nueva estructura de ISO 27002:2022 organiza 93 controles en 4 categorías:

| Categoría | Código | Cantidad | Descripción |
|-----------|--------|----------|-------------|
| **Organizacionales** | 5.x | 37 | Políticas, roles, gestión de activos |
| **De Personas** | 6.x | 8 | RRHH, capacitación, responsabilidades |
| **Físicos** | 7.x | 14 | Perímetros, equipos, servicios |
| **Tecnológicos** | 8.x | 34 | Endpoints, redes, desarrollo seguro |

### 5.3 Mapeo Amenaza → Control

| Amenaza | Controles Recomendados |
|---------|------------------------|
| A.5 Suplantación identidad | 5.15, 5.16, 8.5 |
| A.6 Abuso privilegios | 5.15, 5.17, 8.2, 8.4 |
| A.8 Difusión malware | 8.7, 8.8, 8.23 |
| A.11 Acceso no autorizado | 5.15, 7.2, 7.7, 8.5 |
| A.24 Denegación servicio | 8.6, 8.20, 8.21 |
| E.1 Errores usuarios | 5.10, 6.3 |
| E.2 Errores admin | 6.3, 8.2, 8.9 |

---

## 6. CICLO DE REEVALUACIÓN

### 6.1 Concepto de Reevaluación

> **Definición:** Proceso de evaluar nuevamente los riesgos de un activo para medir la efectividad de los controles implementados y demostrar mejora.

### 6.2 Flujo de Reevaluación

```
┌─────────────────────────────────────────────────────────────┐
│                   CICLO DE REEVALUACIÓN                      │
└─────────────────────────────────────────────────────────────┘

   Evaluación Original (Ciclo 0)
            │
            ▼
   ┌─────────────────────┐
   │ Riesgo Inherente    │ ← Medición inicial
   │ (sin controles)     │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Implementar         │
   │ Salvaguardas        │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Reevaluación        │ ← Ciclo 1
   │ (Ciclo 1)           │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Comparar con        │
   │ ciclo anterior      │
   │                     │
   │ ¿Riesgo bajó?       │
   └──────────┬──────────┘
              │
       ┌──────┴──────┐
       ▼             ▼
   ┌───────┐     ┌───────┐
   │  SÍ   │     │  NO   │
   └───┬───┘     └───┬───┘
       │             │
       ▼             ▼
   Evidencia     Revisar
   de mejora     controles
       │             │
       └──────┬──────┘
              │
              ▼
        Siguiente ciclo
```

### 6.3 Frecuencia Recomendada

| Tipo de Activo | Frecuencia |
|----------------|------------|
| Crítico (Criticidad = 3) | Trimestral |
| Alto (Criticidad = 2) | Semestral |
| Bajo (Criticidad = 1) | Anual |

### 6.4 Métricas de Mejora

```python
# Reducción de riesgo entre ciclos
REDUCCION = ((Riesgo_Ciclo_N-1 - Riesgo_Ciclo_N) / Riesgo_Ciclo_N-1) × 100

# Cumplimiento del objetivo
CUMPLIMIENTO = (Riesgo_Objetivo / Riesgo_Actual) × 100

# Efectividad de controles
EFECTIVIDAD = ((Riesgo_Inherente - Riesgo_Residual) / Riesgo_Inherente) × 100
```

---

## 7. INDICADORES DE MADUREZ

### 7.1 Modelo de Madurez de Ciberseguridad

El sistema mide la madurez en **5 dominios**:

| Dominio | Descripción |
|---------|-------------|
| **Gobierno** | Políticas, roles, compromiso directivo |
| **Identificación** | Inventario, clasificación, valoración |
| **Protección** | Controles preventivos implementados |
| **Detección** | Monitoreo, alertas, análisis |
| **Respuesta** | Incidentes, recuperación, mejora |

### 7.2 Niveles de Madurez

| Nivel | Nombre | % | Descripción |
|-------|--------|---|-------------|
| 1 | Inicial | 0-20% | Procesos ad-hoc, sin documentar |
| 2 | Repetible | 21-40% | Procesos básicos documentados |
| 3 | Definido | 41-60% | Procesos estandarizados |
| 4 | Gestionado | 61-80% | Procesos medidos y controlados |
| 5 | Optimizado | 81-100% | Mejora continua implementada |

### 7.3 Relación Madurez - Riesgo

```
A mayor madurez → Menor riesgo residual
A menor madurez → Mayor riesgo residual
```

| Madurez | Reducción esperada de riesgo |
|---------|------------------------------|
| Nivel 1 | 0-10% |
| Nivel 2 | 10-25% |
| Nivel 3 | 25-40% |
| Nivel 4 | 40-60% |
| Nivel 5 | 60-80% |

---

## 8. NIVELES DE RIESGO

### 8.1 Clasificación de Riesgo

| Nivel | Rango | Color | Tratamiento |
|-------|-------|-------|-------------|
| **CRÍTICO** | ≥ 20 | 🔴 Rojo | Acción inmediata obligatoria |
| **ALTO** | 15-19 | 🟠 Naranja | Plan de tratamiento urgente |
| **MEDIO** | 9-14 | 🟡 Amarillo | Tratamiento planificado |
| **BAJO** | 4-8 | 🟢 Verde | Aceptar con monitoreo |
| **MUY BAJO** | < 4 | 🔵 Azul | Aceptar |

### 8.2 Matriz de Riesgo (Impacto vs Frecuencia)

```
              │         IMPACTO
              │   1    2    3    4    5
         ─────┼────────────────────────
           5  │   5   10   15   20   25  ← CRÍTICO
    F      4  │   4    8   12   16   20
    R      3  │   3    6    9   12   15
    E      2  │   2    4    6    8   10
    C      1  │   1    2    3    4    5   ← MUY BAJO
```

### 8.3 Decisiones por Nivel

| Nivel | Decisión | Responsable | Plazo |
|-------|----------|-------------|-------|
| CRÍTICO | Escalar a dirección | CISO/CIO | Inmediato |
| ALTO | Plan de acción | Gerente TI | 1 semana |
| MEDIO | Incluir en roadmap | Líder técnico | 1 mes |
| BAJO | Monitorear | Analista | Trimestral |
| MUY BAJO | Aceptar | Documentar | - |

---

## 9. ESTRATEGIAS DE TRATAMIENTO

### 9.1 Opciones de Tratamiento

| Estrategia | Descripción | Cuándo usar |
|------------|-------------|-------------|
| **Mitigar** | Implementar controles para reducir | Riesgo > Límite, costo viable |
| **Transferir** | Trasladar a tercero (seguro, proveedor) | Riesgo alto, mitigación costosa |
| **Aceptar** | Asumir el riesgo conscientemente | Riesgo ≤ Límite, costo > beneficio |
| **Evitar** | Eliminar la actividad que genera riesgo | Riesgo inaceptable, sin mitigación |

### 9.2 Selección de Controles

**Criterios de selección:**
1. **Efectividad:** ¿Reduce significativamente el riesgo?
2. **Costo:** ¿Es proporcional al riesgo?
3. **Viabilidad:** ¿Se puede implementar?
4. **Compatibilidad:** ¿Se integra con controles existentes?

### 9.3 Priorización de Tratamiento

```
PRIORIDAD = (Nivel_Riesgo × Criticidad_Activo) / Costo_Implementación
```

| Prioridad | Acción |
|-----------|--------|
| Alta | Implementar primero |
| Media | Incluir en plan trimestral |
| Baja | Incluir en plan anual |

---

## 10. GLOSARIO COMPLETO

| Término | Definición |
|---------|------------|
| **Activo** | Elemento de valor para la organización que requiere protección |
| **Amenaza** | Causa potencial de un incidente de seguridad |
| **Análisis de Riesgos** | Proceso de identificar y evaluar riesgos |
| **Catálogo** | Lista estructurada de elementos (amenazas, controles) |
| **Ciclo** | Período entre evaluaciones consecutivas |
| **Confidencialidad** | Propiedad de que la información no se divulga a no autorizados |
| **Control** | Medida que modifica el riesgo (sinónimo: salvaguarda) |
| **Criticidad** | Importancia máxima del activo (MAX de D, I, C) |
| **Degradación** | Porcentaje de daño a cada dimensión por una amenaza |
| **Disponibilidad** | Propiedad de ser accesible cuando se necesita |
| **Evaluación** | Proceso completo de análisis de riesgos de un conjunto de activos |
| **Frecuencia** | Tasa de ocurrencia esperada de una amenaza |
| **Gestión de Riesgos** | Proceso coordinado de identificar, analizar y tratar riesgos |
| **Impacto** | Consecuencia de la materialización de una amenaza |
| **Integridad** | Propiedad de exactitud y completitud de la información |
| **ISO 27002** | Estándar internacional de controles de seguridad |
| **Límite de Riesgo** | Umbral máximo aceptable de riesgo |
| **MAGERIT** | Metodología de Análisis y Gestión de Riesgos de los SI (España) |
| **Madurez** | Nivel de desarrollo de las prácticas de seguridad |
| **Mitigar** | Reducir el riesgo mediante controles |
| **Reevaluación** | Nueva evaluación para medir cambios |
| **Riesgo** | Combinación de probabilidad e impacto de una amenaza |
| **Riesgo Inherente** | Riesgo sin considerar controles existentes |
| **Riesgo Objetivo** | Meta de riesgo a alcanzar (típicamente 50% del actual) |
| **Riesgo Residual** | Riesgo que permanece después de aplicar controles |
| **Salvaguarda** | Mecanismo para reducir el riesgo (sinónimo: control) |
| **Tratamiento** | Acción para modificar el riesgo |
| **Valoración** | Asignación de valores D, I, C a un activo |
| **Vulnerabilidad** | Debilidad que puede ser explotada por una amenaza |

---

## 📌 PRINCIPIOS DE USO DE ESTE DOCUMENTO

1. **Este documento es la referencia única** para la comprensión conceptual del modelo
2. **No debe modificarse** sin revisión del equipo de arquitectura
3. **Todo cambio de código** debe alinearse con este marco teórico
4. **Las fórmulas son inmutables** salvo decisión formal de cambio metodológico
5. **Los catálogos pueden extenderse** pero no reducirse

---

**Documento generado:** 27/01/2026  
**Estado:** Marco Teórico Oficial  
**Versión:** 1.0

# PROYECTO TITA - Documentación Completa del Sistema

**Sistema de Evaluación de Riesgos MAGERIT/ISO 27002**  
*Versión: 3.0 | Última actualización: 25 Enero 2026*

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Objetivo del Proyecto](#2-objetivo-del-proyecto)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Arquitectura del Sistema](#4-arquitectura-del-sistema)
5. [Modelo de Datos](#5-modelo-de-datos)
6. [Flujos de Funcionamiento](#6-flujos-de-funcionamiento)
7. [Módulos y Funcionalidades](#7-módulos-y-funcionalidades)
8. [Tabs de la Aplicación](#8-tabs-de-la-aplicación)
9. [Banco de Preguntas](#9-banco-de-preguntas)
10. [Integración con IA](#10-integración-con-ia)
11. [IA Avanzada](#11-ia-avanzada)
12. [Matriz MAGERIT](#12-matriz-magerit)
13. [Catálogos y Estándares](#13-catálogos-y-estándares)
14. [Estructura de Archivos](#14-estructura-de-archivos)
15. [API de Servicios](#15-api-de-servicios)
16. [Guía de Desarrollo](#16-guía-de-desarrollo)
17. [Reglas de Negocio Críticas](#17-reglas-de-negocio-críticas)

---

## 1. Resumen Ejecutivo

**Proyecto TITA** es un sistema web de gestión de auditoría de activos críticos de TI que permite realizar evaluaciones de riesgos siguiendo:

- **Metodología MAGERIT v3** (Metodología de Análisis y Gestión de Riesgos de los Sistemas de Información)
- **Estándar ISO/IEC 27002:2022** (93 controles de seguridad organizados en 4 dominios)

### Características Principales:
- ✅ Evaluación automatizada de riesgos con IA (Ollama Local)
- ✅ Cuestionarios dinámicos por tipo de activo
- ✅ Matriz MAGERIT completa (Activo-Amenaza)
- ✅ Dashboards interactivos
- ✅ Cálculo de nivel de madurez (CMMI 1-5)
- ✅ Exportación a Excel y Power BI
- ✅ 100% offline (no requiere conexión a internet)

---

## 2. Objetivo del Proyecto

### 2.1 Objetivo General
Desarrollar una herramienta que automatice y estandarice el proceso de evaluación de riesgos de activos TI críticos, integrando metodologías reconocidas (MAGERIT, ISO 27002) con inteligencia artificial local.

### 2.2 Objetivos Específicos

| # | Objetivo | Estado |
|---|----------|--------|
| 1 | Gestión de evaluaciones como contenedor principal | ✅ Implementado |
| 2 | Inventario de activos (servidores físicos/virtuales) | ✅ Implementado |
| 3 | Cuestionarios dinámicos por tipo de activo | ✅ Implementado |
| 4 | Cálculo automático de impacto DIC | ✅ Implementado |
| 5 | Evaluación de riesgo con IA (Ollama) | ✅ Implementado |
| 6 | Dashboards interactivos | ✅ Implementado |
| 7 | Exportación a Excel para reportes | ✅ Implementado |
| 8 | Re-evaluaciones comparativas | ✅ Implementado |
| 9 | Cálculo de nivel de madurez (CMMI 1-5) | ✅ Implementado |
| 10 | Comparativa de madurez entre evaluaciones | ✅ Implementado |
| 11 | Carga masiva de activos (JSON/Excel) | ✅ Implementado |
| 12 | IA Avanzada (5 funcionalidades) | ✅ Implementado |
| 13 | Persistencia de resultados IA | ✅ Implementado |
| 14 | Matriz MAGERIT v3 completa | ✅ Implementado |
| 15 | Validación IA de resultados | ✅ Implementado |

### 2.3 Alcance
- **Tipos de activos soportados**: Servidores Físicos, Servidores Virtuales
- **Dimensiones de impacto**: Disponibilidad (D), Integridad (I), Confidencialidad (C)
- **Preguntas por activo**: 21 preguntas estandarizadas
- **Controles ISO 27002**: 93 controles en 4 dominios

---

## 3. Stack Tecnológico

### 3.1 Tecnologías Principales

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Frontend** | Streamlit | 1.31+ | Interfaz web interactiva |
| **Backend** | Python | 3.14 | Lógica de negocio |
| **Base de Datos** | SQLite | 3 | Persistencia (ACID-compliant) |
| **IA** | Ollama | Local | Análisis de riesgos con LLM |
| **Modelo LLM** | llama3.2:1b | 1B params | Modelo ligero y rápido |
| **Visualización** | Plotly | 5.18+ | Gráficos interactivos |
| **Datos** | Pandas | 2.1+ | Manipulación de datos |

### 3.2 Dependencias Python

```
streamlit>=1.31.0
pandas>=2.1.0
openpyxl>=3.1.0      # Exportación a Excel
plotly>=5.18.0       # Gráficos
requests>=2.31.0     # Comunicación con Ollama
```

### 3.3 Servicios Externos

| Servicio | URL | Propósito |
|----------|-----|-----------|
| Ollama API | http://localhost:11434 | LLM local para análisis IA |

---

## 4. Arquitectura del Sistema

### 4.1 Diagrama de Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE PRESENTACIÓN                        │
│                     (app_final.py - Streamlit)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 🏠 Evaluaciones │ 📦 Activos │ 📝 Cuestionarios │ 🤖 MAGERIT│ │
│  │ 📈 Dashboard │ 🧮 Matriz │ 🎯 Madurez │ 🧠 IA Avanzada     │ │
│  │ 🔄 Comparativas │ 🛡️ Validación IA                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE COMPONENTES UI                      │
│                        (components/)                            │
│  ┌──────────────────┐ ┌──────────────────┐ ┌─────────────────┐  │
│  │dashboard_magerit │ │ia_advanced_ui    │ │ia_validation_ui │  │
│  │• render_resumen  │ │• render_ia_ui    │ │• validar_result │  │
│  │• render_ranking  │ │• chatbot         │ │                 │  │
│  │• render_madurez  │ │• planes          │ │                 │  │
│  └──────────────────┘ └──────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE SERVICIOS                           │
│                        (services/)                              │
│  ┌──────────────────┐ ┌──────────────────┐ ┌─────────────────┐  │
│  │magerit_engine    │ │ia_advanced_      │ │maturity_service │  │
│  │• evaluar_activo  │ │service           │ │• calcular_      │  │
│  │• calcular_riesgo │ │• generar_plan    │ │  madurez        │  │
│  │• guardar_result  │ │• chatbot         │ │• get_controles  │  │
│  └──────────────────┘ │• resumen         │ └─────────────────┘  │
│  ┌──────────────────┐ │• prediccion      │ ┌─────────────────┐  │
│  │ollama_magerit_   │ │• priorizacion    │ │database_service │  │
│  │service           │ └──────────────────┘ │• read_table     │  │
│  │• analisis IA     │                      │• insert_rows    │  │
│  └──────────────────┘                      │• get_connection │  │
│                                            └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE PERSISTENCIA                        │
│                     (tita_database.db - SQLite)                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ EVALUACIONES │ INVENTARIO_ACTIVOS │ CUESTIONARIOS          │ │
│  │ RESPUESTAS │ IMPACTO_ACTIVOS │ RESULTADOS_MAGERIT          │ │
│  │ RESULTADOS_MADUREZ │ IA_RESULTADOS_AVANZADOS               │ │
│  │ CATALOGO_AMENAZAS_MAGERIT │ CATALOGO_CONTROLES_ISO27002    │ │
│  │ BANCO_PREGUNTAS_FISICAS │ BANCO_PREGUNTAS_VIRTUALES        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Flujo de Datos Principal

```
Usuario → Streamlit UI → Services → SQLite
                ↓
            Ollama (IA Local)
                ↓
         Resultados JSON
                ↓
         Almacenamiento SQLite
                ↓
         Visualización Dashboard
```

---

## 5. Modelo de Datos

### 5.1 Tablas Principales

#### EVALUACIONES
```sql
CREATE TABLE EVALUACIONES (
    ID_Evaluacion TEXT PRIMARY KEY,
    Nombre TEXT NOT NULL,
    Fecha TEXT,
    Estado TEXT DEFAULT 'Activa',
    Descripcion TEXT
)
```

#### INVENTARIO_ACTIVOS
```sql
CREATE TABLE INVENTARIO_ACTIVOS (
    ID_Activo TEXT PRIMARY KEY,
    ID_Evaluacion TEXT,
    Nombre_Activo TEXT NOT NULL,
    Tipo_Activo TEXT,           -- 'Servidor Físico' | 'Servidor Virtual'
    Ubicacion TEXT,
    Propietario TEXT,
    Tipo_Servicio TEXT,
    App_Critica TEXT,
    Estado TEXT DEFAULT 'Pendiente',
    Fecha_Creacion TEXT,
    FOREIGN KEY (ID_Evaluacion) REFERENCES EVALUACIONES(ID_Evaluacion)
)
```

#### RESULTADOS_MAGERIT
```sql
CREATE TABLE RESULTADOS_MAGERIT (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT,
    ID_Activo TEXT,
    Nombre_Activo TEXT,
    Impacto_D INTEGER,          -- 1-5
    Impacto_I INTEGER,          -- 1-5
    Impacto_C INTEGER,          -- 1-5
    Riesgo_Inherente REAL,
    Riesgo_Residual REAL,
    Nivel_Riesgo TEXT,          -- CRÍTICO, ALTO, MEDIO, BAJO, MUY BAJO
    Amenazas_JSON TEXT,         -- JSON array de amenazas
    Controles_JSON TEXT,        -- JSON array de controles
    Observaciones TEXT,
    Modelo_IA TEXT,
    Fecha_Evaluacion TEXT
)
```

#### RESULTADOS_MADUREZ
```sql
CREATE TABLE RESULTADOS_MADUREZ (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT UNIQUE,
    Puntuacion_Total REAL,      -- 0-100
    Nivel_Madurez INTEGER,      -- 1-5
    Nombre_Nivel TEXT,          -- Inicial, Básico, Definido, Gestionado, Optimizado
    Dominio_Organizacional REAL,
    Dominio_Personas REAL,
    Dominio_Fisico REAL,
    Dominio_Tecnologico REAL,
    Pct_Controles_Implementados REAL,
    Pct_Controles_Medidos REAL,
    Pct_Riesgos_Mitigados REAL,
    Pct_Activos_Evaluados REAL,
    Controles_Implementados INTEGER,
    Controles_Parciales INTEGER,
    Controles_No_Implementados INTEGER,
    Fecha_Calculo TEXT
)
```

#### IA_RESULTADOS_AVANZADOS
```sql
CREATE TABLE IA_RESULTADOS_AVANZADOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_evaluacion TEXT NOT NULL,
    tipo_resultado TEXT NOT NULL,  -- resumen, prediccion, priorizacion, planes
    datos_json TEXT NOT NULL,
    fecha_generacion TEXT NOT NULL,
    modelo_ia TEXT,
    UNIQUE(id_evaluacion, tipo_resultado)
)
```

### 5.2 Tablas de Catálogos

#### CATALOGO_AMENAZAS_MAGERIT
```sql
CREATE TABLE CATALOGO_AMENAZAS_MAGERIT (
    Cod_MAGERIT TEXT PRIMARY KEY,  -- N.1, I.5, E.2, A.24
    Categoria TEXT,                 -- Natural, Industrial, Error, Ataque
    Amenaza TEXT,
    Descripcion TEXT,
    "Dimension(D/I/C)" TEXT,
    "Severidad_Base(1-5)" INTEGER
)
```

#### CATALOGO_CONTROLES_ISO27002
```sql
CREATE TABLE CATALOGO_CONTROLES_ISO27002 (
    codigo TEXT PRIMARY KEY,        -- 5.1, 6.2, 7.3, 8.1
    nombre TEXT,
    dominio TEXT,                   -- organizacional, personas, fisico, tecnologico
    descripcion TEXT,
    objetivo TEXT
)
```

### 5.3 Estructura JSON de Amenazas

```json
{
    "codigo": "A.24",
    "amenaza": "Denegación de servicio",
    "tipo_amenaza": "Ataque deliberado",
    "dimension": "D",
    "probabilidad": 3,
    "impacto": 4,
    "riesgo_inherente": 12,
    "nivel_riesgo": "MEDIO",
    "riesgo_residual": 8.4,
    "tratamiento": "mitigar",
    "controles_existentes": ["8.6", "8.20"],
    "efectividad_controles": 0.3,
    "controles_recomendados": [
        {"codigo": "8.22", "nombre": "Segregación de redes", "prioridad": "ALTA"}
    ],
    "justificacion": "Servidor expuesto a internet sin redundancia"
}
```

---

## 6. Flujos de Funcionamiento

### 6.1 Flujo Principal de Evaluación

```
1. CREAR EVALUACIÓN
   └── Usuario crea evaluación con nombre/descripción
   
2. AGREGAR ACTIVOS
   └── Manual o carga masiva (Excel/JSON)
   └── Tipo: Físico o Virtual
   
3. RESPONDER CUESTIONARIOS
   └── 21 preguntas por activo
   └── Sistema calcula impacto DIC automáticamente
   
4. EVALUACIÓN MAGERIT CON IA
   └── Ollama analiza contexto del activo
   └── Identifica amenazas aplicables
   └── Calcula riesgos inherente y residual
   └── Recomienda controles ISO 27002
   └── Guarda en RESULTADOS_MAGERIT
   
5. VISUALIZAR RESULTADOS
   └── Dashboard con gráficos
   └── Matriz MAGERIT completa
   └── Nivel de madurez
   
6. EXPORTAR
   └── Excel con múltiples hojas
   └── CSV para Power BI
```

### 6.2 Flujo de Evaluación MAGERIT

```
┌─────────────────┐
│ Activo + Context│
│ (Cuestionario)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ollama AI       │
│ (llama3.2:1b)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│ RESPUESTA IA ESTRUCTURADA                       │
│ ┌─────────────────────────────────────────────┐ │
│ │ Impacto DIC + Justificación                 │ │
│ ├─────────────────────────────────────────────┤ │
│ │ 5-10 Amenazas MAGERIT identificadas         │ │
│ │  - Código, Probabilidad, Impacto            │ │
│ │  - Riesgo inherente = P × I                 │ │
│ │  - Controles existentes detectados          │ │
│ │  - Riesgo residual = RI × (1 - efectividad) │ │
│ │  - Controles recomendados ISO 27002         │ │
│ ├─────────────────────────────────────────────┤ │
│ │ Tratamiento: mitigar/aceptar/transferir     │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Guardar en      │
│ RESULTADOS_     │
│ MAGERIT         │
└─────────────────┘
```

---

## 7. Módulos y Funcionalidades

### 7.1 Servicios (services/)

| Servicio | Archivo | Funciones Principales |
|----------|---------|----------------------|
| **Database** | `database_service.py` | `read_table()`, `insert_rows()`, `get_connection()` |
| **MAGERIT Engine** | `magerit_engine.py` | `evaluar_activo_magerit()`, `guardar_resultado_magerit()` |
| **Ollama MAGERIT** | `ollama_magerit_service.py` | `analizar_activo_ia()` |
| **IA Avanzada** | `ia_advanced_service.py` | `generar_plan_tratamiento()`, `chatbot_magerit()`, `generar_resumen_ejecutivo()` |
| **Madurez** | `maturity_service.py` | `calcular_madurez_evaluacion()`, `get_controles_existentes_detallados()` |
| **Cuestionario** | `cuestionario_service.py` | `generar_cuestionario()`, `guardar_respuestas()` |
| **Activos** | `activo_service.py` | `crear_activo()`, `listar_activos()` |
| **Evaluación** | `evaluacion_service.py` | `crear_evaluacion()`, `get_evaluaciones()` |
| **Excel/Export** | `excel_service.py`, `export_service.py` | Exportación a Excel y Power BI |
| **Validación IA** | `ia_validation_service.py` | Validación de resultados IA |
| **Carga Masiva** | `carga_masiva_service.py` | Importación Excel/JSON |

### 7.2 Componentes UI (components/)

| Componente | Archivo | Propósito |
|------------|---------|-----------|
| **Dashboard MAGERIT** | `dashboard_magerit.py` | Visualizaciones de riesgos |
| **IA Avanzada UI** | `ia_advanced_ui.py` | Interfaz de funciones IA |
| **Validación IA UI** | `ia_validation_ui.py` | Interfaz de validación |
| **Carga Masiva UI** | `carga_masiva_ui.py` | Interfaz de importación |

---

## 8. Tabs de la Aplicación

### 8.1 Lista de Tabs (app_final.py)

| # | Tab | Icono | Descripción |
|---|-----|-------|-------------|
| 1 | Evaluaciones | 🏠 | Crear/seleccionar evaluaciones |
| 2 | Activos | 📦 | Inventario de activos TI |
| 3 | Cuestionarios | 📝 | Responder cuestionarios por activo |
| 4 | Evaluación MAGERIT | 🤖 | Ejecutar análisis IA por activo |
| 5 | Dashboard Riesgos | 📈 | Visualizaciones y métricas |
| 6 | Matriz MAGERIT | 🧮 | Tabla técnica Activo-Amenaza |
| 7 | Madurez | 🎯 | Nivel de madurez CMMI 1-5 |
| 8 | IA Avanzada | 🧠 | 5 funcionalidades de IA |
| 9 | Comparativas | 🔄 | Comparar evaluaciones |
| 10 | Validación IA | 🛡️ | Validar/ajustar resultados |

### 8.2 Detalle de Cada Tab

#### 🏠 Evaluaciones
- Crear nueva evaluación con nombre y descripción
- Listar evaluaciones existentes
- Seleccionar evaluación activa (obligatorio para otros tabs)
- Eliminar evaluaciones

#### 📦 Activos
- Agregar activos manualmente
- Carga masiva desde Excel/JSON
- Ver inventario de activos
- Editar/eliminar activos

#### 📝 Cuestionarios
- Seleccionar activo
- Responder 21 preguntas
- Ver respuestas guardadas
- Recalcular impacto DIC

#### 🤖 Evaluación MAGERIT
- Evaluar activo individual con IA
- Evaluar todos los activos pendientes
- Ver estado de evaluación por activo
- Forzar re-evaluación

#### 📈 Dashboard Riesgos
- Resumen ejecutivo con KPIs
- Gráfico comparativo inherente vs residual
- Ranking de activos por riesgo
- Mapa de calor de riesgos
- Distribución por tipo de amenaza

#### 🧮 Matriz MAGERIT
- Tabla técnica: cada fila = Activo-Amenaza
- Columnas: Evaluación, Activo, Tipo, Código Amenaza, Amenaza, Tipo Amenaza, D, I, C, Impacto, Probabilidad, Riesgo Inherente, Riesgo Residual, Nivel, Tratamiento, Controles
- Filtros por activo, nivel de riesgo
- Ordenar por riesgo
- Colores por activo para diferenciación visual
- Exportar a Excel/CSV
- Información metodológica MAGERIT v3

#### 🎯 Madurez
- Calcular nivel de madurez (1-5)
- Gauge visual de puntuación
- Radar de dominios ISO 27002
- Controles implementados vs parciales
- Métricas detalladas

#### 🧠 IA Avanzada
5 funcionalidades:
1. **Planes de Tratamiento**: Genera plan detallado por amenaza
2. **Chatbot MAGERIT**: Consultor interactivo
3. **Resumen Ejecutivo**: Informe para gerencia
4. **Predicción de Riesgo**: Proyección a futuro
5. **Priorización de Controles**: Ranking de implementación

#### 🔄 Comparativas
- Comparar dos evaluaciones
- Delta de riesgos
- Evolución de madurez
- Nuevos activos/amenazas

#### 🛡️ Validación IA
- Revisar resultados generados por IA
- Ajustar valores manualmente
- Aprobar/rechazar análisis

---

## 9. Banco de Preguntas

### 9.1 Estructura de Cuestionarios

| Bloque | Dimensión | # Preguntas | Peso |
|--------|-----------|-------------|------|
| BLQ-D | Disponibilidad | 7 | 1-3 |
| BLQ-I | Integridad | 7 | 1-3 |
| BLQ-C | Confidencialidad | 7 | 1-3 |
| **Total** | - | **21** | - |

### 9.2 Formato de Pregunta

```json
{
    "ID_Pregunta": "D-001",
    "Tipo_Activo": "Servidor Físico",
    "Bloque": "BLQ-D",
    "Dimension": "Disponibilidad",
    "Pregunta": "¿Qué tan crítico es el uptime del servidor?",
    "Opcion_1": "No crítico (puede estar caído días)",
    "Opcion_2": "Bajo (puede tolerar horas de caída)",
    "Opcion_3": "Medio (máximo 4 horas de caída)",
    "Opcion_4": "Alto (debe tener 99.9% uptime)",
    "Peso": 3
}
```

### 9.3 Cálculo de Impacto DIC

```python
# Por cada dimensión (D, I, C):
suma_ponderada = Σ (valor_respuesta × peso_pregunta)
max_posible = Σ (4 × peso_pregunta)  # 4 = máximo valor
porcentaje = suma_ponderada / max_posible

# Mapeo a escala 1-5:
if porcentaje >= 0.80: impacto = 5  # Muy Alto
elif porcentaje >= 0.60: impacto = 4  # Alto
elif porcentaje >= 0.40: impacto = 3  # Medio
elif porcentaje >= 0.20: impacto = 2  # Bajo
else: impacto = 1  # Muy Bajo
```

---

## 10. Integración con IA

### 10.1 Ollama Configuration

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_DEFAULT = "llama3.2:1b"
TIMEOUT = 60
```

### 10.2 Prompt de Evaluación MAGERIT

El prompt incluye:
- Contexto del activo (nombre, tipo, ubicación)
- Respuestas del cuestionario
- Catálogo de amenazas MAGERIT
- Catálogo de controles ISO 27002
- Instrucciones de formato JSON

### 10.3 Estructura de Respuesta IA

```json
{
    "impacto": {
        "disponibilidad": 4,
        "integridad": 3,
        "confidencialidad": 5,
        "justificacion_d": "...",
        "justificacion_i": "...",
        "justificacion_c": "..."
    },
    "amenazas": [
        {
            "codigo": "A.24",
            "amenaza": "Denegación de servicio",
            "tipo_amenaza": "Ataque deliberado",
            "dimension_afectada": "D",
            "probabilidad": 3,
            "impacto": 4,
            "riesgo_inherente": 12,
            "nivel_riesgo": "MEDIO",
            "justificacion": "...",
            "controles_existentes": ["8.6"],
            "efectividad_controles": 0.3,
            "riesgo_residual": 8.4,
            "controles_recomendados": [
                {"codigo": "8.22", "nombre": "...", "prioridad": "ALTA", "motivo": "..."}
            ],
            "tratamiento": "mitigar"
        }
    ],
    "observaciones": "..."
}
```

---

## 11. IA Avanzada

### 11.1 Funcionalidades

| # | Función | Descripción | Persistencia |
|---|---------|-------------|--------------|
| 1 | **Planes de Tratamiento** | Plan detallado por amenaza con pasos, responsables, plazos | ✅ Sí |
| 2 | **Chatbot MAGERIT** | Consultor interactivo para dudas | ❌ Sesión |
| 3 | **Resumen Ejecutivo** | Informe para gerencia con inversión estimada | ✅ Sí |
| 4 | **Predicción de Riesgo** | Proyección a 6-12 meses con escenarios | ✅ Sí |
| 5 | **Priorización de Controles** | Ranking por ROI y facilidad | ✅ Sí |

### 11.2 Persistencia de Resultados IA

Los resultados se guardan en tabla `IA_RESULTADOS_AVANZADOS`:
- **tipo_resultado**: "resumen", "prediccion", "priorizacion", "planes"
- **datos_json**: Resultado completo serializado
- Se puede regenerar o usar el guardado

---

## 12. Matriz MAGERIT

### 12.1 Estructura de Columnas

| Columna | Descripción |
|---------|-------------|
| Evaluación | Nombre de la evaluación |
| ID Activo | Identificador único |
| Activo | Nombre del activo |
| Tipo Activo | Físico / Virtual |
| Código Amenaza | Código MAGERIT (A.24, E.2, etc.) |
| Amenaza | Descripción de la amenaza |
| Tipo Amenaza | Categoría (Ataque, Error, etc.) |
| Dimensión | D, I, C afectada |
| D, I, C | Valores de impacto (1-5) |
| Impacto | Valor de impacto de la amenaza |
| Probabilidad | Frecuencia (1-5) |
| Riesgo Inherente | P × I |
| Riesgo Residual | RI × (1 - efectividad) |
| Nivel Riesgo | CRÍTICO/ALTO/MEDIO/BAJO |
| Tratamiento | Estrategia sugerida |
| Controles Existentes | Salvaguardas implementadas |
| Salvaguardas (Recomendadas) | Controles ISO 27002 sugeridos |
| Efectividad Controles | % de efectividad |
| Justificación | Razón de la amenaza |

### 12.2 Filtros Disponibles

- Por activo
- Por nivel de riesgo
- Ordenar por riesgo inherente/residual

### 12.3 Visualización

- Colores de fondo alternados por activo (10 colores pastel)
- Leyenda visual de activos
- Columna Nivel Riesgo coloreada por severidad

### 12.4 Exportación

- Excel con múltiples hojas (Matriz, Resumen, Amenazas)
- CSV para Power BI

---

## 13. Catálogos y Estándares

### 13.1 Amenazas MAGERIT

| Código | Categoría | Ejemplo |
|--------|-----------|---------|
| N.x | Naturales | N.1 Fuego, N.2 Inundación |
| I.x | Industriales | I.5 Fallo eléctrico, I.6 Climatización |
| E.x | Errores | E.1 Errores de usuarios, E.2 Errores de administrador |
| A.x | Ataques | A.7 Malware, A.24 DoS, A.11 Acceso no autorizado |

### 13.2 Controles ISO 27002:2022

| Dominio | Rango | Ejemplos |
|---------|-------|----------|
| Organizacional | 5.1 - 5.37 | Políticas, roles, gestión de activos |
| Personas | 6.1 - 6.8 | Selección, formación, disciplina |
| Físico | 7.1 - 7.14 | Perímetro, áreas seguras, equipos |
| Tecnológico | 8.1 - 8.34 | Endpoint, red, cifrado, desarrollo |

### 13.3 Criterios de Valoración

**Impacto (1-5):**
| Valor | Nivel | Descripción |
|-------|-------|-------------|
| 5 | Muy Alto | Daño muy grave, pérdida irreparable |
| 4 | Alto | Daño grave, recuperación costosa |
| 3 | Medio | Daño importante, recuperación posible |
| 2 | Bajo | Daño menor, recuperación sencilla |
| 1 | Muy Bajo | Daño insignificante |

**Probabilidad (1-5):**
| Valor | Frecuencia | Descripción |
|-------|------------|-------------|
| 5 | Muy frecuente | Diariamente o casi |
| 4 | Frecuente | Semanalmente |
| 3 | Normal | Mensualmente |
| 2 | Poco frecuente | Anualmente |
| 1 | Muy raro | Cada varios años |

**Niveles de Riesgo:**
| Nivel | Rango | Tratamiento |
|-------|-------|-------------|
| CRÍTICO | ≥20 | Acción inmediata |
| ALTO | 15-19 | Plan prioritario (<30 días) |
| MEDIO | 10-14 | Seguimiento y controles |
| BAJO | 5-9 | Controles básicos |
| MUY BAJO | <5 | Monitoreo rutinario |

---

## 14. Estructura de Archivos

```
c:\capston_riesgos\
├── app_final.py              # 🎯 Aplicación principal (2173 líneas)
├── tita_database.db          # Base de datos SQLite
├── requirements.txt          # Dependencias Python
├── CONTEXTO_PROYECTO_TITA.md # Este archivo
│
├── services/                 # Capa de servicios
│   ├── __init__.py
│   ├── database_service.py   # Acceso a SQLite
│   ├── magerit_engine.py     # Motor de evaluación MAGERIT
│   ├── ollama_magerit_service.py  # Integración Ollama
│   ├── ia_advanced_service.py     # IA Avanzada (5 funciones)
│   ├── maturity_service.py   # Cálculo de madurez
│   ├── cuestionario_service.py
│   ├── activo_service.py
│   ├── evaluacion_service.py
│   ├── excel_service.py
│   ├── export_service.py
│   ├── ia_validation_service.py
│   ├── carga_masiva_service.py
│   └── knowledge_base_service.py
│
├── components/               # Componentes UI
│   ├── __init__.py
│   ├── dashboard_magerit.py  # Visualizaciones dashboard
│   ├── ia_advanced_ui.py     # UI de IA Avanzada
│   ├── ia_validation_ui.py
│   ├── carga_masiva_ui.py
│   └── concentration_risk_ui.py
│
├── config/                   # Configuración
│   ├── settings.py           # Variables globales
│   └── auth_config.py
│
├── utils/                    # Utilidades
│   └── auth_helpers.py
│
├── docs/                     # Documentación adicional
│   └── FLUJO_IA_ARQUITECTURA.md
│
└── knowledge_base/           # Base de conocimiento
```

---

## 15. API de Servicios

### 15.1 database_service.py

```python
# Lectura
read_table(table_name: str) -> pd.DataFrame
query_rows(table_name: str, conditions: Dict) -> pd.DataFrame

# Escritura
insert_row(table_name: str, data: Dict)
insert_rows(table_name: str, rows: List[Dict])
update_row(table_name: str, updates: Dict, conditions: Dict)
delete_row(table_name: str, conditions: Dict)

# Conexión
get_connection() -> sqlite3.Connection  # Context manager
```

### 15.2 magerit_engine.py

```python
# Evaluación
evaluar_activo_magerit(eval_id: str, activo_id: str) -> ResultadoEvaluacionMagerit

# Persistencia
guardar_resultado_magerit(resultado: ResultadoEvaluacionMagerit) -> bool
get_resultado_magerit(eval_id: str, activo_id: str) -> Optional[Dict]
get_resumen_evaluacion(eval_id: str) -> pd.DataFrame
get_amenazas_activo(eval_id: str, activo_id: str) -> pd.DataFrame

# Cálculos
calcular_nivel_riesgo(valor: float) -> str
calcular_riesgo_residual(ri: float, efectividad: float) -> float
```

### 15.3 ia_advanced_service.py

```python
# Generación
generar_plan_tratamiento(eval_id: str, amenaza_codigo: str) -> Dict
chatbot_magerit(eval_id: str, pregunta: str) -> str
generar_resumen_ejecutivo(eval_id: str) -> Dict
predecir_riesgo_futuro(eval_id: str) -> Dict
priorizar_controles(eval_id: str) -> List[Dict]

# Persistencia
guardar_resultado_ia(eval_id: str, tipo: str, datos: dict, modelo: str)
cargar_resultado_ia(eval_id: str, tipo: str) -> Optional[dict]
eliminar_resultado_ia(eval_id: str, tipo: str)
```

### 15.4 maturity_service.py

```python
# Cálculo
calcular_madurez_evaluacion(eval_id: str) -> Optional[ResultadoMadurez]
get_madurez_evaluacion(eval_id: str) -> Optional[Dict]
guardar_madurez(resultado: ResultadoMadurez) -> bool

# Controles
get_controles_existentes_detallados(eval_id: str) -> Dict
analizar_controles_desde_respuestas(respuestas_df: pd.DataFrame) -> Dict
```

---

## 16. Guía de Desarrollo

### 16.1 Ejecutar la Aplicación

```bash
# Activar entorno virtual
cd c:\capston_riesgos
.venv\Scripts\activate

# Ejecutar Streamlit
streamlit run app_final.py --server.port 8510

# Acceder en navegador
http://localhost:8510
```

### 16.2 Requisitos Previos

1. **Ollama instalado y corriendo**:
   ```bash
   ollama serve
   ollama pull llama3.2:1b
   ```

2. **Python 3.14** con virtualenv

3. **Dependencias instaladas**:
   ```bash
   pip install -r requirements.txt
   ```

### 16.3 Inicializar Base de Datos

```python
from services.database_service import init_database
init_database()
```

### 16.4 Seedear Catálogos

```bash
python seed_catalogos_magerit.py
```

---

## 17. Reglas de Negocio Críticas

### 17.1 Jerarquía de Datos

```
EVALUACIÓN (contenedor principal)
    └── ACTIVOS (pertenecen a una evaluación)
        └── CUESTIONARIOS (preguntas para cada activo)
            └── RESPUESTAS (respuestas del usuario)
                └── IMPACTO_DIC (calculado de respuestas)
                    └── RESULTADOS_MAGERIT (evaluación IA)
```

### 17.2 Estados de Activos

| Estado | Descripción |
|--------|-------------|
| Pendiente | Sin cuestionario ni evaluación |
| Cuestionario Completo | Cuestionario respondido, sin MAGERIT |
| Evaluado | Evaluación MAGERIT completada |

### 17.3 Fórmulas de Cálculo

```python
# Riesgo Inherente
riesgo_inherente = probabilidad × impacto

# Efectividad de Controles (0.0 - 1.0)
efectividad = controles_implementados / controles_necesarios

# Riesgo Residual
riesgo_residual = riesgo_inherente × (1 - efectividad)

# Nivel de Madurez
puntuacion = (
    pct_controles_implementados × 0.30 +
    pct_controles_medidos × 0.25 +
    pct_riesgos_mitigados × 0.25 +
    pct_activos_evaluados × 0.20
)
```

### 17.4 Validaciones

1. **Evaluación obligatoria**: No se puede hacer nada sin seleccionar evaluación
2. **Cuestionario previo**: Se recomienda completar cuestionario antes de MAGERIT
3. **Ollama requerido**: Sin Ollama, no funciona la evaluación IA
4. **IDs únicos**: Evaluaciones, activos, respuestas tienen IDs únicos

---

## 18. Funcionalidad: Controles Implementados en Reevaluación

### 18.1 Ubicación
Tab **🔄 Comparativas** - Sección "Controles Implementados (Justificación de Mejora)"

### 18.2 Funcionalidad
Cuando se comparan dos evaluaciones (anterior vs actual), el sistema:

1. **Extrae controles recomendados** de la evaluación anterior (Eval1)
2. **Detecta controles implementados** en la evaluación actual (Eval2)
3. **Muestra tabla comparativa** con estado de implementación
4. **Calcula métricas** de cumplimiento (% implementados)
5. **Genera justificación automática** de reducción de riesgo

### 18.3 Lógica de Detección
```python
# Controles recomendados en Eval1
for amenaza in amenazas_eval1:
    controles_recomendados = amenaza["controles_recomendados"]
    
# Controles existentes en Eval2 (detectados por IA)
for amenaza in amenazas_eval2:
    controles_existentes = amenaza["controles_existentes"]

# Si un control recomendado en Eval1 aparece como existente en Eval2 → IMPLEMENTADO
```

### 18.4 Métricas Mostradas
- **Total Controles Recomendados**: Cantidad de controles sugeridos en Eval1
- **Implementados**: Controles que aparecen en Eval2
- **% Cumplimiento**: Porcentaje de implementación

### 18.5 Justificación Automática
Si hay controles implementados y el riesgo residual bajó:
> "Se implementaron X de Y controles recomendados (Z%), 
> lo cual contribuyó a reducir el riesgo residual promedio en N puntos."

---

## Changelog

### v3.0 (25 Enero 2026)
- ✅ Tab "🧮 Matriz MAGERIT" completo con vista técnica Activo-Amenaza
- ✅ Colores diferenciados por activo en matriz
- ✅ Columnas adicionales: Controles Existentes, Salvaguardas, Efectividad, Justificación
- ✅ Información metodológica MAGERIT v3 expandida
- ✅ Exportación Excel/CSV mejorada
- ✅ Fix: render_detalle_activo con nombres de campos correctos
- ✅ Fix: render_madurez_completo con soporte mayúsculas/minúsculas
- ✅ Reorganización de tabs (Validación IA al final)
- ✅ Eliminación de tab Concentración
- ✅ **NUEVO**: Sección "Controles Implementados" en tab Comparativas
- ✅ **NUEVO**: Justificación automática de reducción de riesgo en reevaluaciones

### v2.5 (25 Enero 2026)
- ✅ IA Avanzada con persistencia de resultados
- ✅ Fix de Resumen Ejecutivo (valores concretos en lugar de templates)

### v2.0 (Enero 2026)
- ✅ Motor MAGERIT completo con IA
- ✅ Dashboard de riesgos
- ✅ Nivel de madurez CMMI

### v1.0 (Diciembre 2025)
- ✅ Estructura base
- ✅ Gestión de evaluaciones y activos
- ✅ Cuestionarios

---

*Documento generado automáticamente - Proyecto TITA v3.0*

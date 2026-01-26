# PROYECTO TITA - Documentación Completa del Sistema

**Sistema de Evaluación de Riesgos MAGERIT/ISO 27002**  
*Versión: 2.5 | Última actualización: 25 Enero 2026*

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Objetivo del Proyecto](#2-objetivo-del-proyecto)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Arquitectura del Sistema](#4-arquitectura-del-sistema)
5. [Modelo de Datos](#5-modelo-de-datos)
6. [Flujos de Funcionamiento](#6-flujos-de-funcionamiento)
7. [Módulos y Funcionalidades](#7-módulos-y-funcionalidades)
8. [Banco de Preguntas](#8-banco-de-preguntas)
9. [Integración con IA](#9-integración-con-ia)
10. [IA Avanzada](#10-ia-avanzada)
11. [Catálogos y Estándares](#11-catálogos-y-estándares)
12. [Estructura de Archivos](#12-estructura-de-archivos)
13. [Guía de Desarrollo](#13-guía-de-desarrollo)
14. [Reglas de Negocio Críticas](#14-reglas-de-negocio-críticas)

---

## 1. Resumen Ejecutivo

**Proyecto TITA** es un sistema web de gestión de auditoría de activos críticos de TI que permite realizar evaluaciones de riesgos siguiendo:

- **Metodología MAGERIT** (Metodología de Análisis y Gestión de Riesgos de los Sistemas de Información)
- **Estándar ISO/IEC 27002:2022** (93 controles de seguridad)

El sistema permite a auditores y equipos de seguridad:
1. Crear evaluaciones de riesgo para activos de infraestructura
2. Aplicar cuestionarios estandarizados según tipo de activo
3. Obtener análisis de riesgo asistido por IA (Ollama)
4. Generar dashboards y reportes ejecutivos

---

## 2. Objetivo del Proyecto

### 2.1 Objetivo General
Desarrollar una herramienta que automatice y estandarice el proceso de evaluación de riesgos de activos TI críticos, integrando metodologías reconocidas (MAGERIT, ISO 27002) con inteligencia artificial.

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
| 12 | Riesgo por concentración (Host-VM) | ✅ Implementado |
| 13 | IA Avanzada (5 funcionalidades) | ✅ Implementado |
| 14 | Exportación para Power BI | ✅ Implementado |
| 15 | Persistencia de resultados IA | ✅ Implementado |

### 2.3 Alcance
- **Tipos de activos soportados**: Servidores Físicos, Servidores Virtuales
- **Dimensiones de impacto**: Disponibilidad (D), Integridad (I), Confidencialidad (C)
- **Preguntas por activo**: 21 preguntas estandarizadas

---

## 3. Stack Tecnológico

### 3.1 Tecnologías Principales

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Frontend** | Streamlit | 1.31+ | Interfaz web interactiva |
| **Backend** | Python | 3.14 | Lógica de negocio |
| **Base de Datos** | SQLite | 3 | Persistencia (ACID-compliant) |
| **IA** | Ollama | Local | Análisis de riesgos con LLM |
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
| Ollama | http://localhost:11434 | LLM local para análisis IA |

---

## 4. Arquitectura del Sistema

### 4.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STREAMLIT UI                                    │
│                             (app_final.py)                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │Evaluación│ │ Activos  │ │Cuestion. │ │ MAGERIT  │ │Dashboard │ │Madurez│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘ │
└───────┼────────────┼────────────┼────────────┼────────────┼───────────┼─────┘
        │            │            │            │            │           │
┌───────┴────────────┴────────────┴────────────┴────────────┴───────────┴─────┐
│                           CAPA DE SERVICIOS                                  │
│                            (services/)                                       │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌───────────────┐ │
│  │evaluacion_svc  │ │  activo_svc    │ │cuestionario_svc│ │ maturity_svc  │ │
│  └───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬───────┘ │
│          │                  │                  │                  │          │
│  ┌───────┴──────────────────┴──────────────────┴──────────────────┴───────┐ │
│  │                     database_service.py                                 │ │
│  │                        (SQLite CRUD)                                    │ │
│  └───────────────────────────┬─────────────────────────────────────────────┘ │
│                              │                                               │
│  ┌───────────────────────────┴─────────────────────────────────────────────┐ │
│  │                      ollama_magerit_service.py                          │ │
│  │                    (Comunicación con LLM + MAGERIT)                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
        │                                          │
        ▼                                          ▼
┌───────────────┐                         ┌───────────────┐
│ tita_database │                         │    Ollama     │
│    (.db)      │                         │   (LLM API)   │
└───────────────┘                         └───────────────┘
```

### 4.2 Estructura de Capas

| Capa | Directorio | Responsabilidad |
|------|------------|-----------------|
| **Presentación** | `app_final.py` | UI Streamlit, navegación, formularios |
| **Servicios** | `services/` | Lógica de negocio, validaciones |
| **Datos** | `services/database_service.py` | CRUD SQLite, transacciones |
| **IA** | `services/ollama_service.py` | Comunicación con Ollama |
| **Configuración** | `config/settings.py` | Constantes, headers, colores |

---

## 5. Modelo de Datos

### 5.1 Base de Datos SQLite

**Archivo**: `tita_database.db`

El sistema usa SQLite en lugar de Excel para garantizar:
- ✅ Transacciones ACID (no se corrompe)
- ✅ Concurrencia segura
- ✅ Mejor rendimiento

### 5.2 Tablas Principales

#### EVALUACIONES
```sql
CREATE TABLE EVALUACIONES (
    ID_Evaluacion TEXT PRIMARY KEY,  -- EVA-001, EVA-002...
    Nombre TEXT NOT NULL,
    Descripcion TEXT,
    Fecha_Creacion TEXT,
    Responsable TEXT,
    Estado TEXT DEFAULT 'En Progreso',  -- En Progreso, Cerrada
    Origen_Re_Evaluacion TEXT  -- ID de evaluación padre si es re-evaluación
);
```

#### INVENTARIO_ACTIVOS
```sql
CREATE TABLE INVENTARIO_ACTIVOS (
    ID_Activo TEXT PRIMARY KEY,      -- ACT-EVA-001-001
    ID_Evaluacion TEXT,              -- FK a EVALUACIONES
    Nombre_Activo TEXT NOT NULL,
    Tipo_Activo TEXT,                -- 'Servidor Físico' | 'Servidor Virtual'
    Ubicacion TEXT,
    Propietario TEXT,
    Tipo_Servicio TEXT,
    App_Critica TEXT,
    Estado TEXT DEFAULT 'Pendiente', -- Pendiente|Incompleto|Completo|Evaluado
    Fecha_Creacion TEXT
);
```

#### BANCO_PREGUNTAS_FISICAS / BANCO_PREGUNTAS_VIRTUALES
```sql
CREATE TABLE BANCO_PREGUNTAS_FISICAS (
    ID_Pregunta TEXT PRIMARY KEY,    -- PF-A01, PF-B02...
    Tipo_Activo TEXT,                -- 'Servidor Físico'
    Bloque TEXT,                     -- A-Impacto, B-Continuidad, etc.
    Dimension TEXT,                  -- D, I, C
    Pregunta TEXT,
    Opcion_1 TEXT,                   -- Valor 1 (menor riesgo)
    Opcion_2 TEXT,                   -- Valor 2
    Opcion_3 TEXT,                   -- Valor 3
    Opcion_4 TEXT,                   -- Valor 4 (mayor riesgo)
    Peso INTEGER                     -- 1-5 (importancia de la pregunta)
);
```

#### CUESTIONARIOS
```sql
CREATE TABLE CUESTIONARIOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT,
    ID_Activo TEXT,
    Fecha_Version TEXT,
    ID_Pregunta TEXT,
    Bloque TEXT,
    Dimension TEXT,
    Pregunta TEXT,
    Opcion_1 TEXT,
    Opcion_2 TEXT,
    Opcion_3 TEXT,
    Opcion_4 TEXT,
    Peso INTEGER
);
```

#### RESPUESTAS
```sql
CREATE TABLE RESPUESTAS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT,
    ID_Activo TEXT,
    Fecha_Cuestionario TEXT,
    ID_Pregunta TEXT,
    Bloque TEXT,
    Pregunta TEXT,
    Respuesta TEXT,              -- Texto de la opción seleccionada
    Valor_Numerico INTEGER,      -- 1, 2, 3 o 4
    Peso INTEGER,
    Dimension TEXT,              -- D, I, C
    Fecha TEXT
);
```

#### IMPACTO_ACTIVOS
```sql
CREATE TABLE IMPACTO_ACTIVOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT,
    ID_Activo TEXT,
    Fecha TEXT,
    Impacto_D INTEGER,           -- 1-5
    Impacto_I INTEGER,           -- 1-5
    Impacto_C INTEGER,           -- 1-5
    Justificacion_D TEXT,
    Justificacion_I TEXT,
    Justificacion_C TEXT,
    UNIQUE(ID_Evaluacion, ID_Activo)
);
```

#### ANALISIS_RIESGO
```sql
CREATE TABLE ANALISIS_RIESGO (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT,
    ID_Activo TEXT,
    Fecha TEXT,
    Tipo_Activo TEXT,
    Nombre_Activo TEXT,
    Probabilidad REAL,           -- 0.0 - 1.0
    Impacto REAL,                -- 1-5
    Riesgo_Inherente REAL,       -- Probabilidad * Impacto
    Nivel_Riesgo TEXT,           -- Bajo, Medio, Alto, Crítico
    Recomendaciones TEXT,        -- JSON con recomendaciones IA
    Estado TEXT,
    Modelo_IA TEXT               -- llama3, mistral, etc.
);
```

#### RESULTADOS_MADUREZ
```sql
CREATE TABLE RESULTADOS_MADUREZ (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT UNIQUE,
    Fecha TEXT,
    Nivel_Madurez INTEGER,       -- 1-5 (CMMI)
    Nombre_Nivel TEXT,           -- Inicial, Básico, Definido, Gestionado, Optimizado
    Porcentaje_Madurez REAL,     -- 0-100%
    Controles_Implementados INTEGER,
    Controles_Parciales INTEGER,
    Controles_No_Implementados INTEGER,
    Total_Controles_Evaluados INTEGER,
    Dominios_Evaluados TEXT,     -- JSON con detalle por dominio ISO 27002
    Activos_Evaluados INTEGER,
    Total_Activos INTEGER,
    Observaciones TEXT
);
```

#### IA_RESULTADOS_AVANZADOS (NUEVO v2.5)
```sql
CREATE TABLE IA_RESULTADOS_AVANZADOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_evaluacion TEXT NOT NULL,
    tipo_resultado TEXT NOT NULL,    -- resumen_ejecutivo, prediccion_riesgo, 
                                     -- priorizacion_controles, planes_tratamiento
    datos_json TEXT NOT NULL,        -- Resultado serializado en JSON
    fecha_generacion TEXT NOT NULL,
    modelo_ia TEXT,
    UNIQUE(id_evaluacion, tipo_resultado)
);
```

#### CATALOGO_AMENAZAS_MAGERIT
```sql
CREATE TABLE CATALOGO_AMENAZAS_MAGERIT (
    Cod_MAGERIT TEXT PRIMARY KEY,    -- N.1, I.5, E.1, A.11...
    Categoria TEXT,                   -- Desastres naturales, Industrial, Errores, Ataques
    Amenaza TEXT,
    Descripcion TEXT,
    "Dimension(D/I/C)" TEXT,
    "Severidad_Base(1-5)" INTEGER
);
```

#### CATALOGO_ISO27002_2022
```sql
CREATE TABLE CATALOGO_ISO27002_2022 (
    Control TEXT PRIMARY KEY,         -- 5.1, 8.9, etc.
    Nombre TEXT,
    Dominio TEXT,                     -- Organizacional, Personas, Físico, Tecnológico
    Descripcion TEXT
);
```

### 5.3 Diagrama Entidad-Relación

```
┌─────────────────┐       ┌───────────────────┐
│   EVALUACIONES  │──────<│ INVENTARIO_ACTIVOS│
│   (1)           │       │ (N)               │
└─────────────────┘       └─────────┬─────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
              │CUESTIONARIO│   │RESPUESTAS │   │ANALISIS   │
              │ (N)        │   │ (N)       │   │RIESGO (1) │
              └───────────┘   └───────────┘   └───────────┘
```

---

## 6. Flujos de Funcionamiento

### 6.1 Flujo Principal de Evaluación

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CREAR     │────▶│  REGISTRAR  │────▶│  COMPLETAR  │────▶│  EVALUAR    │
│ EVALUACIÓN  │     │   ACTIVOS   │     │CUESTIONARIO │     │   CON IA    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
  EVA-001 creada      ACT-001 creado     21 respuestas      Nivel: Alto
  Estado: Activa      Estado: Pendiente  Estado: Completo   Estado: Evaluado
```

### 6.2 Máquina de Estados del Activo

```
                          ┌─────────────────────────────────────┐
                          │          ESTADOS DE ACTIVO          │
                          └─────────────────────────────────────┘

┌───────────┐  Generar    ┌─────────────┐  Completar  ┌──────────┐  Evaluar IA ┌──────────┐
│ PENDIENTE │────────────▶│ INCOMPLETO  │────────────▶│ COMPLETO │────────────▶│ EVALUADO │
└───────────┘ cuestionario└─────────────┘  respuestas └──────────┘             └──────────┘
     │                          │                │                                   │
     │                          │                │      Modificar respuestas         │
     │                          │                │◀──────────────────────────────────┘
     │                          │                │      (invalida análisis IA)
     ▼                          ▼                ▼
   Activo                   Cuestionario     Todas las 21
   sin datos                parcialmente     preguntas
                            respondido       contestadas
```

### 6.3 Flujo del Cuestionario

```
┌──────────────────────────────────────────────────────────────┐
│                    FLUJO DE CUESTIONARIO                     │
└──────────────────────────────────────────────────────────────┘

1. Usuario selecciona activo
           │
           ▼
2. Sistema verifica tipo de activo
   ├── Servidor Físico → BANCO_PREGUNTAS_FISICAS
   └── Servidor Virtual → BANCO_PREGUNTAS_VIRTUALES
           │
           ▼
3. Se cargan las 21 preguntas del banco correspondiente
           │
           ▼
4. Usuario responde pregunta por pregunta
   • Cada pregunta tiene 4 opciones (valor 1-4)
   • El peso indica importancia (1-5)
   • La dimensión indica qué afecta (D/I/C)
           │
           ▼
5. Al completar todas → Estado = "Completo"
           │
           ▼
6. Usuario puede solicitar evaluación IA
```

### 6.4 Flujo de Evaluación IA

```
┌──────────────────────────────────────────────────────────────┐
│                    FLUJO DE EVALUACIÓN IA                    │
└──────────────────────────────────────────────────────────────┘

1. Activo en estado "Completo"
           │
           ▼
2. Sistema recopila:
   • Datos del activo (nombre, tipo, ubicación)
   • Respuestas del cuestionario (21)
   • Catálogo de amenazas MAGERIT
   • Controles ISO 27002
           │
           ▼
3. Se construye prompt para Ollama:
   "Analiza el siguiente activo... identifica riesgos..."
           │
           ▼
4. Ollama procesa y devuelve:
   • Probabilidad (0.0 - 1.0)
   • Impacto (1-5)
   • Nivel de riesgo (Bajo/Medio/Alto/Crítico)
   • Amenazas identificadas
   • Controles recomendados
           │
           ▼
5. Resultado se guarda en ANALISIS_RIESGO
           │
           ▼
6. Estado del activo → "Evaluado"
```

---

## 7. Módulos y Funcionalidades

### 7.1 Módulo de Evaluaciones

**Ubicación**: `services/evaluacion_service.py`

| Función | Descripción |
|---------|-------------|
| `crear_evaluacion(nombre, descripcion, responsable)` | Crea nueva evaluación, retorna ID |
| `get_evaluaciones()` | Lista todas las evaluaciones |
| `actualizar_estado_evaluacion(eval_id, estado)` | Cambia estado |
| `get_activos_por_evaluacion(eval_id)` | Lista activos de una evaluación |
| `get_estadisticas_evaluacion(eval_id)` | Conteos y métricas |

### 7.2 Módulo de Activos

**Ubicación**: `services/activo_service.py`

| Función | Descripción |
|---------|-------------|
| `crear_activo(eval_id, datos)` | Crea activo con validación de duplicados |
| `editar_activo(eval_id, activo_id, datos)` | Actualiza activo |
| `eliminar_activo(eval_id, activo_id)` | Elimina activo |
| `get_activo(eval_id, activo_id)` | Obtiene un activo específico |
| `validar_duplicado(eval_id, nombre, ubicacion, tipo)` | Previene duplicados |

### 7.3 Módulo de Cuestionarios

**Ubicación**: `services/cuestionario_service.py`

| Función | Descripción |
|---------|-------------|
| `get_banco_preguntas(tipo_activo)` | Obtiene las 21 preguntas según tipo |
| `generar_cuestionario(eval_id, activo)` | Asigna preguntas al activo |
| `get_cuestionario(eval_id, activo_id)` | Obtiene cuestionario del activo |
| `guardar_respuestas(eval_id, activo_id, respuestas)` | Guarda respuestas |
| `verificar_cuestionario_completo(eval_id, activo_id)` | Verifica si está completo |
| `invalidar_analisis_ia(eval_id, activo_id)` | Invalida IA si se modifican respuestas |

### 7.4 Módulo de Base de Datos

**Ubicación**: `services/database_service.py`

| Función | Descripción |
|---------|-------------|
| `init_database()` | Crea todas las tablas |
| `read_table(table_name)` | Lee tabla como DataFrame |
| `insert_rows(table_name, rows)` | Inserta múltiples filas |
| `update_row(table_name, updates, conditions)` | Actualiza con condiciones |
| `delete_row(table_name, conditions)` | Elimina con condiciones |
| `query_rows(table_name, conditions)` | Consulta con filtros |
| `exportar_a_excel(output_path)` | Exporta toda la BD a Excel |

### 7.5 Módulo de IA

**Ubicación**: `services/ollama_service.py`

| Función | Descripción |
|---------|-------------|
| `ollama_generate(prompt, model)` | Genera texto con Ollama |
| `ollama_analyze_risk(activo, respuestas)` | Analiza riesgo completo |
| `extract_json_array(text)` | Extrae JSON de respuesta |

### 7.6 Motor de Evaluación MAGERIT v3

**Ubicación**: `services/magerit_engine.py`

Este módulo implementa el cálculo completo de riesgos según la metodología MAGERIT v3:

| Función | Descripción |
|---------|-------------|
| `get_nivel_riesgo(valor)` | Clasifica valor 1-25 en nivel (MUY BAJO, BAJO, MEDIO, ALTO, CRÍTICO) |
| `get_color_riesgo(nivel)` | Retorna color hex para el nivel |
| `get_accion_riesgo(nivel)` | Retorna acción recomendada |
| `calcular_impacto_desde_respuestas(respuestas)` | Calcula ImpactoDIC desde cuestionario |
| `identificar_controles_existentes(respuestas)` | Extrae controles implementados, efectividad y detalle (3 valores) |
| `evaluar_activo_magerit(eval_id, activo_id, amenazas_ia, probabilidad_ia)` | **Función principal** - Ejecuta evaluación completa |
| `guardar_resultado_magerit(resultado)` | Persiste resultado en SQLite |
| `get_resultado_magerit(eval_id, activo_id)` | Recupera resultado guardado |
| `get_resumen_evaluacion(eval_id)` | Resumen de todos los activos |

**Dataclasses**:
- `ImpactoDIC`: Valoración de impacto en D/I/C con justificaciones
- `AmenazaIdentificada`: Amenaza con probabilidad, impacto, riesgo inherente/residual
- `ResultadoEvaluacionMagerit`: Resultado completo con todas las amenazas y controles

**Algoritmo de Cálculo**:
```
Riesgo Inherente = Probabilidad × Impacto (1-25)
Riesgo Residual = Riesgo Inherente × (1 - Cobertura × Efectividad × 0.8)
```

### 7.7 Servicio de Madurez de Ciberseguridad (NUEVO)

**Ubicación**: `services/maturity_service.py`

Módulo para calcular el nivel de madurez de ciberseguridad basado en modelo CMMI:

| Función | Descripción |
|---------|-------------|
| `calcular_madurez_evaluacion(eval_id)` | Calcula nivel de madurez (1-5, 0-100%) |
| `guardar_madurez(resultado)` | Persiste resultado en RESULTADOS_MADUREZ |
| `get_madurez_evaluacion(eval_id)` | Recupera madurez guardada |
| `comparar_madurez(eval_id_1, eval_id_2)` | Compara madurez entre dos evaluaciones |
| `get_controles_existentes_detallados(eval_id, activo_id)` | Detalle de controles por dominio |
| `analizar_controles_desde_respuestas(respuestas)` | Mapea respuestas a controles ISO 27002 |

**Niveles de Madurez (CMMI)**:

| Nivel | Nombre | Rango | Descripción |
|-------|--------|-------|-------------|
| 1 | Inicial | 0-20% | Procesos ad-hoc, no documentados |
| 2 | Básico | 20-40% | Procesos reactivos, parcialmente documentados |
| 3 | Definido | 40-60% | Procesos estandarizados y documentados |
| 4 | Gestionado | 60-80% | Procesos medidos y controlados |
| 5 | Optimizado | 80-100% | Mejora continua, procesos optimizados |

**Fórmula de Cálculo**:
```
Madurez = (Controles_Impl × 0.30) + (Controles_Medidos × 0.25) + 
          (Riesgos_Mitigados × 0.25) + (Activos_Evaluados × 0.20)
```

**Mapeo Preguntas → Controles ISO 27002**:
- 21 preguntas del cuestionario mapean a 31+ controles ISO 27002
- Clasificación: Implementado (valor ≤2), Parcial (valor=3), No Implementado (valor=4)

### 7.9 Servicio de IA para MAGERIT

**Ubicación**: `services/ollama_magerit_service.py`

Este módulo integra Ollama con validación contra catálogos oficiales:

| Función | Descripción |
|---------|-------------|
| `analizar_activo_con_ia(eval_id, activo_id, modelo)` | Analiza activo con IA y valida JSON |
| `verificar_ollama_disponible()` | Verifica conexión y lista modelos |
| `crear_evaluacion_manual(activo, amenazas, prob, obs)` | Crea evaluación sin IA |
| `get_catalogo_amenazas()` | Carga catálogo de 52 amenazas |
| `get_catalogo_controles()` | Carga catálogo de 93 controles |

**Validación JSON**:
- Solo acepta códigos de amenaza del catálogo MAGERIT (52)
- Solo acepta códigos de control del catálogo ISO 27002 (93)
- Valida dimensiones (D, I, C) y prioridades (Alta, Media, Baja)
- Corrige automáticamente códigos inválidos

### 7.10 Dashboard MAGERIT

**Ubicación**: `components/dashboard_magerit.py`

Componentes visuales Plotly para Streamlit:

| Función | Descripción |
|---------|-------------|
| `render_mapa_calor_riesgos(amenazas)` | Matriz 5×5 de probabilidad vs impacto |
| `render_ranking_activos(evaluaciones, por)` | Ranking por riesgo inherente/residual |
| `render_comparativo_riesgos(evaluaciones)` | Barras inherente vs residual |
| `render_distribucion_amenazas(amenazas)` | Pie chart por tipo y nivel |
| `render_cobertura_controles(evaluaciones)` | Top controles implementados |
| `render_resumen_ejecutivo(evaluaciones)` | Métricas globales |
| `render_detalle_activo(resultado)` | Detalle de un activo específico |
| `render_gauge_riesgo(valor)` | Gauge de nivel de riesgo |
| `render_gauge_madurez(porcentaje, nivel, nombre)` | **NUEVO**: Gauge de nivel de madurez |
| `render_radar_dominios(dominios)` | **NUEVO**: Radar chart de dominios ISO 27002 |
| `render_madurez_completo(resultado)` | **NUEVO**: Vista completa de madurez |
| `render_comparativa_madurez(comp)` | **NUEVO**: Comparación de madurez |
| `render_controles_existentes(controles)` | **NUEVO**: Lista de controles por dominio |

### 7.11 Servicio de Carga Masiva de Activos (NUEVO)

**Ubicación**: `services/carga_masiva_service.py`

Módulo para importar activos de forma masiva desde JSON o Excel:

| Función | Descripción |
|---------|-------------|
| `procesar_json(contenido, eval_id)` | Procesa archivo JSON con activos |
| `procesar_excel(archivo_bytes, eval_id)` | Procesa archivo Excel con activos |
| `generar_plantilla_json()` | Genera plantilla JSON de ejemplo |
| `generar_plantilla_excel()` | Genera DataFrame plantilla para Excel |
| `get_campos_info()` | Retorna información de campos para UI |
| `validar_activo(activo, fila)` | Valida un activo individual |
| `validar_tipo_activo(valor)` | Valida y normaliza tipo de activo |

**Dataclasses**:
- `ErrorValidacion`: Representa un error de validación con fila, campo y mensaje
- `ResultadoCarga`: Resultado completo con totales, insertados, duplicados y errores

**Decisión Arquitectónica**:
- **JSON (Principal)**: Validación estricta, sin macros, auditable, preparado para API
- **Excel (Compatibilidad)**: Para usuarios que prefieren hojas de cálculo

**Campos Requeridos**:
| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| nombre_activo | Nombre único del activo | Servidor BD Académica |
| tipo_activo | Servidor Físico o Virtual | Servidor Virtual |
| ubicacion | Ubicación física/lógica | DataCenter Principal |
| propietario | Área responsable | Departamento TI |
| tipo_servicio | Función principal | Base de Datos |

**Campos Opcionales**: app_critica, descripcion

**Validaciones**:
- Tipos de activo flexibles: "vm", "virtual", "fisico" → normalizados
- Detección de duplicados (internos y contra BD)
- Sanitización de caracteres peligrosos
- Hash SHA-256 del archivo para auditoría

### 7.12 UI Carga Masiva

**Ubicación**: `components/carga_masiva_ui.py`

| Función | Descripción |
|---------|-------------|
| `render_carga_masiva(eval_id, eval_nombre)` | Interfaz completa con tabs JSON/Excel/Ayuda |
| `render_carga_masiva_modal(eval_id, eval_nombre)` | Versión simplificada para modal |

### 7.13 Servicio de Riesgo por Concentración (NUEVO)

**Ubicación**: `services/concentration_risk_service.py`

Implementa el modelo híbrido de riesgo por dependencia entre hosts físicos y máquinas virtuales, basado en MAGERIT v3, Libro II, Capítulo 4 (Propagación de impacto).

| Fase | Dirección | Descripción |
|------|-----------|-------------|
| **Blast Radius** | VM → Host | El host hereda criticidad de sus VMs dependientes |
| **Herencia** | Host → VM | Las VMs heredan riesgo del host comprometido |

**Fórmulas implementadas:**

```
Blast_Radius = Σ(Criticidad_VMi × Peso_Dependencia_VMi)
Factor_Concentración = min(4, floor(Blast_Radius / 5))
Impacto_D_Host_Ajustado = min(5, Impacto_D_Host + Factor_Concentración)
Riesgo_VM_Final = max(Riesgo_VM_Propio, Riesgo_Host × 0.7)
```

**Dataclasses:**

| Clase | Propósito |
|-------|-----------|
| `DependenciaVM` | Representa la relación VM-Host |
| `ResultadoConcentracion` | Resultado del cálculo de blast radius |
| `RiesgoHeredado` | Riesgo heredado por una VM desde su host |

**Funciones principales:**

| Función | Descripción |
|---------|-------------|
| `init_concentration_tables()` | Crea columnas ID_Host, Tipo_Dependencia y tablas |
| `asignar_host_a_vm(eval_id, id_vm, id_host, tipo)` | Asigna dependencia VM→Host |
| `calcular_blast_radius(eval_id, id_host)` | Calcula blast radius de un host |
| `calcular_riesgo_heredado(eval_id, id_vm)` | Calcula riesgo heredado por VM |
| `calcular_concentracion_evaluacion(eval_id)` | Fase 1: Blast radius para todos los hosts |
| `calcular_herencia_evaluacion(eval_id)` | Fase 2: Herencia para todas las VMs |
| `get_hosts_spof(eval_id)` | Obtiene hosts identificados como SPOF |
| `get_ranking_hosts_blast_radius(eval_id)` | Ranking de hosts por blast radius |

**Tipos de dependencia:**

| Tipo | Peso | Descripción |
|------|------|-------------|
| `total` | 1.0 | VM depende completamente del host |
| `parcial` | 0.5 | VM puede migrar a otro host |
| `ninguna` | 0.0 | VM independiente (ej: multi-cloud) |

### 7.14 UI Riesgo por Concentración (NUEVO)

**Ubicación**: `components/concentration_risk_ui.py`

| Función | Descripción |
|---------|-------------|
| `render_asignacion_dependencias(eval_id)` | Panel para asignar VMs a hosts |
| `render_dashboard_concentracion(eval_id)` | Dashboard con métricas, alertas SPOF, gráficos |
| `render_concentracion_tab(eval_id)` | Tab completo (combina asignación + dashboard) |
| `render_concentracion_mini_card(eval_id)` | Tarjeta resumen para dashboard principal |

**Tablas de BD creadas:**

| Tabla | Propósito |
|-------|-----------|
| `RESULTADOS_CONCENTRACION` | Blast radius calculado por host |
| `RIESGO_HEREDADO` | Riesgo heredado por cada VM |

---

## 8. Banco de Preguntas

### 8.1 Estructura del Cuestionario

Cada tipo de activo tiene **21 preguntas** organizadas en **5 bloques**:

| Bloque | Código | Preguntas | Enfoque |
|--------|--------|-----------|---------|
| **A - Impacto** | A01-A05 | 5 | RTO, RPO, dependencias, criticidad |
| **B - Continuidad** | B01-B04 | 4 | Backups, failover, redundancia |
| **C - Controles** | C01-C05 | 5 | Acceso, parches, monitoreo, logs |
| **D - Ciberseguridad** | D01-D04 | 4 | Antimalware, cifrado, vulnerabilidades |
| **E - Exposición** | E01-E03 | 3 | Internet, acceso físico, dependencias |

### 8.2 Formato de Pregunta

Cada pregunta tiene:

```
ID_Pregunta: PF-A01 (Físico) o PV-A01 (Virtual)
Bloque: A-Impacto
Dimension: D, I o C
Pregunta: "¿Cuál es el tiempo máximo tolerable de interrupción (RTO)?"
Opcion_1: "Más de 72 horas" (Valor: 1 - menor riesgo)
Opcion_2: "24-72 horas" (Valor: 2)
Opcion_3: "4-24 horas" (Valor: 3)
Opcion_4: "Menos de 4 horas" (Valor: 4 - mayor riesgo)
Peso: 5 (importancia 1-5)
```

### 8.3 Ejemplo de Preguntas por Bloque

#### Bloque A - Impacto (Servidores Físicos)
| ID | Pregunta | Dimensión |
|----|----------|-----------|
| PF-A01 | ¿Cuál es el tiempo máximo tolerable de interrupción (RTO)? | D |
| PF-A02 | ¿Cuántos usuarios o procesos críticos dependen del servidor? | D |
| PF-A03 | ¿Qué nivel de pérdida de datos es tolerable (RPO)? | I |
| PF-A04 | ¿Qué tipo de información procesa este servidor? | C |
| PF-A05 | ¿Cuál sería el impacto financiero por hora de inactividad? | D |

#### Bloque B - Continuidad
| ID | Pregunta | Dimensión |
|----|----------|-----------|
| PF-B01 | ¿Existe un servidor de respaldo o failover configurado? | D |
| PF-B02 | ¿Con qué frecuencia se realizan copias de seguridad? | D |
| PF-B03 | ¿Se prueban regularmente las restauraciones de backup? | D |
| PF-B04 | ¿El servidor tiene fuente de alimentación redundante (UPS)? | D |

---

## 9. Integración con IA

### 9.1 Modelo de IA

- **Motor**: Ollama (LLM local)
- **Modelos soportados**: llama3, mistral, qwen, gemma
- **Puerto**: 11434 (por defecto)

### 9.2 Prompt de Análisis

El sistema construye un prompt estructurado:

```
Eres un experto en análisis de riesgos de TI siguiendo MAGERIT e ISO 27002.

ACTIVO A EVALUAR:
- Nombre: {nombre}
- Tipo: {tipo_activo}
- Ubicación: {ubicacion}
- Servicio: {tipo_servicio}

RESPUESTAS DEL CUESTIONARIO:
{respuestas_formateadas}

CATÁLOGO DE AMENAZAS MAGERIT:
{amenazas}

CONTROLES ISO 27002:
{controles}

TAREA:
1. Identifica las 3 principales amenazas para este activo
2. Calcula probabilidad (0.0-1.0) e impacto (1-5)
3. Determina nivel de riesgo (Bajo/Medio/Alto/Crítico)
4. Recomienda controles ISO 27002 específicos

Responde en formato JSON.
```

### 9.3 Respuesta Esperada

```json
{
  "probabilidad": 0.65,
  "impacto": 4.2,
  "nivel_riesgo": "Alto",
  "amenazas_identificadas": [
    {"codigo": "A.11", "amenaza": "Acceso no autorizado", "justificacion": "..."},
    {"codigo": "E.8", "amenaza": "Malware", "justificacion": "..."}
  ],
  "controles_recomendados": [
    {"control": "5.15", "nombre": "Control de acceso", "prioridad": "Alta"},
    {"control": "8.12", "nombre": "Prevención de malware", "prioridad": "Alta"}
  ],
  "recomendaciones": [
    "Implementar MFA para acceso al servidor",
    "Actualizar parches de seguridad mensualmente"
  ]
}
```

---

## 10. IA Avanzada

### 10.1 Descripción General

El módulo de **IA Avanzada** extiende las capacidades de análisis del sistema con funcionalidades inteligentes que aprovechan modelos de lenguaje (LLM) a través de Ollama.

**Ubicación de archivos**:
- **Servicios**: `services/ia_advanced_service.py` (~1270 líneas)
- **UI**: `components/ia_advanced_ui.py` (~950 líneas)
- **Exportación**: `services/export_service.py` (~500 líneas)

### 10.2 Funcionalidades (5 Features)

| # | Funcionalidad | Descripción | Persistencia |
|---|---------------|-------------|--------------|
| 1 | 📝 Planes de Tratamiento | Genera planes de acción detallados para mitigar amenazas | ✅ BD |
| 2 | 💬 Chatbot MAGERIT | Consultor interactivo sobre la evaluación | ❌ No aplica |
| 3 | 📋 Resumen Ejecutivo | Informe profesional para alta gerencia | ✅ BD |
| 4 | 🔮 Predicción de Riesgo | Proyección de evolución del riesgo a futuro | ✅ BD |
| 5 | 🎯 Priorización de Controles | Ordena controles por ROI de seguridad | ✅ BD |

### 10.3 Dataclasses Principales

```python
@dataclass
class PlanTratamiento:
    id_evaluacion: str
    id_activo: str
    codigo_amenaza: str
    nombre_amenaza: str
    nivel_riesgo: str
    acciones_corto_plazo: List[Dict]   # [{"accion", "responsable", "plazo", "costo"}]
    acciones_mediano_plazo: List[Dict]
    acciones_largo_plazo: List[Dict]
    responsable_general: str
    presupuesto_total: str
    kpis: List[str]
    modelo_ia: str

@dataclass
class ResumenEjecutivo:
    id_evaluacion: str
    fecha_generacion: str
    total_activos: int
    total_amenazas: int
    distribucion_riesgo: Dict[str, int]  # {"CRÍTICO": 2, "ALTO": 5, ...}
    hallazgos_principales: List[str]
    activos_criticos: List[Dict]
    recomendaciones_prioritarias: List[str]
    inversion_estimada: str              # "$10,000 - $30,000 USD"
    reduccion_riesgo_esperada: str       # "40-60%"
    conclusion: str
    modelo_ia: str

@dataclass
class PrediccionRiesgo:
    id_evaluacion: str
    riesgo_actual: float
    riesgo_residual: float
    tendencia: str                       # "INCREMENTO", "ESTABLE", "DECREMENTO"
    proyecciones: Dict[str, float]       # {"mes_1": 10.5, "mes_3": 11.2, ...}
    factores_incremento: List[str]
    factores_mitigacion: List[str]
    recomendacion: str
    fecha_generacion: str
    modelo_ia: str

@dataclass
class ControlPriorizado:
    codigo: str
    nombre: str
    categoria: str
    riesgos_que_mitiga: int
    activos_afectados: List[str]
    costo_estimado: str                  # "BAJO", "MEDIO", "ALTO"
    tiempo_implementacion: str
    roi_seguridad: int                   # 1-5 (5 = mayor retorno)
    justificacion: str
    orden_prioridad: int
```

### 10.4 Persistencia de Resultados IA

Los resultados generados por IA se guardan en la tabla `IA_RESULTADOS_AVANZADOS` para evitar regeneraciones innecesarias.

```sql
CREATE TABLE IA_RESULTADOS_AVANZADOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_evaluacion TEXT NOT NULL,
    tipo_resultado TEXT NOT NULL,    -- resumen_ejecutivo, prediccion_riesgo, etc.
    datos_json TEXT NOT NULL,        -- Resultado serializado
    fecha_generacion TEXT NOT NULL,
    modelo_ia TEXT,
    UNIQUE(id_evaluacion, tipo_resultado)
);
```

**Funciones de persistencia**:

| Función | Descripción |
|---------|-------------|
| `guardar_resultado_ia(eval_id, tipo, datos, modelo)` | Guarda/actualiza resultado |
| `cargar_resultado_ia(eval_id, tipo)` | Recupera resultado guardado |
| `eliminar_resultado_ia(eval_id, tipo)` | Elimina resultado |

**Comportamiento UI**:
- Si existe resultado guardado → Muestra "🔄 Regenerar" + fecha de generación
- Si no existe → Muestra "Generar" como botón primario
- Al generar → Guarda automáticamente y hace `st.rerun()`

### 10.5 Funciones de Extracción de Datos

Las amenazas y controles se almacenan en formato JSON dentro de `RESULTADOS_MAGERIT`:

| Función | Descripción |
|---------|-------------|
| `obtener_amenazas_evaluacion(eval_id)` | Extrae amenazas de `Amenazas_JSON` |
| `obtener_controles_evaluacion(eval_id)` | Extrae controles de `amenaza.controles_recomendados` |

**Estructura del JSON de amenazas**:
```json
{
  "codigo": "A.11",
  "amenaza": "Acceso no autorizado",
  "tipo_amenaza": "Ataques deliberados",
  "dimension": "C",
  "probabilidad": 4,
  "impacto": 4,
  "riesgo_inherente": 16,
  "nivel_riesgo": "CRÍTICO",
  "controles_recomendados": [
    {"control": "5.15", "nombre": "Control de acceso", "prioridad": "Alta"}
  ]
}
```

### 10.6 Exportación para Ejecutivos

El servicio `export_service.py` genera documentos profesionales:

**Formatos soportados**:

| Formato | Función | Descripción |
|---------|---------|-------------|
| HTML | `generar_documento_ejecutivo(resumen, "html")` | Documento estilizado con CSS profesional |
| Markdown | `generar_documento_ejecutivo(resumen, "markdown")` | Para edición posterior |
| JSON | `resumen.to_dict()` | Datos estructurados |

**Ejemplo HTML generado**:
- Header con logo y fecha
- Sección de métricas clave (activos, amenazas, distribución)
- Tabla de activos críticos
- Lista de hallazgos y recomendaciones
- Estimaciones de inversión y reducción de riesgo
- Footer con disclaimer

### 10.7 Integración con Power BI

Se generan datasets optimizados para dashboards en Power BI:

| Dataset | Descripción |
|---------|-------------|
| `Activos` | Inventario completo con estados |
| `Resultados_MAGERIT` | Análisis de riesgo por activo |
| `Amenazas` | Detalle de amenazas identificadas |
| `Controles_Recomendados` | Controles sugeridos por amenaza |
| `Distribucion_Riesgos` | Conteo por nivel de riesgo |
| `Impacto_Dimensiones` | Promedio DIC por activo |
| `Tipos_Amenaza` | Clasificación de amenazas |
| `Metadata` | Información de la evaluación |

**Funciones de exportación**:

| Función | Descripción |
|---------|-------------|
| `generar_datos_powerbi(eval_id)` | Genera dict de DataFrames |
| `exportar_powerbi_excel(eval_id, ruta)` | Exporta a Excel multi-hoja |

### 10.8 Chatbot Consultor MAGERIT

Chatbot interactivo que responde preguntas sobre la evaluación:

**Configuración**:
- Modelo: `llama3.2:1b` (configurable)
- Temperatura: `0.3` (respuestas más coherentes)
- Contexto: Incluye métricas de la evaluación actual

**Preguntas sugeridas**:
- "¿Cuáles son los principales riesgos identificados?"
- "¿Qué controles debo implementar primero?"
- "¿Cómo se calcula el riesgo inherente?"
- "Resume el estado de la evaluación"

**Historial de conversación**:
- Se mantiene en `st.session_state["ia_chat_history"]`
- Botón para limpiar historial

---

## 11. Catálogos y Estándares

### 10.1 Criterios MAGERIT (Valoración DIC)

Escala 1-5 para Disponibilidad, Integridad y Confidencialidad:

| Nivel | Disponibilidad | Integridad | Confidencialidad |
|-------|----------------|------------|------------------|
| 1 | Interrupción < 1h | Errores menores | Info pública |
| 2 | Interrupción 1-4h | Errores corregibles | Info interna |
| 3 | Interrupción 4-24h | Impacto operativo | Info sensible |
| 4 | Interrupción 1-7 días | Datos críticos | Datos personales |
| 5 | Interrupción > 7 días | Pérdida total | Secretos comerciales |

### 10.2 Amenazas MAGERIT v3 (52 amenazas)

✅ **IMPLEMENTADO** en `CATALOGO_AMENAZAS_MAGERIT`

| Categoría | Código | Cantidad | Ejemplos |
|-----------|--------|----------|----------|
| Desastres Naturales | N.* | 3 | N.1 Fuego, N.2 Daños por agua, N.* Desastres naturales |
| Origen Industrial | I.* | 11 | I.5 Avería de origen físico/lógico, I.6 Corte de suministro eléctrico |
| Errores no Intencionados | E.* | 17 | E.1 Errores de usuarios, E.20 Vulnerabilidades software |
| Ataques Intencionados | A.* | 21 | A.5 Suplantación de identidad, A.24 Denegación de servicio |

**Seed Script**: `python seed_catalogos_magerit.py`

### 10.3 Controles ISO 27002:2022 (93 controles)

✅ **IMPLEMENTADO** en `CATALOGO_CONTROLES_ISO27002`

| Categoría | Rango | Cantidad | Ejemplos |
|-----------|-------|----------|----------|
| Organizacional | 5.1-5.37 | 37 | 5.1 Políticas de seguridad, 5.29 Continuidad |
| Personas | 6.1-6.8 | 8 | 6.3 Concientización, 6.8 Reporte de eventos |
| Físico | 7.1-7.14 | 14 | 7.1 Perímetros, 7.11 Servicios de apoyo |
| Tecnológico | 8.1-8.34 | 34 | 8.5 Autenticación, 8.7 Malware, 8.13 Backups |

**Seed Script**: `python seed_catalogos_magerit.py`

### 10.4 Niveles de Riesgo (Matriz 5×5)

| Valor | Nivel | Color | Acción |
|-------|-------|-------|--------|
| 1-2 | MUY BAJO | 🟢 Verde oscuro | Aceptar |
| 3-5 | BAJO | 🟢 Verde claro | Monitorear |
| 6-11 | MEDIO | 🟡 Naranja | Planificar mitigación |
| 12-19 | ALTO | 🟠 Rojo claro | Acción prioritaria |
| 20-25 | CRÍTICO | 🔴 Rojo oscuro | Acción inmediata obligatoria |

---

## 12. Estructura de Archivos

```
capston_riesgos/
├── app_final.py              # Aplicación principal Streamlit (9 tabs)
├── init_sqlite.py            # Script de inicialización de BD
├── seed_catalogos_magerit.py # Seed de 52 amenazas + 93 controles
├── tita_database.db          # Base de datos SQLite (NO EDITAR MANUALMENTE)
├── CONTEXTO_PROYECTO_TITA.md # Este documento
├── requirements.txt          # Dependencias Python
│
├── services/
│   ├── __init__.py           # Exports de servicios
│   ├── database_service.py   # CRUD SQLite (capa de persistencia)
│   ├── evaluacion_service.py # Gestión de evaluaciones y re-evaluaciones
│   ├── activo_service.py     # Gestión de activos
│   ├── cuestionario_service.py # Cuestionarios y respuestas
│   ├── ollama_service.py     # Integración con IA (legacy)
│   ├── ollama_magerit_service.py # IA con validación MAGERIT
│   ├── magerit_engine.py     # Motor de cálculo MAGERIT v3
│   ├── maturity_service.py   # Cálculo de nivel de madurez CMMI
│   ├── carga_masiva_service.py # Carga masiva JSON/Excel con campos concentración
│   ├── concentration_risk_service.py # ✨ NUEVO: Riesgo por concentración Host-VM
│   ├── ia_validation_service.py  # Validación IA local
│   └── knowledge_base_service.py # Knowledge Base MAGERIT
│
├── components/
│   ├── __init__.py           # Exports de componentes
│   ├── dashboard_magerit.py  # Dashboards visuales
│   ├── ia_validation_ui.py   # UI validación IA
│   ├── carga_masiva_ui.py    # UI carga masiva de activos
│   └── concentration_risk_ui.py # ✨ NUEVO: UI riesgo por concentración
│
├── knowledge_base/           # Archivos de conocimiento
│   ├── MAGERIT_CRITERIOS.md  # Documentación metodología MAGERIT
│   ├── amenazas_magerit.json # Catálogo 52 amenazas en JSON
│   ├── controles_iso27002.json # Catálogo 93 controles en JSON
│   └── system_prompt.md      # System prompt para IA
│
├── docs/
│   └── ADR_RIESGO_CONCENTRACION.md # ✨ Arquitectura Decision Record
│
├── config/
│   └── settings.py           # Configuraciones, constantes
│
└── .venv/                    # Entorno virtual Python
```

---

## 11.1 Sistema de Validación de IA Local (NUEVO)

### Propósito
Sistema completo para validar que la IA funciona 100% local con Ollama, sin conexiones a Internet, con evidencia técnica auditable para defensa académica.

### Componentes

| Archivo | Propósito |
|---------|-----------|
| `ia_validation_service.py` | Servicio de validación completa |
| `knowledge_base_service.py` | Gestión de Knowledge Base |
| `ia_validation_ui.py` | Interfaz Streamlit para validación |

### Validaciones Realizadas

1. **Verificación Local**: Confirma que Ollama corre en localhost:11434
2. **Canary Token**: Inyecta nonce único que IA debe devolver (anti-falsificación)
3. **Variabilidad**: Prueba respuestas con diferentes temperaturas
4. **Dependencia de Input**: Verifica respuestas diferentes para inputs opuestos
5. **Catálogos**: Confirma 52 amenazas + 93 controles cargados

### Evidencia Técnica

Cada ejecución de IA genera:
- Hash SHA-256 del prompt
- Hash SHA-256 de la respuesta
- Timestamp preciso
- Latencia en ms
- Validación de códigos contra catálogos

### Tablas de BD Creadas

```sql
-- Evidencia de ejecuciones IA
IA_EXECUTION_EVIDENCE (
    id, id_evaluacion, id_activo, timestamp,
    modelo, endpoint, prompt_hash, response_hash,
    latency_ms, json_valid, canary_verified
)

-- Log de validaciones
IA_VALIDATION_LOG (
    id, timestamp, validation_type, result,
    details, evidence_hash
)

-- Estado de IA
IA_STATUS (
    id, ia_ready, last_validation, canary_nonce
)
```

### Bloqueo de Seguridad

El botón "Evaluar Activo" está **bloqueado** hasta que:
1. Se ejecute validación completa de IA
2. Canary token pase exitosamente
3. Catálogos estén cargados

---

## 13. Guía de Desarrollo

### 12.1 Instalación

```bash
# Clonar/abrir proyecto
cd capston_riesgos

# Crear entorno virtual
python -m venv .venv

# Activar (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python init_sqlite.py

# Cargar catálogos MAGERIT + ISO 27002
python seed_catalogos_magerit.py

# Ejecutar aplicación
streamlit run app_final.py --server.port 8506
```

### 12.2 Inicializar/Reiniciar Base de Datos

```bash
# Elimina BD existente y crea una nueva con datos de prueba
python init_sqlite.py

# Cargar catálogos oficiales (52 amenazas + 93 controles)
python seed_catalogos_magerit.py
```

### 12.3 Exportar a Excel

```python
from services import exportar_a_excel
exportar_a_excel("reporte_completo.xlsx")
```

### 12.4 Verificar Ollama

```bash
# Verificar que Ollama está corriendo
curl http://localhost:11434/api/tags

# Listar modelos disponibles
ollama list

# Descargar modelo recomendado
ollama pull llama3
```

---

## 14. Reglas de Negocio Críticas

### 13.1 Evaluación como Contenedor

> ⚠️ **REGLA FUNDAMENTAL**: Una evaluación es el contenedor obligatorio.
> Los activos NO pueden existir sin una evaluación asociada.

### 13.2 Estados Automáticos

> ⚠️ **REGLA**: Los estados de activos se CALCULAN, no se setean manualmente.

```python
def calcular_estado_activo(eval_id, activo_id):
    if tiene_analisis_ia():
        return "Evaluado"
    elif cuestionario_completo():
        return "Completo"
    elif tiene_respuestas():
        return "Incompleto"
    else:
        return "Pendiente"
```

### 13.3 Invalidación de Análisis IA

> ⚠️ **REGLA**: Si se modifican respuestas después de evaluar con IA,
> el análisis queda OBSOLETO y debe regenerarse.

```python
# Si usuario modifica respuestas de un activo "Evaluado":
invalidar_analisis_ia(eval_id, activo_id)
# Estado vuelve a "Completo"
```

### 13.4 Validación de Duplicados

> ⚠️ **REGLA**: No pueden existir dos activos con:
> - Mismo nombre
> - Misma ubicación  
> - Mismo tipo de servicio
> Dentro de la misma evaluación.

### 13.5 Cuestionarios Inmutables

> ⚠️ **REGLA**: Una vez generado el cuestionario para un activo,
> las preguntas no cambian (se preserva la versión del banco usada).

### 13.6 Dimensiones DIC

> ⚠️ **REGLA**: Cada pregunta afecta una dimensión específica:
> - **D** = Disponibilidad
> - **I** = Integridad
> - **C** = Confidencialidad

El impacto final se calcula agregando respuestas por dimensión.

---

## Pendientes por Implementar

| # | Funcionalidad | Prioridad | Estado |
|---|---------------|-----------|--------|
| 1 | Catálogo completo de amenazas MAGERIT | Alta | ✅ Implementado (52 amenazas) |
| 2 | 93 controles ISO 27002:2022 | Alta | ✅ Implementado |
| 3 | Criterios MAGERIT correctos | Alta | ✅ Implementado |
| 4 | Re-evaluaciones comparativas | Media | ✅ Implementado |
| 5 | Cálculo de nivel de madurez | Alta | ✅ Implementado |
| 6 | Comparativa de madurez entre evaluaciones | Media | ✅ Implementado |
| 7 | Carga masiva de activos (JSON/Excel) | Alta | ✅ Implementado |
| 8 | Exportación de reportes PDF | Baja | ❌ No iniciado |
| 9 | Autenticación de usuarios | Baja | ❌ No iniciado |

---

## Historial de Cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|\n| 25 Enero 2026 | 2.5 | **NUEVO**: Módulo IA Avanzada completo (5 funcionalidades), persistencia de resultados IA en BD, exportación HTML/MD/JSON para ejecutivos, datasets para Power BI (8 tablas), chatbot mejorado (temperatura 0.3), botón "Regenerar" en lugar de regenerar siempre |
| 25 Enero 2026 | 2.4 | **NUEVO**: Riesgo por concentración (Host-VM) con modelo Blast Radius + Herencia, tab dedicado con dashboard, integración en carga masiva (campos id_host, tipo_dependencia), botón eliminar evaluación con confirmación |
| 25 Enero 2026 | 2.2 | **NUEVO**: Carga masiva de activos (JSON/Excel) con validación, plantillas descargables |
| 24 Enero 2026 | 2.1 | Sistema de madurez CMMI, comparativas funcionales, fix re-evaluaciones |
| Enero 2026 | 2.0 | Migración de Excel a SQLite, documentación completa |
| Enero 2026 | 1.5 | Cuestionarios de 21 preguntas, 5 bloques |
| Enero 2026 | 1.0 | Versión inicial con Excel |

---

*Documento generado para facilitar el contexto a asistentes de IA y desarrolladores.*
*Última actualización: 25 Enero 2026 - Versión 2.5*

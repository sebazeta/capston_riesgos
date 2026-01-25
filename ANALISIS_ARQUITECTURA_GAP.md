# ANÁLISIS ARQUITECTÓNICO: ESTADO ACTUAL vs. DOCUMENTACIÓN
## Proyecto TITA - Evaluación de Riesgos MAGERIT/ISO 27002

**Arquitecto:** Experto en Ciberseguridad y Desarrollo de Software  
**Fecha:** 22 de Enero de 2026  
**Versión:** 1.0

---

## RESUMEN EJECUTIVO

### Hallazgo Principal
El **CONTEXTO_PROYECTO_TITA.md** describe una **aplicación de escritorio completa con arquitectura en capas (PySide6/Qt)**, pero la **implementación actual es una aplicación web Streamlit** con funcionalidad parcial y estructura simplificada.

### Nivel de Discrepancia
🔴 **CRÍTICO** - Existe una brecha arquitectónica fundamental entre lo documentado y lo implementado.

### Impacto
- **Académico:** El documento no refleja la realidad del código
- **Técnico:** La arquitectura real es más simple y limitada
- **Funcional:** Múltiples componentes descritos NO existen

---

## 1. ANÁLISIS COMPARATIVO DE ARQUITECTURA

### 1.1 Framework de Interfaz Gráfica

| Aspecto | DOCUMENTADO (TO-BE) | IMPLEMENTADO (AS-IS) | Gap |
|---------|---------------------|----------------------|-----|
| **Framework** | PySide6 (Qt for Python) | Streamlit | 🔴 Diferente |
| **Tipo** | Aplicación Desktop | Aplicación Web | 🔴 Diferente |
| **Complejidad** | GUI nativa con ventanas | Single-page web app | 🔴 Más simple |
| **Deployment** | Instalación local | Servidor web | 🔴 Diferente |

**Análisis:**
El documento describe una aplicación **desktop Qt** compleja, pero el código real es una **aplicación web Streamlit** mucho más simple. Esta es una diferencia arquitectónica fundamental.

---

### 1.2 Arquitectura en Capas

#### DOCUMENTADO (según CONTEXTO_PROYECTO_TITA.md)

```
┌─────────────────────────────────────────────┐
│  CAPA DE PRESENTACIÓN (gui/)                │
│  ├── main_window.py                         │
│  ├── home_screen.py                         │
│  ├── evaluation_menu.py                     │
│  ├── assets/                                │
│  ├── questionnaire/                         │
│  ├── dashboards/                            │
│  └── dialogs/                               │
├─────────────────────────────────────────────┤
│  CAPA DE SERVICIOS (services/)              │
│  ├── evaluation_service.py                  │
│  ├── asset_service.py                       │
│  ├── questionnaire_service.py               │
│  ├── risk_assessment_service.py             │
│  └── dashboard_service.py                   │
├─────────────────────────────────────────────┤
│  CAPA DE DOMINIO (core/)                    │
│  ├── models.py (dataclasses)                │
│  ├── enums.py                               │
│  └── exceptions.py                          │
├─────────────────────────────────────────────┤
│  CAPA DE INFRAESTRUCTURA (infra/)           │
│  ├── excel_repository.py                    │
│  ├── ollama_client.py                       │
│  └── config_manager.py                      │
├─────────────────────────────────────────────┤
│  CONFIGURACIÓN (config/)                    │
│  ├── config.json                            │
│  ├── catalogs.json                          │
│  └── questions.json                         │
└─────────────────────────────────────────────┘
```

#### IMPLEMENTADO (estructura real del proyecto)

```
c:\capston_riesgos\
├── app.py                    # ✅ Todo en un solo archivo
├── setup_excel_v2.py         # ✅ Utilitario de setup
├── setup_excel.py            # ✅ Versión anterior
├── seed_catalogos.py         # ✅ Seeding inicial
├── generate_questions.py     # ✅ Script de generación IA
├── add_bia_columns.py        # ✅ Migración de esquema
├── matriz_riesgos_v2.xlsx    # ✅ Base de datos Excel
├── matriz_riesgos.xlsx       # ✅ Versión anterior
└── CONTEXTO_PROYECTO_TITA.md # ❌ Documentación desactualizada
```

**Análisis:**
- ❌ **NO existe** carpeta `gui/`
- ❌ **NO existe** carpeta `services/`
- ❌ **NO existe** carpeta `core/`
- ❌ **NO existe** carpeta `infra/`
- ❌ **NO existe** carpeta `config/`
- ✅ **Toda la lógica** está en un único archivo: `app.py` (668 líneas)

---

### 1.3 Dependencias Tecnológicas

| Componente | DOCUMENTADO | IMPLEMENTADO | Estado |
|------------|-------------|--------------|--------|
| PySide6 | ✅ Requerido | ❌ No instalado | 🔴 Faltante |
| pandas | ✅ Requerido | ✅ Presente | ✅ OK |
| openpyxl | ✅ Requerido | ✅ Presente | ✅ OK |
| requests | ✅ Requerido | ✅ Presente | ✅ OK |
| matplotlib | ✅ Requerido | ❌ No usado | 🟡 Opcional |
| numpy | ✅ Requerido | ❌ No usado | 🟡 Opcional |
| **streamlit** | ❌ No documentado | ✅ **USADO** | 🔴 **CRÍTICO** |

**Análisis:**
La dependencia más crítica (Streamlit) **NO está documentada** en el CONTEXTO_PROYECTO_TITA.md.

---

## 2. ANÁLISIS FUNCIONAL: QUÉ EXISTE vs. QUÉ FALTA

### 2.1 Módulos de GUI (DOCUMENTADOS pero NO IMPLEMENTADOS)

| Módulo Documentado | Archivo Esperado | Estado Real |
|-------------------|------------------|-------------|
| Ventana Principal | `gui/main_window.py` | ❌ No existe |
| Pantalla Inicial | `gui/home_screen.py` | ❌ No existe |
| Menú Evaluación | `gui/evaluation_menu.py` | ❌ No existe |
| Formularios Activos | `gui/assets/` | ❌ No existe |
| Cuestionarios | `gui/questionnaire/` | ❌ No existe |
| Dashboards | `gui/dashboards/` | ❌ No existe |
| Diálogos IA | `gui/dialogs/` | ❌ No existe |

**Funcionalidad Equivalente en app.py:**
```python
# Tab 1: Inventario (reemplaza gui/assets/)
# Tab 2: Preguntas IA (reemplaza gui/questionnaire/)
# Tab 3: Responder (reemplaza gui/questionnaire/)
# Tab 4: Cálculo Impacto (reemplaza gui/dashboards/ parcialmente)
```

---

### 2.2 Servicios de Negocio (DOCUMENTADOS pero NO IMPLEMENTADOS)

| Servicio Documentado | Archivo Esperado | Implementación Real |
|---------------------|------------------|---------------------|
| EvaluationService | `services/evaluation_service.py` | ❌ No existe como clase |
| AssetService | `services/asset_service.py` | ❌ No existe como clase |
| QuestionnaireService | `services/questionnaire_service.py` | ❌ No existe como clase |
| RiskAssessmentService | `services/risk_assessment_service.py` | ❌ No existe como clase |
| DashboardService | `services/dashboard_service.py` | ❌ No existe como clase |

**Funcionalidad Equivalente en app.py:**
```python
# Funciones sueltas (no orientadas a objetos):
def set_eval_active(eval_id: str, nombre: str)
def read_sheet(sheet_name: str) -> pd.DataFrame
def append_rows(sheet_name: str, rows: list)
def ollama_generate(model: str, prompt: str)
def extract_json_array(text: str)
def validate_ia_questions(qs, n_ia: int)
```

---

### 2.3 Modelos de Dominio (DOCUMENTADOS pero NO IMPLEMENTADOS)

| Modelo Documentado | Archivo Esperado | Estado Real |
|-------------------|------------------|-------------|
| Evaluation (dataclass) | `core/models.py` | ❌ No existe |
| Asset (dataclass) | `core/models.py` | ❌ No existe |
| RiskResult | `core/models.py` | ❌ No existe |
| Threat | `core/models.py` | ❌ No existe |
| Vulnerability | `core/models.py` | ❌ No existe |
| Safeguard | `core/models.py` | ❌ No existe |

**Implementación Real:**
- Los datos se manejan como **diccionarios simples de Python**
- No hay validación de tipos
- No hay encapsulación de lógica de negocio

```python
# Ejemplo real de "modelo" en app.py:
row = {
    "ID_Evaluacion": eval_id,
    "Nombre": nombre,
    "Fecha": now,
    "Estado": "Activa",
    "Descripcion": "Evaluación activa desde la GUI"
}
```

---

### 2.4 Infraestructura (DOCUMENTADOS pero NO IMPLEMENTADOS)

| Componente | Archivo Esperado | Implementación Real |
|-----------|------------------|---------------------|
| ExcelRepository | `infra/excel_repository.py` | ❌ Funciones sueltas en app.py |
| OllamaClient | `infra/ollama_client.py` | ❌ Función `ollama_generate()` |
| ConfigManager | `infra/config_manager.py` | ❌ Constantes globales |

---

### 2.5 Configuración (DOCUMENTADOS pero NO IMPLEMENTADOS)

| Archivo Config | Esperado | Estado Real |
|---------------|----------|-------------|
| `config/config.json` | ✅ | ❌ No existe |
| `config/catalogs.json` | ✅ | ❌ No existe |
| `config/questions.json` | ✅ | ❌ No existe |

**Implementación Real:**
```python
# Configuración hardcodeada en app.py
EXCEL_PATH = "matriz_riesgos_v2.xlsx"
OLLAMA_URL = "http://localhost:11434/api/generate"
```

---

## 3. ANÁLISIS DE PERSISTENCIA (EXCEL)

### 3.1 Estructura de Excel Documentada vs. Implementada

| Hoja Excel | DOCUMENTADO | IMPLEMENTADO | Estado |
|-----------|-------------|--------------|--------|
| PORTADA | ✅ | ✅ | ✅ OK |
| EVALUACIONES | ✅ | ✅ | ✅ OK |
| CRITERIOS_MAGERIT | ✅ | ✅ | ✅ OK |
| CATALOGO_AMENAZAS_MAGERIT | ✅ | ✅ | ✅ OK |
| CATALOGO_ISO27002_2022 | ✅ | ⚠️ (nombre diferente) | 🟡 Variante |
| INVENTARIO_ACTIVOS | ✅ | ✅ | ✅ OK |
| BANCO_PREGUNTAS | ❌ No documentado | ✅ **EXISTE** | 🟡 Extra |
| **CUESTIONARIOS** | ❌ Llama "Cuestionario" | ✅ "CUESTIONARIOS" | 🟡 Variante |
| RESPUESTAS | ❌ No documentado | ✅ **EXISTE** | 🟡 Extra |
| IMPACTO_ACTIVOS | ❌ No documentado | ✅ **EXISTE** | 🟡 Extra |
| VALORACION_DIC | ✅ | ✅ | ✅ OK |
| AMENAZAS_VULNERAB | ✅ | ✅ | ✅ OK |
| ANALISIS_RIESGO | ✅ | ✅ | ✅ OK |
| SALVAGUARDAS | ✅ | ✅ | ✅ OK |
| RIESGO_RESIDUAL | ✅ | ✅ | ✅ OK |
| HISTORICO | ✅ | ✅ | ✅ OK |
| DASHBOARD | ✅ | ✅ | ✅ OK |
| COMPARATIVO | ✅ | ✅ | ✅ OK |

**Hallazgos:**
- ✅ La mayoría de hojas existen
- 🟡 Hay hojas **nuevas** no documentadas: `BANCO_PREGUNTAS`, `CUESTIONARIOS`, `RESPUESTAS`, `IMPACTO_ACTIVOS`
- 🟡 Estas hojas implementan el **flujo de versionado de cuestionarios** que no está en el documento

---

### 3.2 Esquema de Versionado (INNOVACIÓN NO DOCUMENTADA)

**Implementación Real (app.py):**
El sistema implementa un **versionado de cuestionarios por timestamp** que NO está descrito en el documento:

```python
CUESTIONARIOS_HEADERS = [
    "ID_Evaluacion",
    "ID_Activo",
    "Fecha",                # ⭐ versión del cuestionario (timestamp)
    "ID_Pregunta",
    "Pregunta",
    "Tipo_Respuesta",
    "Peso",
    "Dimension",
    "Fuente(IA/Base)"       # ⭐ distingue preguntas base vs IA
]

RESPUESTAS_HEADERS = [
    "ID_Evaluacion",
    "ID_Activo",
    "Fecha_Cuestionario",   # ⭐ versión respondida
    "ID_Pregunta",
    "Pregunta",
    "Respuesta",
    "Tipo_Respuesta",
    "Peso",
    "Dimension",
    "Fecha"                 # ⭐ timestamp de respuesta
]
```

**Análisis:**
- ✅ **Innovación positiva:** El código implementa trazabilidad temporal
- ❌ **NO documentado:** El documento no menciona este mecanismo
- 🟡 **Complejidad adicional:** Versiones múltiples del mismo cuestionario

---

## 4. ANÁLISIS DE INTELIGENCIA ARTIFICIAL

### 4.1 Integración de IA

| Aspecto | DOCUMENTADO | IMPLEMENTADO | Estado |
|---------|-------------|--------------|--------|
| Motor IA | Ollama local | Ollama local | ✅ OK |
| Modelo Default | llama3.2:1b | llama3 | 🟡 Variante |
| Timeout | 900s (15 min) | 90s (1.5 min) | 🔴 Diferente |
| Uso | Evaluación completa de riesgos | Solo generación de preguntas | 🔴 **LIMITADO** |

**Análisis Crítico:**

El documento describe que la IA hace:
```
1. Análisis de contexto
2. Identificación de amenazas
3. Detección de vulnerabilidades
4. Cálculo de riesgo inherente
5. Propuesta de salvaguardas
6. Justificación
```

**Implementación Real (app.py):**
```python
# La IA SOLO genera preguntas de cuestionario:
prompt = f"""
Genera EXACTAMENTE {n_ia} preguntas TÉCNICAS para continuidad...
"""
```

- ❌ **NO calcula riesgos**
- ❌ **NO identifica amenazas**
- ❌ **NO propone salvaguardas**
- ✅ **SOLO genera preguntas de cuestionario**

**Gap Funcional:**
El 80% de la funcionalidad de IA descrita **NO EXISTE**.

---

### 4.2 Flujo de Evaluación IA Documentado

```
Activo COMPLETO → Construir prompt → Ollama → Parsear JSON →
Crear objetos (RiskResult, Threat, Vulnerability) → Persistir
```

**Flujo Real Implementado:**
```
Activo seleccionado → Banco de preguntas → Generar prompt IA →
Ollama genera preguntas → Validar JSON → Guardar en CUESTIONARIOS
```

**Conclusión:** Son flujos completamente diferentes.

---

## 5. ANÁLISIS DE DASHBOARDS Y VISUALIZACIÓN

### 5.1 Visualizaciones Documentadas vs. Implementadas

| Dashboard | DOCUMENTADO | IMPLEMENTADO | Estado |
|-----------|-------------|--------------|--------|
| Ranking de Activos Críticos | ✅ | ❌ | 🔴 Faltante |
| Mapa de Calor (Probabilidad×Impacto) | ✅ | ❌ | 🔴 Faltante |
| Distribución por Categorías | ✅ | ❌ | 🔴 Faltante |
| Tendencias Temporales | ✅ | ❌ | 🔴 Faltante |
| Comparativas entre Evaluaciones | ✅ | ❌ | 🔴 Faltante |

**Implementación Real:**
- ✅ Tab 4 calcula **Impacto DIC** básico (promedio ponderado)
- ❌ **NO hay visualizaciones gráficas** (ni matplotlib, ni charts)
- ❌ **NO hay comparativas** entre evaluaciones

---

## 6. ANÁLISIS DE ESTADOS Y WORKFLOW

### 6.1 Máquina de Estados Documentada

```
PENDIENTE → INCOMPLETO → COMPLETO → EVALUADO
```

**Implementación Real:**
- ❌ **NO existe máquina de estados** formal
- ❌ **NO hay validación de transiciones**
- 🟡 El campo `Estado_Cuestionario` existe en Excel pero no se usa programáticamente

---

## 7. BRECHAS CRÍTICAS DE SEGURIDAD

### 7.1 Autenticación y Autorización

| Característica | DOCUMENTADO (TO-BE) | IMPLEMENTADO | Riesgo |
|----------------|---------------------|--------------|--------|
| Autenticación | JWT/OAuth2 | ❌ Ninguna | 🔴 CRÍTICO |
| Control de acceso | RBAC | ❌ Ninguno | 🔴 CRÍTICO |
| Roles | Admin, Auditor, etc. | ❌ Ninguno | 🔴 CRÍTICO |
| Auditoría de usuarios | Log de acciones | ❌ Ninguna | 🔴 CRÍTICO |

**Análisis:**
Como es una aplicación Streamlit básica sin autenticación:
- ⚠️ **Cualquiera con acceso al servidor puede modificar datos**
- ⚠️ **No hay trazabilidad de quién hizo qué**
- ⚠️ **No hay control de permisos**

---

### 7.2 Validación de Datos

| Validación | DOCUMENTADO | IMPLEMENTADO | Estado |
|-----------|-------------|--------------|--------|
| Tipos de datos (dataclasses) | ✅ | ❌ | 🔴 Faltante |
| Constraints de BD | ✅ | ❌ (Excel no soporta) | 🟡 Limitación técnica |
| Validación de entrada | ✅ | 🟡 Parcial | 🟡 Básica |

---

## 8. QUÉ SÍ FUNCIONA (FORTALEZAS)

### 8.1 Funcionalidades Implementadas Correctamente

| Funcionalidad | Estado | Calidad |
|--------------|--------|---------|
| **Setup de Excel** | ✅ | ⭐⭐⭐⭐⭐ Excelente |
| **Seeding de catálogos** | ✅ | ⭐⭐⭐⭐ Buena |
| **Gestión de evaluaciones** | ✅ | ⭐⭐⭐ Básica |
| **Inventario de activos** | ✅ | ⭐⭐⭐ Básica (solo visualización) |
| **Generación IA de preguntas** | ✅ | ⭐⭐⭐⭐ Buena |
| **Versionado de cuestionarios** | ✅ | ⭐⭐⭐⭐ Innovadora |
| **Respuesta de cuestionarios** | ✅ | ⭐⭐⭐⭐ Buena |
| **Cálculo de impacto DIC** | ✅ | ⭐⭐⭐ Básica |
| **Edición de preguntas** | ✅ | ⭐⭐⭐ Básica |

---

### 8.2 Innovaciones No Documentadas (POSITIVAS)

1. **Sistema de Versionado de Cuestionarios**
   - Permite múltiples versiones por activo/evaluación
   - Timestamp como identificador de versión
   - Trazabilidad de qué versión se respondió

2. **Banco de Preguntas Base**
   - Repositorio de preguntas estándar
   - Clasificadas por tipo de activo
   - Permite personalización por dimensión DIC

3. **Distinción Fuente (IA/Base)**
   - Identifica origen de cada pregunta
   - Permite auditar qué generó la IA vs. lo predefinido

4. **Fallback de IA**
   - Si Ollama falla, usa preguntas de respaldo
   - Evita que el flujo se rompa

---

## 9. ANÁLISIS DE SCRIPTS AUXILIARES

### 9.1 Scripts No Documentados pero Implementados

| Script | Propósito | Estado |
|--------|-----------|--------|
| `setup_excel_v2.py` | Crea estructura Excel con hojas nuevas | ✅ Funcional |
| `setup_excel.py` | Versión anterior (deprecated) | 🟡 Legacy |
| `seed_catalogos.py` | Inicializa catálogos MAGERIT/ISO | ✅ Funcional |
| `generate_questions.py` | CLI para generar preguntas IA | ✅ Funcional |
| `add_bia_columns.py` | Migración: añade RTO/RPO/BIA | ✅ Funcional |

**Análisis:**
Estos scripts muestran **evolución iterativa** del proyecto:
- Hay versiones v1 y v2
- Migraciones de esquema
- Herramientas CLI separadas de la GUI

---

## 10. RECOMENDACIONES CRÍTICAS

### 10.1 Prioridad 1: SINCRONIZAR DOCUMENTACIÓN

🔴 **URGENTE**

**Acción:**
Actualizar `CONTEXTO_PROYECTO_TITA.md` para reflejar:
- Arquitectura real: **Streamlit**, no PySide6
- Funcionalidad real: generación de preguntas, no evaluación completa
- Estructura real: archivo único, no arquitectura en capas

**Razón:**
La documentación actual es **engañosa** para cualquier auditor, académico o nuevo desarrollador.

---

### 10.2 Prioridad 2: COMPLETAR FUNCIONALIDAD DE IA

🔴 **ALTA**

**Gap Actual:**
La IA solo genera preguntas. **Falta el 80% de la funcionalidad prometida:**
- Análisis de riesgos
- Identificación de amenazas
- Cálculo de probabilidad/impacto
- Propuesta de salvaguardas

**Acción:**
Decidir:
1. **Opción A:** Implementar la funcionalidad completa de IA
2. **Opción B:** Actualizar el documento para reflejar el alcance limitado actual

---

### 10.3 Prioridad 3: IMPLEMENTAR SEGURIDAD BÁSICA

🔴 **ALTA**

**Gap Actual:**
- Sin autenticación
- Sin control de acceso
- Sin auditoría

**Acción Mínima:**
```python
# Añadir a app.py
import streamlit_authenticator as stauth

# Configurar usuarios básicos
authenticator = stauth.Authenticate(
    credentials,
    cookie_name='tita_auth',
    key='tita_secret_key',
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login('Login', 'main')

if not authentication_status:
    st.stop()
```

---

### 10.4 Prioridad 4: REFACTORIZAR ARQUITECTURA

🟡 **MEDIA** (post-MVP)

**Problema:**
`app.py` tiene 668 líneas. No escalable.

**Solución:**
Implementar arquitectura en capas (aunque sea simple):

```
capston_riesgos/
├── app.py                    # Solo UI Streamlit
├── services/
│   ├── excel_service.py      # Lectura/escritura Excel
│   ├── ollama_service.py     # Cliente IA
│   └── evaluation_service.py # Lógica de negocio
├── models/
│   └── schemas.py            # Pydantic models
└── config/
    └── settings.py           # Configuración centralizada
```

---

### 10.5 Prioridad 5: IMPLEMENTAR DASHBOARDS

🟡 **MEDIA**

**Gap Actual:**
No hay visualizaciones gráficas.

**Solución:**
```python
import plotly.express as px
import streamlit as st

# Ejemplo: Mapa de calor
fig = px.density_heatmap(
    df_riesgos,
    x="Probabilidad",
    y="Impacto",
    z="Cantidad",
    title="Mapa de Calor de Riesgos"
)
st.plotly_chart(fig)
```

---

## 11. EVALUACIÓN DE VIABILIDAD DE MIGRACIÓN WEB

### 11.1 Ironía Detectada

El documento propone **migrar de Desktop a Web**, pero el sistema **YA ES WEB** (Streamlit).

### 11.2 Re-interpretación de la Migración

**Migración REAL necesaria:**
```
Streamlit monolítico
    ↓
FastAPI + React/Vue (aplicación web profesional)
```

**NO:**
```
PySide6 Desktop → Web (como dice el documento)
```

---

### 11.3 Arquitectura TO-BE Ajustada

```
┌─────────────────────────────────────────────┐
│  FRONTEND: React/Vue/Angular                │
│  - Componentes reutilizables                │
│  - Estado global (Redux/Pinia)              │
│  - Gráficos interactivos (Chart.js/D3)      │
├─────────────────────────────────────────────┤
│  BACKEND: FastAPI (Python)                  │
│  - Endpoints REST                           │
│  - Autenticación JWT                        │
│  - Validación Pydantic                      │
├─────────────────────────────────────────────┤
│  SERVICIOS (reutilizar lógica actual)       │
│  - evaluation_service.py                    │
│  - questionnaire_service.py                 │
│  - risk_service.py (extender IA)            │
├─────────────────────────────────────────────┤
│  PERSISTENCIA                               │
│  - PostgreSQL (operación)                   │
│  - Generador Excel (reportes)               │
├─────────────────────────────────────────────┤
│  IA                                         │
│  - Ollama local (dev)                       │
│  - OpenAI API (producción, opcional)        │
└─────────────────────────────────────────────┘
```

---

## 12. MATRIZ DE DECISIONES ESTRATÉGICAS

### 12.1 Decisión 1: ¿Qué hacer con la documentación?

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| **A) Actualizar doc para reflejar realidad** | Honestidad técnica | Admitir gap | ⭐⭐⭐⭐⭐ **RECOMENDADO** |
| B) Implementar lo documentado | Cumplir promesa | 3-6 meses de trabajo | ⭐⭐ Costoso |
| C) No hacer nada | Sin esfuerzo | Confusión permanente | ❌ No recomendado |

---

### 12.2 Decisión 2: ¿Cómo manejar la IA?

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| **A) Extender para análisis completo** | Funcionalidad completa | Requiere prompts complejos | ⭐⭐⭐⭐ **RECOMENDADO** |
| B) Mantener solo generación | Simple, funciona | Gap con documento | ⭐⭐⭐ Aceptable |
| C) Usar API cloud (OpenAI) | Calidad superior | Costo, privacidad | ⭐⭐⭐⭐ Considerar |

---

### 12.3 Decisión 3: ¿Refactorizar ahora o después?

| Opción | Pros | Contras | Recomendación |
|--------|------|---------|---------------|
| A) Refactorizar ahora | Código limpio | Retrasa features | ⭐⭐⭐ Después de MVP |
| **B) Completar funcionalidad primero** | Valor de negocio | Deuda técnica | ⭐⭐⭐⭐ **RECOMENDADO** |
| C) Migrar directamente a FastAPI+React | Salto de calidad | Reescritura completa | ⭐⭐⭐⭐⭐ **Ideal post-validación** |

---

## 13. ROADMAP SUGERIDO

### Fase 0: INMEDIATO (1 semana)
1. ✅ Actualizar CONTEXTO_PROYECTO_TITA.md
2. ✅ Documentar arquitectura real (Streamlit)
3. ✅ Añadir autenticación básica
4. ✅ Crear tests unitarios básicos

### Fase 1: COMPLETAR MVP (4 semanas)
1. ✅ Extender IA para análisis de riesgos
2. ✅ Implementar dashboards con Plotly
3. ✅ Añadir comparativas entre evaluaciones
4. ✅ Implementar máquina de estados

### Fase 2: PROFESIONALIZAR (8 semanas)
1. ✅ Refactorizar a FastAPI backend
2. ✅ Implementar frontend React
3. ✅ Migrar a PostgreSQL
4. ✅ CI/CD y deployment

### Fase 3: ENTERPRISE (12 semanas)
1. ✅ RBAC granular
2. ✅ Auditoría completa
3. ✅ Multi-tenancy
4. ✅ Integración con SIEM

---

## 14. CONCLUSIONES FINALES

### 14.1 Estado del Proyecto

| Aspecto | Calificación | Comentario |
|---------|--------------|------------|
| **Funcionalidad Core** | 🟢 60% | Lo esencial funciona |
| **Arquitectura** | 🟡 40% | Monolítica, no escalable |
| **Documentación** | 🔴 20% | Desactualizada/incorrecta |
| **Seguridad** | 🔴 10% | Sin autenticación/autorización |
| **Testing** | 🔴 0% | No hay tests |
| **IA** | 🟡 30% | Solo preguntas, no análisis |
| **Dashboards** | 🔴 10% | Solo métricas básicas |

**Promedio General:** 🟡 **24% de completitud** respecto a lo documentado.

---

### 14.2 Es Este un Mal Proyecto?

**NO.** Es un proyecto en **etapa temprana** con:
- ✅ Concepto sólido (MAGERIT/ISO 27002)
- ✅ Innovaciones valiosas (versionado de cuestionarios)
- ✅ Código funcional (el flujo principal funciona)
- ✅ Potencial de crecimiento

**PERO:**
- ❌ Documentación desincronizada
- ❌ Funcionalidad IA incompleta
- ❌ Sin seguridad

---

### 14.3 Valor Académico vs. Valor Productivo

| Criterio | Académico | Productivo |
|----------|-----------|------------|
| **Concepto** | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐⭐ Bueno |
| **Metodología (MAGERIT)** | ⭐⭐⭐⭐⭐ Completo | ⭐⭐⭐⭐ Aplicable |
| **Implementación** | ⭐⭐⭐ Básica | ⭐⭐ Insuficiente |
| **Escalabilidad** | ⭐⭐ Limitada | ⭐ No escalable |
| **Seguridad** | ⭐ Sin implementar | ⭐ Crítico |

**Veredicto:**
- ✅ **Válido como proyecto académico** (demostración de concepto)
- ❌ **NO listo para producción** (requiere refactorización y seguridad)

---

## 15. RECOMENDACIÓN FINAL DEL ARQUITECTO

### Si el objetivo es ACADÉMICO (Capstone/Tesis):

**OPCIÓN 1: Actualizar Documentación**
1. Reescribir CONTEXTO_PROYECTO_TITA.md reflejando Streamlit
2. Documentar innovaciones (versionado, banco de preguntas)
3. Ser honesto sobre limitaciones
4. Demostrar funcionalidad real en defensa

**Esfuerzo:** 1 semana  
**Riesgo:** Bajo  
**Recomendación:** ⭐⭐⭐⭐⭐

---

### Si el objetivo es PRODUCCIÓN:

**OPCIÓN 2: Migración a FastAPI + React**
1. Usar `app.py` actual como **prueba de concepto**
2. Implementar backend FastAPI
3. Crear frontend React profesional
4. Migrar a PostgreSQL
5. Implementar autenticación/autorización

**Esfuerzo:** 3-6 meses  
**Riesgo:** Medio  
**Recomendación:** ⭐⭐⭐⭐

---

## 16. SIGUIENTES PASOS INMEDIATOS

### Acción 1: Reunión de Alineación
- ¿Cuál es el objetivo real? (académico vs. productivo)
- ¿Qué funcionalidad es crítica?
- ¿Cuál es el timeline?

### Acción 2: Decisión sobre IA
- ¿Implementar análisis completo de riesgos?
- ¿Mantener solo generación de preguntas?
- ¿Usar API cloud (OpenAI)?

### Acción 3: Priorizar Backlog
Según decisión anterior:
- [ ] Completar funcionalidad IA
- [ ] Implementar dashboards
- [ ] Añadir autenticación
- [ ] Refactorizar arquitectura
- [ ] Actualizar documentación

---

**FIN DEL ANÁLISIS**

---

**Firma Digital:**
Arquitecto de Software Experto en Ciberseguridad  
Fecha: 22 de Enero de 2026  
Versión del Análisis: 1.0

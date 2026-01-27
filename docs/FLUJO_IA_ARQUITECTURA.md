# 🤖 Arquitectura del Flujo de IA en TITA

## Diagrama de Flujo Principal

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USUARIO (Interfaz Streamlit)                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐               │
│  │ 📋 Cuestionario  │  │ 📦 Inventario    │  │ 🎯 Evaluación    │               │
│  │    (Respuestas)  │  │    (Activos)     │  │    (Contexto)    │               │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘               │
└───────────┼──────────────────────┼──────────────────────┼───────────────────────┘
            │                      │                      │
            ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        📊 CAPA DE DATOS (SQLite)                                │
│  ┌────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │ RESPUESTAS     │  │ INVENTARIO_     │  │ CATALOGO_AMENAZAS_MAGERIT (52)  │   │
│  │ (Cuestionario) │  │ ACTIVOS         │  │ CATALOGO_CONTROLES_ISO27002 (93)│   │
│  └────────┬───────┘  └────────┬────────┘  └──────────────┬──────────────────┘   │
└───────────┼───────────────────┼──────────────────────────┼──────────────────────┘
            │                   │                          │
            └─────────┬─────────┘                          │
                      ▼                                    │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     🧠 SERVICIO DE IA (ollama_magerit_service.py)               │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    PASO 1: CONSTRUCCIÓN DE CONTEXTO                       │  │
│  │  construir_contexto_activo()                                              │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ • Nombre y tipo del activo                                          │  │  │
│  │  │ • Criticidad del proceso                                            │  │  │
│  │  │ • Respuestas del cuestionario (todas las preguntas/respuestas)      │  │  │
│  │  │ • Formato: texto plano estructurado                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    PASO 2: CONSTRUCCIÓN DEL PROMPT                        │  │
│  │  construir_prompt_magerit()                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ ESTRUCTURA DEL PROMPT:                                              │  │  │
│  │  │ ────────────────────────────────────────────────────────────────────│  │  │
│  │  │ 1. ROL: "Experto en seguridad MAGERIT v3 + ISO 27002"               │  │  │
│  │  │                                                                     │  │  │
│  │  │ 2. CATÁLOGO DE AMENAZAS: (52 amenazas con código y descripción)     │  │  │
│  │  │    [A.1] Fuego, [A.2] Daños por agua, [A.3] Desastres naturales...  │  │  │
│  │  │                                                                     │  │  │
│  │  │ 3. CATÁLOGO DE CONTROLES: (93 controles ISO 27002)                  │  │  │
│  │  │    [5.1] Políticas de seguridad, [5.2] Roles y responsabilidades... │  │  │
│  │  │                                                                     │  │  │
│  │  │ 4. CONTEXTO DEL ACTIVO: (datos construidos en paso 1)               │  │  │
│  │  │                                                                     │  │  │
│  │  │ 5. INSTRUCCIONES: "Responde SOLO en JSON con esta estructura..."    │  │  │
│  │  │    - amenazas: [{codigo, dimension, justificacion, controles...}]   │  │  │
│  │  │    - probabilidad: 1-5                                              │  │  │
│  │  │    - observaciones: texto                                           │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    PASO 3: LLAMADA A OLLAMA                               │  │
│  │  llamar_ollama()                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ HTTP POST → http://localhost:11434/api/generate                     │  │  │
│  │  │                                                                     │  │  │
│  │  │ PARÁMETROS:                                                         │  │  │
│  │  │ • model: "llama3.2:1b" (configurable)                               │  │  │
│  │  │ • prompt: (construido en paso 2)                                    │  │  │
│  │  │ • stream: false                                                     │  │  │
│  │  │ • temperature: 0.3 (respuestas más determinísticas)                 │  │  │
│  │  │ • num_predict: 2000 tokens máximo                                   │  │  │
│  │  │ • timeout: 30 segundos                                              │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │                                                     │
            ▼                                                     ▼
┌───────────────────────────┐                     ┌───────────────────────────┐
│    ✅ RESPUESTA OK        │                     │    ❌ RESPUESTA FALLA     │
│   (JSON válido)           │                     │   (Timeout, error, etc)   │
└───────────────────────────┘                     └───────────────────────────┘
            │                                                     │
            ▼                                                     ▼
┌───────────────────────────┐                     ┌───────────────────────────┐
│ extraer_json_de_respuesta │                     │ generar_evaluacion_       │
│ validar_respuesta_ia()    │                     │ heuristica()              │
│                           │                     │                           │
│ • Verifica códigos existen│                     │ • Mapea tipo de activo    │
│   en catálogos            │                     │   a amenazas típicas      │
│ • Normaliza dimensiones   │                     │ • Usa reglas predefinidas │
│ • Limpia controles        │                     │ • Garantiza respuesta     │
└───────────────────────────┘                     └───────────────────────────┘
            │                                                     │
            └─────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     ⚙️ MOTOR MAGERIT (magerit_engine.py)                        │
│                                                                                 │
│  evaluar_activo_magerit()                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │  ENTRADA (desde IA):                                                      │  │
│  │  • amenazas_ia: [{codigo, dimension, justificacion, controles...}]        │  │
│  │  • probabilidad_ia: 1-5                                                   │  │
│  │  • observaciones_ia: texto                                                │  │
│  │                                                                           │  │
│  │  ─────────────────────────────────────────────────────────────────────    │  │
│  │                                                                           │  │
│  │  PROCESAMIENTO:                                                           │  │
│  │                                                                           │  │
│  │  1. 📊 CALCULAR IMPACTO DIC (desde respuestas cuestionario)               │  │
│  │     calcular_impacto_desde_respuestas()                                   │  │
│  │     → Disponibilidad: 1-5, Integridad: 1-5, Confidencialidad: 1-5         │  │
│  │                                                                           │  │
│  │  2. 🛡️ IDENTIFICAR CONTROLES EXISTENTES                                   │  │
│  │     identificar_controles_existentes()                                    │  │
│  │     → Lista de controles ya implementados según respuestas                │  │
│  │     → Efectividad base (0.0 - 1.0)                                        │  │
│  │                                                                           │  │
│  │  3. 🎯 PARA CADA AMENAZA DE LA IA:                                        │  │
│  │     a) Validar código existe en catálogo                                  │  │
│  │     b) Obtener impacto según dimensión (D, I, C)                          │  │
│  │     c) Riesgo Inherente = Probabilidad × Impacto                          │  │
│  │     d) Calcular riesgo residual con controles                             │  │
│  │     e) Procesar controles recomendados                                    │  │
│  │     f) Determinar tratamiento sugerido                                    │  │
│  │                                                                           │  │
│  │  4. 📈 CALCULAR GLOBALES:                                                 │  │
│  │     → Riesgo inherente global (promedio)                                  │  │
│  │     → Riesgo residual global                                              │  │
│  │     → Lista consolidada de controles recomendados                         │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  SALIDA: ResultadoEvaluacionMagerit                                       │  │
│  │  ────────────────────────────────────────────────────────────────────     │  │
│  │  • id_evaluacion, id_activo, nombre_activo, tipo_activo                   │  │
│  │  • impacto: {disponibilidad, integridad, confidencialidad}                │  │
│  │  • amenazas: [AmenazaIdentificada...]                                     │  │
│  │  • riesgo_inherente_global, nivel_riesgo_inherente_global                 │  │
│  │  • riesgo_residual_global, nivel_riesgo_residual_global                   │  │
│  │  • controles_existentes_global, controles_recomendados_global             │  │
│  │  • modelo_ia (con info si fue fallback)                                   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     💾 PERSISTENCIA EN BASE DE DATOS                            │
│                                                                                 │
│  guardar_resultado_magerit()                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │  Tablas actualizadas:                                                     │  │
│  │                                                                           │  │
│  │  • RESULTADOS_MAGERIT (resultado global por activo)                       │  │
│  │    └─ id_evaluacion, id_activo, riesgo_inherente, riesgo_residual...      │  │
│  │                                                                           │  │
│  │  • AMENAZAS_IDENTIFICADAS (detalle de cada amenaza)                       │  │
│  │    └─ codigo, dimension, probabilidad, impacto, riesgo, tratamiento...    │  │
│  │                                                                           │  │
│  │  • CONTROLES_RECOMENDADOS (controles ISO sugeridos)                       │  │
│  │    └─ codigo, nombre, prioridad, motivo, amenaza_origen...                │  │
│  │                                                                           │  │
│  │  • IA_EXECUTION_EVIDENCE (trazabilidad de ejecución)                      │  │
│  │    └─ timestamp, modelo, prompt_hash, respuesta_hash...                   │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Archivos Involucrados y Sus Roles

### 1. **ollama_magerit_service.py** (Orquestador Principal)
| Función | Descripción |
|---------|-------------|
| `get_catalogo_amenazas()` | Carga las 52 amenazas MAGERIT desde SQLite |
| `get_catalogo_controles()` | Carga los 93 controles ISO 27002 desde SQLite |
| `construir_contexto_activo()` | Construye texto con datos del activo + respuestas |
| `construir_prompt_magerit()` | Genera prompt estructurado con catálogos + contexto |
| `llamar_ollama()` | HTTP POST a Ollama (localhost:11434) |
| `extraer_json_de_respuesta()` | Extrae JSON del texto de respuesta |
| `validar_respuesta_ia()` | Valida que códigos existan en catálogos |
| `generar_evaluacion_heuristica()` | Fallback cuando IA falla |
| `analizar_activo_con_ia()` | **FUNCIÓN PRINCIPAL** - Orquesta todo el flujo |

### 2. **magerit_engine.py** (Motor de Cálculo)
| Función | Descripción |
|---------|-------------|
| `calcular_impacto_desde_respuestas()` | Calcula impacto D/I/C desde cuestionario |
| `identificar_controles_existentes()` | Extrae controles implementados de respuestas |
| `calcular_riesgo_residual()` | Aplica reducción por controles existentes |
| `get_nivel_riesgo()` | Clasifica: MUY BAJO, BAJO, MEDIO, ALTO, CRÍTICO |
| `get_tratamiento_sugerido()` | Sugiere: mitigar, aceptar, transferir, evitar |
| `evaluar_activo_magerit()` | **FUNCIÓN PRINCIPAL** - Cálculos MAGERIT completos |
| `guardar_resultado_magerit()` | Persiste resultados en SQLite |

### 3. **ia_validation_service.py** (Validación de Seguridad)
| Función | Descripción |
|---------|-------------|
| `verificar_endpoint_local()` | Confirma que Ollama corre en localhost |
| `verificar_sin_conexion_externa()` | Valida que no hay llamadas a Internet |
| `generar_token_canario()` | Crea tokens para detectar fugas de datos |
| `validar_ia_local()` | **FUNCIÓN PRINCIPAL** - Garantiza IA 100% local |

### 4. **knowledge_base_service.py** (Base de Conocimiento)
| Función | Descripción |
|---------|-------------|
| `cargar_catalogo_amenazas()` | Carga amenazas con contexto enriquecido |
| `cargar_catalogo_controles()` | Carga controles con mapeo a amenazas |
| `cargar_criterios_dic()` | Carga criterios de impacto D/I/C |
| `get_system_prompt()` | Genera system prompt con rol de experto TITA |

---

## 🔄 Flujo Simplificado (Paso a Paso)

```
1. USUARIO presiona "🤖 Evaluar Todos con MAGERIT"
           │
           ▼
2. app_final.py → llama analizar_activo_con_ia(eval_id, activo_id, modelo)
           │
           ▼
3. ollama_magerit_service.py:
   a) Carga catálogos (52 amenazas, 93 controles)
   b) Lee activo de INVENTARIO_ACTIVOS
   c) Lee respuestas de RESPUESTAS
   d) Construye contexto textual
   e) Construye prompt con catálogos + contexto
   f) POST a Ollama → recibe JSON
   g) Valida códigos contra catálogos
   h) Si falla → usa evaluación heurística
           │
           ▼
4. app_final.py → llama evaluar_activo_magerit(eval_id, activo_id, amenazas_ia, ...)
           │
           ▼
5. magerit_engine.py:
   a) Calcula impacto D/I/C desde respuestas
   b) Identifica controles existentes
   c) Para cada amenaza:
      - Riesgo Inherente = Probabilidad × Impacto
      - Riesgo Residual = Inherente × (1 - Efectividad)
   d) Calcula globales
   e) Retorna ResultadoEvaluacionMagerit
           │
           ▼
6. app_final.py → llama guardar_resultado_magerit(resultado)
           │
           ▼
7. Datos guardados en SQLite (RESULTADOS_MAGERIT, AMENAZAS_IDENTIFICADAS, etc.)
```

---

## 🧪 Ejemplo de Prompt Enviado a Ollama

```
Eres un experto en seguridad de la información especializado en MAGERIT v3 e ISO 27002.
Analiza el siguiente activo y determina las amenazas aplicables.

=== CATÁLOGO DE AMENAZAS MAGERIT ===
[A.1] Fuego - Daños causados por incendios
[A.2] Daños por agua - Inundaciones, goteras, humedad
[A.3] Desastres naturales - Terremotos, tormentas, etc.
[A.4] Daños por agentes externos - Contaminación, polvo, etc.
[A.5] Averías de origen físico - Fallos hardware
... (52 amenazas completas)

=== CATÁLOGO DE CONTROLES ISO 27002 ===
[5.1] Políticas de seguridad de la información
[5.2] Roles y responsabilidades de seguridad
[5.3] Segregación de funciones
... (93 controles completos)

=== ACTIVO A EVALUAR ===
Nombre: Servidor Base de Datos Principal
Tipo: Hardware
Criticidad: Alta

Respuestas del cuestionario:
- ¿El equipo tiene fuente de poder redundante? → No
- ¿Existe respaldo automático diario? → Sí
- ¿El acceso físico está restringido? → Sí, con tarjeta de acceso
... (todas las respuestas)

=== INSTRUCCIONES ===
Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{
  "amenazas": [
    {
      "codigo": "A.5",
      "dimension": "D",
      "justificacion": "El servidor no tiene redundancia de energía...",
      "controles_iso_recomendados": [
        {"control": "8.12", "prioridad": "Alta", "motivo": "Respaldo de datos críticos"}
      ]
    }
  ],
  "probabilidad": 3,
  "observaciones": "El activo presenta vulnerabilidades en..."
}

USA SOLO CÓDIGOS DEL CATÁLOGO. No inventes códigos.
```

---

## 🛡️ Mecanismo de Fallback (Cuando IA Falla)

Si Ollama no responde o el JSON es inválido, se activa `generar_evaluacion_heuristica()`:

```python
AMENAZAS_POR_TIPO = {
    "Hardware": ["A.5", "A.6", "A.23", "A.24", "A.25"],  # Averías, caída sistema, DoS
    "Software": ["A.8", "A.9", "A.10", "A.22"],          # Errores, malware, vulnerabilidades
    "Datos": ["A.15", "A.18", "A.19"],                  # Acceso no autorizado, fuga, manipulación
    "Personas": ["A.29", "A.30"],                        # Errores usuario, abuso privilegios
    "Instalaciones": ["A.1", "A.2", "A.3", "A.4"],       # Fuego, agua, desastres
    ...
}
```

Esto garantiza que **siempre** se genera una evaluación, aunque sea menos precisa.

---

## 📊 Tablas de Base de Datos Relacionadas con IA

| Tabla | Propósito |
|-------|-----------|
| `CATALOGO_AMENAZAS_MAGERIT` | 52 amenazas MAGERIT v3 (alimenta prompts) |
| `CATALOGO_CONTROLES_ISO27002` | 93 controles ISO 27002 (alimenta prompts) |
| `RESULTADOS_MAGERIT` | Resultados globales por activo evaluado |
| `AMENAZAS_IDENTIFICADAS` | Detalle de cada amenaza identificada |
| `CONTROLES_RECOMENDADOS` | Controles ISO sugeridos por la IA |
| `IA_STATUS` | Estado de validación de la IA |
| `IA_VALIDATION_LOG` | Log de validaciones de seguridad |
| `IA_EXECUTION_EVIDENCE` | Evidencia de ejecución (hashes, timestamps) |

---

## 🔒 Validación de IA Local

El servicio `ia_validation_service.py` garantiza que:

1. ✅ Ollama corre en `localhost:11434` (no servidor remoto)
2. ✅ No hay conexiones a dominios externos durante evaluación
3. ✅ Se generan tokens canario para detectar fugas
4. ✅ Se registra evidencia con hash SHA-256

```python
ENDPOINTS_LOCALES_PERMITIDOS = [
    "localhost",
    "127.0.0.1", 
    "0.0.0.0",
    "host.docker.internal"
]

DOMINIOS_BLOQUEADOS = [
    "openai.com",
    "anthropic.com",
    "azure.com",
    # ... etc
]
```

---

## 📈 Métricas de Evaluación

El motor MAGERIT calcula:

| Métrica | Fórmula |
|---------|---------|
| **Riesgo Inherente** | `Probabilidad × Impacto` (1-25) |
| **Riesgo Residual** | `Inherente × (1 - Efectividad)` |
| **Efectividad Controles** | Calculada según respuestas (0.0 - 1.0) |

Niveles de riesgo:
- **CRÍTICO**: ≥ 20
- **ALTO**: 12-19
- **MEDIO**: 6-11
- **BAJO**: 3-5
- **MUY BAJO**: 1-2

---

## 🎯 Resumen Ejecutivo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO RESUMIDO DE IA                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Cuestionario     →  Contexto textual                        │
│  📦 Inventario       →  Datos del activo                        │
│  📚 Catálogos        →  52 amenazas + 93 controles              │
│                           ↓                                     │
│                    ┌──────────────┐                             │
│                    │   PROMPT     │                             │
│                    │  CONSTRUIDO  │                             │
│                    └──────┬───────┘                             │
│                           ↓                                     │
│                    ┌──────────────┐                             │
│                    │   OLLAMA     │  ← localhost:11434          │
│                    │  llama3.2:1b │                             │
│                    └──────┬───────┘                             │
│                           ↓                                     │
│                    ┌──────────────┐                             │
│                    │  JSON con    │                             │
│                    │  amenazas +  │                             │
│                    │  controles   │                             │
│                    └──────┬───────┘                             │
│                           ↓                                     │
│                    ┌──────────────┐                             │
│                    │   MOTOR      │  ← Cálculos MAGERIT         │
│                    │   MAGERIT    │                             │
│                    └──────┬───────┘                             │
│                           ↓                                     │
│                    ┌──────────────┐                             │
│                    │   SQLite     │  ← Persistencia             │
│                    │   Database   │                             │
│                    └──────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**Documento generado para:** TITA - Sistema de Evaluación de Riesgos  
**Versión:** 2.5  
**Fecha:** 25 Enero 2026

---

## 🧠 MÓDULO IA AVANZADA (NUEVO v2.5)

### Diagrama de Flujo IA Avanzada

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        🤖 IA AVANZADA (Tab Independiente)                       │
│                                                                                 │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐   │
│  │ 📝 Planes de   │ │ 💬 Chatbot     │ │ 📋 Resumen     │ │ 🔮 Predicción  │   │
│  │   Tratamiento  │ │   MAGERIT      │ │   Ejecutivo    │ │   de Riesgo    │   │
│  └───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬────────┘   │
│          │                  │                  │                  │            │
│  ┌────────────────┐                                                            │
│  │ 🎯 Priorización│                                                            │
│  │   de Controles │                                                            │
│  └───────┬────────┘                                                            │
└──────────┼──────────────────┼──────────────────┼──────────────────┼────────────┘
           │                  │                  │                  │
           └──────────────────┴────────┬─────────┴──────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     🧠 SERVICIO IA AVANZADA (ia_advanced_service.py)            │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    FUNCIONES PRINCIPALES                                  │  │
│  │                                                                           │  │
│  │  1. generar_plan_tratamiento(eval_id, activo_id, codigo_amenaza, modelo)  │  │
│  │     → PlanTratamiento (acciones corto/mediano/largo plazo)                │  │
│  │                                                                           │  │
│  │  2. consultar_chatbot_magerit(eval_id, pregunta, historial, modelo)       │  │
│  │     → Respuesta contextualizada con datos de la evaluación                │  │
│  │                                                                           │  │
│  │  3. generar_resumen_ejecutivo(eval_id, modelo)                            │  │
│  │     → ResumenEjecutivo (hallazgos, recomendaciones, inversión)            │  │
│  │                                                                           │  │
│  │  4. generar_prediccion_riesgo(eval_id, meses, modelo)                     │  │
│  │     → PrediccionRiesgo (tendencia, proyecciones, factores)                │  │
│  │                                                                           │  │
│  │  5. generar_priorizacion_controles(eval_id, modelo)                       │  │
│  │     → List[ControlPriorizado] (ordenados por ROI de seguridad)            │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│                                       ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    LLAMADA A OLLAMA                                       │  │
│  │                                                                           │  │
│  │  llamar_ollama_avanzado(prompt, modelo, max_tokens, temperature)          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ HTTP POST → http://localhost:11434/api/generate                     │  │  │
│  │  │                                                                     │  │  │
│  │  │ PARÁMETROS OPTIMIZADOS:                                             │  │  │
│  │  │ • model: "llama3.2:1b" (ligero y rápido)                            │  │  │
│  │  │ • temperature: 0.3 (respuestas coherentes)                          │  │  │
│  │  │ • num_predict: 1500-2000 tokens                                     │  │  │
│  │  │ • timeout: 45 segundos                                              │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│            ┌──────────────────────────┴──────────────────────────┐              │
│            ▼                                                     ▼              │
│  ┌───────────────────────────┐                     ┌───────────────────────────┐│
│  │    ✅ RESPUESTA OK        │                     │    ❌ RESPUESTA FALLA     ││
│  │   (JSON válido)           │                     │   (Timeout, error, etc)   ││
│  │                           │                     │                           ││
│  │ extraer_json_seguro()     │                     │ Función _generar_xxx_     ││
│  │                           │                     │ heuristico()              ││
│  └───────────────────────────┘                     └───────────────────────────┘│
│                                       │                                         │
└───────────────────────────────────────┼─────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     💾 PERSISTENCIA DE RESULTADOS IA                            │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Tabla: IA_RESULTADOS_AVANZADOS                                           │  │
│  │                                                                           │  │
│  │  • id_evaluacion: TEXT (FK a EVALUACIONES)                                │  │
│  │  • tipo_resultado: TEXT (resumen_ejecutivo, prediccion_riesgo, etc.)      │  │
│  │  • datos_json: TEXT (resultado serializado)                               │  │
│  │  • fecha_generacion: TEXT                                                 │  │
│  │  • modelo_ia: TEXT                                                        │  │
│  │                                                                           │  │
│  │  UNIQUE(id_evaluacion, tipo_resultado) → Solo un resultado por tipo       │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  Funciones de persistencia:                                                     │
│  • guardar_resultado_ia(eval_id, tipo, datos, modelo)                           │
│  • cargar_resultado_ia(eval_id, tipo) → dict o None                             │
│  • eliminar_resultado_ia(eval_id, tipo)                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Persistencia (Regenerar vs Generar)

```
┌──────────────────────────────────────────────────────────────────┐
│                    FLUJO UI CON PERSISTENCIA                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Usuario abre tab IA Avanzada                                    │
│              │                                                   │
│              ▼                                                   │
│  ┌────────────────────────────────┐                              │
│  │  cargar_resultado_ia(eval_id,  │                              │
│  │  "resumen_ejecutivo")          │                              │
│  └───────────┬────────────────────┘                              │
│              │                                                   │
│     ┌────────┴────────┐                                          │
│     │                 │                                          │
│     ▼                 ▼                                          │
│  ┌──────────┐    ┌───────────┐                                   │
│  │ EXISTE   │    │ NO EXISTE │                                   │
│  │ resultado│    │ resultado │                                   │
│  └────┬─────┘    └─────┬─────┘                                   │
│       │                │                                         │
│       ▼                ▼                                         │
│  ┌───────────────┐  ┌───────────────┐                            │
│  │ 🔄 Regenerar  │  │ 📄 Generar    │  ← Botón mostrado          │
│  │   + Fecha     │  │   (Primary)   │                            │
│  └───────────────┘  └───────────────┘                            │
│              │                                                   │
│              ▼                                                   │
│  Usuario hace clic                                               │
│              │                                                   │
│              ▼                                                   │
│  ┌───────────────────────────────────┐                           │
│  │  Generar con IA                   │                           │
│  │  guardar_resultado_ia(...)        │                           │
│  │  st.rerun()                       │                           │
│  └───────────────────────────────────┘                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Dataclasses Principales

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
    distribucion_riesgo: Dict[str, int]
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
    proyecciones: Dict[str, float]       # {"mes_1": 10.5, "mes_3": 11.2}
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

### Servicio de Exportación (export_service.py)

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXPORTACIÓN PARA EJECUTIVOS                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ResumenEjecutivo                                               │
│         │                                                       │
│         ├──────► generar_documento_ejecutivo(resumen, "html")   │
│         │           └─► HTML profesional con CSS                │
│         │               • Header con logo y fecha               │
│         │               • Métricas en cards                     │
│         │               • Tabla de activos críticos             │
│         │               • Lista de hallazgos                    │
│         │               • Recomendaciones prioritarias          │
│         │               • Footer con disclaimer                 │
│         │                                                       │
│         ├──────► generar_documento_ejecutivo(resumen, "markdown")│
│         │           └─► Markdown para edición posterior         │
│         │                                                       │
│         └──────► resumen.to_dict()                              │
│                     └─► JSON para integración                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Integración con Power BI

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATASETS PARA POWER BI                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  generar_datos_powerbi(eval_id)                                 │
│         │                                                       │
│         └─► Dict[str, DataFrame] con 8 tablas:                  │
│                                                                 │
│             • Activos             → Inventario completo         │
│             • Resultados_MAGERIT  → Riesgos por activo          │
│             • Amenazas            → Detalle de amenazas         │
│             • Controles_Recomendados → ISO 27002 sugeridos      │
│             • Distribucion_Riesgos → Conteo por nivel           │
│             • Impacto_Dimensiones → Promedio DIC                │
│             • Tipos_Amenaza       → Categorías                  │
│             • Metadata            → Info de evaluación          │
│                                                                 │
│  exportar_powerbi_excel(eval_id, ruta)                          │
│         └─► Excel multi-hoja (.xlsx)                            │
│             • Una hoja por dataset                              │
│             • Listo para importar en Power BI                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Chatbot Consultor MAGERIT

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHATBOT MAGERIT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Usuario escribe pregunta                                       │
│         │                                                       │
│         ▼                                                       │
│  consultar_chatbot_magerit(eval_id, pregunta, historial, modelo)│
│         │                                                       │
│         ├─► Carga contexto de la evaluación:                    │
│         │   • Total activos, amenazas                           │
│         │   • Distribución de riesgos                           │
│         │   • Top 5 activos más críticos                        │
│         │                                                       │
│         ├─► Construye prompt con:                               │
│         │   • Rol: "Consultor experto MAGERIT"                  │
│         │   • Contexto de evaluación                            │
│         │   • Historial de conversación                         │
│         │   • Pregunta actual                                   │
│         │                                                       │
│         └─► Llama a Ollama (temperature: 0.3)                   │
│                   │                                             │
│                   ▼                                             │
│         Respuesta coherente y contextualizada                   │
│                                                                 │
│  Historial guardado en: st.session_state["ia_chat_history"]     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Archivos del Módulo IA Avanzada

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `services/ia_advanced_service.py` | Servicios principales de IA Avanzada | ~1270 |
| `components/ia_advanced_ui.py` | Interfaz de usuario Streamlit | ~950 |
| `services/export_service.py` | Exportación HTML/MD/Excel | ~500 |

### Funciones Clave por Archivo

**ia_advanced_service.py:**
| Función | Descripción |
|---------|-------------|
| `generar_plan_tratamiento()` | Plan de acciones para amenaza específica |
| `generar_planes_evaluacion()` | Planes para todas las amenazas críticas |
| `consultar_chatbot_magerit()` | Respuesta del chatbot contextualizada |
| `generar_resumen_ejecutivo()` | Informe para alta gerencia |
| `generar_prediccion_riesgo()` | Proyección de riesgo futuro |
| `generar_priorizacion_controles()` | Ordenamiento por ROI |
| `obtener_amenazas_evaluacion()` | Extrae amenazas de JSON |
| `obtener_controles_evaluacion()` | Extrae controles de JSON |
| `guardar_resultado_ia()` | Persiste resultado en BD |
| `cargar_resultado_ia()` | Recupera resultado de BD |

**export_service.py:**
| Función | Descripción |
|---------|-------------|
| `generar_documento_ejecutivo()` | HTML/MD/TXT profesional |
| `_generar_html_ejecutivo()` | Template HTML con CSS |
| `generar_datos_powerbi()` | 8 DataFrames optimizados |
| `exportar_powerbi_excel()` | Excel multi-hoja |

---
## 🔄 FLUJO DE REEVALUACIÓN Y CONTROLES IMPLEMENTADOS

Este flujo permite justificar la reducción de riesgo entre evaluaciones comparando los controles recomendados vs implementados.

### Diagrama del Flujo de Reevaluación

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EVALUACIÓN 1 (ANTERIOR)                               │
│                                                                                 │
│  1. Usuario completa cuestionarios                                              │
│  2. IA analiza activos con MAGERIT                                              │
│  3. Sistema genera:                                                             │
│     • Lista de AMENAZAS identificadas                                           │
│     • Lista de CONTROLES RECOMENDADOS (ISO 27002)                               │
│     • Riesgo Inherente y Residual por activo                                    │
│                                                                                 │
│  RESULTADOS_MAGERIT.Amenazas_JSON contiene:                                     │
│  └─► controles_recomendados: [{codigo, nombre, prioridad, motivo}]              │
│                                                                                 │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PERÍODO ENTRE EVALUACIONES                                   │
│                                                                                 │
│  El usuario/organización:                                                       │
│  ✅ Implementa controles recomendados                                           │
│  ✅ Documenta las implementaciones                                              │
│  ✅ Mejora procesos y tecnología                                                │
│                                                                                 │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EVALUACIÓN 2 (ACTUAL)                                 │
│                                                                                 │
│  1. Usuario crea nueva evaluación                                               │
│  2. Agrega los mismos activos (u otros)                                         │
│  3. Completa cuestionarios (respuestas pueden variar)                           │
│  4. IA analiza activos con MAGERIT                                              │
│     └─► La IA DETECTA los controles ahora implementados                         │
│                                                                                 │
│  RESULTADOS_MAGERIT.Amenazas_JSON contiene:                                     │
│  └─► controles_existentes: ["8.6", "8.22", "5.15", ...]                         │
│  └─► efectividad_controles: 0.35 (35% de reducción)                             │
│  └─► riesgo_residual: menor que en Eval1                                        │
│                                                                                 │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    TAB 🔄 COMPARATIVAS - CONTROLES IMPLEMENTADOS                │
│                                                                                 │
│  El usuario selecciona:                                                         │
│  • Evaluación 1 (Anterior)                                                      │
│  • Evaluación 2 (Actual)                                                        │
│                                                                                 │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│  LÓGICA DE COMPARACIÓN (app_final.py):                                          │
│                                                                                 │
│  1. obtener_amenazas_evaluacion(eval_1)                                         │
│     └─► Extrae controles_recomendados de cada amenaza                           │
│     └─► Crea lista única de controles sugeridos                                 │
│                                                                                 │
│  2. obtener_amenazas_evaluacion(eval_2)                                         │
│     └─► Extrae controles_existentes de cada amenaza                             │
│     └─► Crea set de controles detectados como implementados                     │
│                                                                                 │
│  3. MATCHING:                                                                   │
│     Si control_recomendado_eval1 IN controles_existentes_eval2:                 │
│        → Estado = "✅ IMPLEMENTADO"                                             │
│     Else:                                                                       │
│        → Estado = "⏳ Pendiente"                                                 │
│                                                                                 │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│  SALIDA VISUAL:                                                                 │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐            │
│  │ 📊 MÉTRICAS                                                     │            │
│  │ • Controles Recomendados: 15                                    │            │
│  │ • Implementados: 9                                              │            │
│  │ • % Cumplimiento: 60%                                           │            │
│  └─────────────────────────────────────────────────────────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐            │
│  │ 📋 TABLA DE CONTROLES                                           │            │
│  │ Código │ Control              │ Prioridad │ Estado              │            │
│  │ 8.22   │ Segregación de redes │ ALTA      │ ✅ IMPLEMENTADO     │            │
│  │ 8.6    │ Gestión de capacidad │ MEDIA     │ ✅ IMPLEMENTADO     │            │
│  │ 5.15   │ Control de acceso    │ ALTA      │ ⏳ Pendiente        │            │
│  └─────────────────────────────────────────────────────────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐            │
│  │ ✅ JUSTIFICACIÓN DE MEJORA                                      │            │
│  │ "Se implementaron 9 de 15 controles recomendados (60%),         │            │
│  │  lo cual contribuyó a reducir el riesgo residual promedio       │            │
│  │  en 3.2 puntos."                                                │            │
│  └─────────────────────────────────────────────────────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Código Clave del Flujo

```python
# En app_final.py - Tab Comparativas

# 1. Obtener amenazas de ambas evaluaciones
amenazas_eval1 = obtener_amenazas_evaluacion(eval_1)
amenazas_eval2 = obtener_amenazas_evaluacion(eval_2)

# 2. Extraer controles recomendados de Eval1
controles_recomendados_eval1 = []
for _, row in amenazas_eval1.iterrows():
    ctrls = row.get("controles_recomendados", [])
    for ctrl in ctrls:
        controles_recomendados_eval1.append({
            "codigo": ctrl["codigo"],
            "nombre": ctrl["nombre"],
            "prioridad": ctrl["prioridad"],
            "amenaza": row["amenaza"],
            "activo": row["nombre_activo"]
        })

# 3. Extraer controles existentes de Eval2
controles_existentes_eval2 = set()
for _, row in amenazas_eval2.iterrows():
    ctrls_exist = row.get("controles_existentes", [])
    for c in ctrls_exist:
        controles_existentes_eval2.add(c)

# 4. Matching: ¿El control recomendado fue implementado?
for ctrl in controles_recomendados_eval1:
    implementado = ctrl["codigo"] in controles_existentes_eval2
    estado = "✅ IMPLEMENTADO" if implementado else "⏳ Pendiente"

# 5. Calcular métricas
total_recomendados = len(controles_recomendados_eval1)
implementados = len([c for c in tabla if "IMPLEMENTADO" in c["Estado"]])
pct_cumplimiento = (implementados / total_recomendados * 100)

# 6. Justificación si hay mejora
if implementados > 0 and delta_riesgo_residual < 0:
    st.success(f"Se implementaron {implementados} controles, "
               f"reduciendo el riesgo en {abs(delta_riesgo_residual):.1f} puntos")
```

### Campos Utilizados en Amenazas_JSON

| Campo | Eval1 (Anterior) | Eval2 (Actual) | Propósito |
|-------|------------------|----------------|-----------|
| `controles_recomendados` | ✅ Se usa | - | Lista de controles sugeridos por IA |
| `controles_existentes` | - | ✅ Se usa | Controles detectados como implementados |
| `efectividad_controles` | 0.1 (baja) | 0.4 (mejorada) | % de reducción de riesgo |
| `riesgo_residual` | Alto | Menor | Resultado del cálculo con controles |

### Función obtener_amenazas_evaluacion()

Ubicación: `services/ia_advanced_service.py`

```python
def obtener_amenazas_evaluacion(eval_id: str) -> pd.DataFrame:
    """
    Extrae las amenazas de una evaluación desde RESULTADOS_MAGERIT.Amenazas_JSON.
    Retorna DataFrame con columnas:
    - id_evaluacion, id_activo, nombre_activo
    - codigo, amenaza, tipo_amenaza, dimension
    - probabilidad, impacto, riesgo_inherente, riesgo_residual
    - controles_existentes, efectividad_controles
    - controles_recomendados
    """
```

---
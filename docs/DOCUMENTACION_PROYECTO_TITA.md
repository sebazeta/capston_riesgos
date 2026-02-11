# DOCUMENTACIÓN DEL PROYECTO TITA
## Sistema de Gestión de Riesgos basado en Metodología MAGERIT v3

---

# ÍNDICE

1. [Introducción](#1-introducción)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Descripción de los Tabs](#3-descripción-de-los-tabs)
4. [Resultados de la Evaluación](#4-resultados-de-la-evaluación)
5. [Guía de Documentación](#5-guía-de-documentación)

---

# 1. INTRODUCCIÓN

## 1.1 Propósito del Sistema

TITA (Tool for IT Assessment) es un sistema de evaluación de riesgos de TI que implementa la metodología MAGERIT v3 (Metodología de Análisis y Gestión de Riesgos de los Sistemas de Información) desarrollada por el Consejo Superior de Administración Electrónica de España.

## 1.2 Objetivos

- Inventariar activos de TI de la organización
- Valorar activos en dimensiones de seguridad (D/I/C)
- Identificar vulnerabilidades y amenazas
- Calcular niveles de riesgo
- Recomendar salvaguardas/controles
- Medir el nivel de madurez de gestión de riesgos
- Permitir reevaluaciones periódicas

## 1.3 Metodología

El sistema sigue el flujo MAGERIT:

```
Activos → Valoración D/I/C → Amenazas → Impacto → Frecuencia → Riesgo → Salvaguardas
```

---

# 2. ARQUITECTURA DEL SISTEMA

## 2.1 Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Frontend | Streamlit |
| Backend | Python 3.x |
| Base de Datos | SQLite |
| IA Local | Ollama (Llama 3.2) |
| Visualización | Plotly |
| Procesamiento | Pandas |

## 2.2 Estructura de Tablas

| Tabla | Propósito |
|-------|-----------|
| EVALUACIONES | Registro de evaluaciones de riesgo |
| INVENTARIO_ACTIVOS | Catálogo de activos de TI |
| IDENTIFICACION_VALORACION | Valoración D/I/C de activos |
| VULNERABILIDADES_AMENAZAS | Vulnerabilidades y amenazas identificadas |
| RIESGO_AMENAZA | Cálculo de riesgos por amenaza |
| MAPA_RIESGOS | Visualización matricial de riesgos |
| RIESGO_ACTIVOS | Agregación de riesgos por activo |
| SALVAGUARDAS | Controles recomendados e implementados |
| RESULTADOS_MADUREZ | Nivel de madurez calculado |
| HISTORIAL_REEVALUACIONES | Registro histórico de reevaluaciones |

---

# 3. DESCRIPCIÓN DE LOS TABS

## Tab 1: 📏 Criterios de Valoración

### Propósito
Define las escalas de medición utilizadas en todo el modelo MAGERIT. Estas escalas son la referencia para valorar activos, degradación y frecuencia.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Escala de Disponibilidad** | Tabla con niveles N/B/M/A y sus valores numéricos (0.25-1.0) |
| **Escala de Integridad** | Tabla con niveles N/B/M/A y sus valores numéricos |
| **Escala de Confidencialidad** | Tabla con niveles N/B/M/A y sus valores numéricos |
| **Escala de Criticidad** | Tabla con niveles NULA/BAJA/MEDIA/ALTA |
| **Escala de Frecuencia** | Valores de probabilidad de ocurrencia (0.1-3.0) |
| **Escala de Degradación** | Porcentaje de afectación por dimensión |
| **Fórmulas del Modelo** | Explicación de cálculos MAGERIT |
| **Catálogos MAGERIT** | Amenazas, Controles ISO 27002, Salvaguardas, Vulnerabilidades |

### Fórmulas Clave
```
IMPACTO = MAX(Valor_D × Degradación_D, Valor_I × Degradación_I, Valor_C × Degradación_C)
RIESGO = FRECUENCIA × IMPACTO
CRITICIDAD = MAX(Valor_D, Valor_I, Valor_C)
```

---

## Tab 2: 📦 Inventario de Activos

### Propósito
Registrar y gestionar el inventario completo de activos de TI que serán evaluados.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Métricas Superiores** | Total de activos, tipos únicos, responsables |
| **Formulario Individual** | Agregar activos uno por uno con todos los campos |
| **Carga Masiva** | Importar activos desde JSON o Excel |
| **Tabla de Activos** | Lista completa con opciones de editar/eliminar |
| **Filtro de Tipo** | Filtrar por tipo de activo |

### Campos por Activo
- ID del Activo
- Nombre del Activo
- Tipo (Servidor Virtual, Servidor Físico, etc.)
- Ubicación
- Responsable
- Descripción
- Sistema Operativo
- Dirección IP (opcional)

---

## Tab 3: ⚖️ Valoración D/I/C

### Propósito
Valorar cada activo en las tres dimensiones de seguridad: Disponibilidad, Integridad y Confidencialidad, utilizando un cuestionario guiado.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Selector de Activo** | Dropdown para elegir activo a valorar |
| **Cuestionario por Tipo** | Preguntas específicas según el tipo de activo |
| **Indicadores D/I/C** | Métricas que muestran los valores calculados |
| **Indicador de Criticidad** | Valor máximo de D/I/C con color según nivel |
| **Resumen de Valoraciones** | Tabla con todas las valoraciones completadas |
| **Gráfico de Radar** | Visualización de D/I/C por activo |

### Metodología de Valoración
El cuestionario contiene preguntas como:
- "¿Cuánto tiempo puede estar inactivo el servicio sin impacto grave?"
- "¿Qué tan sensible es la información manejada?"
- "¿Cuál sería el impacto si los datos son modificados sin autorización?"

Las respuestas se mapean a valores:
- **N (Nula)**: 0.25
- **B (Baja)**: 0.50
- **M (Media)**: 0.75
- **A (Alta)**: 1.00

---

## Tab 4: 🔓 Vulnerabilidades y Amenazas

### Propósito
Identificar automáticamente vulnerabilidades y amenazas utilizando IA local (Ollama), basándose en la criticidad del activo.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Panel de Estado IA** | Muestra si Ollama está activo y qué modelo usa |
| **Selector de Activo** | Individual o análisis masivo |
| **Botón de Análisis IA** | Ejecuta el análisis con IA |
| **Tabla de Resultados** | Amenazas identificadas con código, descripción, degradación |
| **Indicador de Impacto** | Cálculo automático del impacto por dimensión |
| **Tabla Unificada** | Todas las vulnerabilidades/amenazas de la evaluación |

### Proceso de Análisis IA
1. La IA recibe el tipo de activo y su valoración D/I/C
2. Identifica amenazas del catálogo MAGERIT relevantes
3. Sugiere vulnerabilidades asociadas
4. Calcula la degradación según la criticidad
5. Genera el impacto total

### Fórmula de Impacto
```
Impacto_D = Valor_D × Degradación_D
Impacto_I = Valor_I × Degradación_I
Impacto_C = Valor_C × Degradación_C
IMPACTO_TOTAL = MAX(Impacto_D, Impacto_I, Impacto_C)
```

---

## Tab 5: ⚡ Cálculo de Riesgo

### Propósito
Calcular el nivel de riesgo para cada par activo-amenaza identificado.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Escalas de Referencia** | Tablas con frecuencias e impactos MAGERIT |
| **Badge de Estado** | Indica si los riesgos ya fueron calculados |
| **Botón Calcular Riesgos** | Ejecuta el cálculo masivo |
| **Tabla de Riesgos** | Lista con Amenaza, Impacto, Frecuencia, Riesgo |
| **Indicadores de Color** | Verde/Amarillo/Naranja/Rojo según nivel |
| **Resumen por Nivel** | Conteo de riesgos ALTOS/MEDIOS/BAJOS |

### Fórmula MAGERIT
```
RIESGO = FRECUENCIA × IMPACTO
```

### Escala de Frecuencia
| Nivel | Valor | Descripción |
|-------|-------|-------------|
| Nula | 0.1 | Muy improbable |
| Baja | 1.0 | Poco frecuente |
| Media | 2.0 | Moderada |
| Alta | 3.0 | Muy frecuente |

---

## Tab 6: 🗺️ Mapa de Riesgos

### Propósito
Visualizar los riesgos en una matriz de calor (Impacto vs Frecuencia).

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Métricas Resumen** | Total riesgos, ALTOS, MEDIOS, BAJOS, NULOS |
| **Matriz de Calor** | Heatmap 4x4 con colores según gravedad |
| **Leyenda de Colores** | Interpretación de zonas de riesgo |
| **Lista de Riesgos** | Tabla detallada con ID, Impacto, Frecuencia, Riesgo |
| **Botón Guardar Mapa** | Persiste el mapa en la base de datos |

### Interpretación del Mapa de Calor
| Color | Zona | Acción Requerida |
|-------|------|------------------|
| 🟢 Verde | Riesgo Bajo | Monitorear |
| 🟡 Amarillo | Riesgo Medio-Bajo | Planificar controles |
| 🟠 Naranja | Riesgo Medio-Alto | Implementar controles |
| 🔴 Rojo | Riesgo Alto | Acción urgente |

---

## Tab 7: 📊 Riesgos por Activo

### Propósito
Consolidar el riesgo por activo con objetivos y límites organizacionales.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Métricas Generales** | Total activos, riesgo promedio, máximo, sobre límite |
| **Tabla Principal** | Activo, Riesgo Actual, Objetivo, Límite, Estado, Observaciones |
| **Gráfico Radar** | Visualización comparativa por activo |
| **Gráfico de Barras** | Riesgo Actual vs Objetivo vs Límite |
| **Indicadores de Estado** | Semáforo por activo (Urgente/Atención/Aceptable) |

### Columnas de la Tabla
- **Riesgo Actual**: Promedio de todos los riesgos del activo
- **Objetivo**: Meta de riesgo = Actual × 0.7
- **Límite**: Umbral máximo aceptable (4.0 por defecto)
- **Observaciones**: Recomendaciones automáticas

---

## Tab 8: 🛡️ Salvaguardas

### Propósito
Gestionar los controles de seguridad recomendados para mitigar riesgos.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Métricas de Salvaguardas** | Total, Implementadas, Planificadas, Pendientes |
| **Botón Generar con IA** | Genera salvaguardas automáticamente |
| **Tabla por Activo** | Lista de salvaguardas agrupadas |
| **Selector de Estado** | Implementada/Planificada/Pendiente/No Aplica |
| **Prioridad** | Alta/Media/Baja con colores |
| **Código ISO 27002** | Referencia al control estándar |

### Estados de Salvaguardas
| Estado | Significado |
|--------|-------------|
| Implementada | Control activo y funcionando |
| Planificada | Programada para implementación |
| Pendiente | Identificada pero sin plan |
| No Aplica | No relevante para el activo |

---

## Tab 9: 🎯 Nivel de Madurez

### Propósito
Evaluar el nivel de madurez de la gestión de riesgos de TI.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Gráfico Gauge** | Medidor visual con escala de colores por nivel |
| **Indicador de Nivel** | Número grande con nombre del nivel |
| **Componentes de Puntuación** | Distribución de Riesgos (60%), Severidad (40%) |
| **Gráfico de Barras** | Puntuación por componente |
| **Gráfico de Dona** | Contribución a la puntuación total |
| **Distribución de Riesgos** | Métricas ALTOS/MEDIOS/BAJOS/MÁXIMO |
| **Interpretación del Nivel** | Descripción y recomendaciones |
| **Detalles Técnicos** | Fórmula de cálculo expandible |
| **Historial de Evaluaciones** | Selector para ver evaluaciones anteriores |
| **Historial de Reevaluaciones** | Evolución de madurez en el tiempo |

### Niveles de Madurez
| Nivel | Nombre | Rango | Descripción |
|-------|--------|-------|-------------|
| 1 | Inicial | 0-19 | Riesgos críticos sin tratar |
| 2 | Básico | 20-39 | Algunos riesgos altos |
| 3 | Definido | 40-59 | Mayoría en zona baja |
| 4 | Gestionado | 60-79 | Pocos riesgos altos |
| 5 | Optimizado | 80-100 | Sin riesgos críticos |

### Fórmula de Madurez (Tab 9 - Inherente)
```
Puntuación = (Distribución_Riesgos × 0.60) + (Severidad_Riesgo × 0.40)

Donde:
- Distribución_Riesgos = % de riesgos en zona BAJA con penalización por ALTOS
- Severidad_Riesgo = Inverso del riesgo máximo
```

---

## Tab 10: 🔄 Reevaluación y Comparativa

### Propósito
Realizar reevaluaciones periódicas y comparar el estado actual vs anterior.

### Componentes Visuales

| Componente | Descripción |
|------------|-------------|
| **Panel de Estado** | Verificación de requisitos completados |
| **Fases del Proceso** | Wizard de 4 pasos para reevaluación |
| **Métricas Comparativas** | Riesgo, Madurez, Nivel, Activos con deltas |
| **Gráfico de Barras** | Antes vs Después |
| **Gráfico Gauge** | Madurez con comparación |
| **Tabla Comparativa** | Resumen detallado de cambios |
| **Gráfico por Activo** | Evolución de riesgo por activo |
| **Distribución de Riesgo** | Gráficos circulares Antes/Después |
| **Resumen de Salvaguardas** | Lista de controles implementados |
| **Conclusión** | Análisis automático de mejora/deterioro |

### Fases de Reevaluación
1. **Inicio**: Revisión del estado actual
2. **Cambios en Activos**: Registrar nuevos/eliminados/modificados
3. **Salvaguardas Implementadas**: Marcar controles aplicados
4. **Resultados**: Comparativa y guardado en historial

### Fórmula de Madurez (Tab 10 - Con Controles)
```
Puntuación = (Nivel_Riesgo_Controlado × 0.40) + 
             (Salvaguardas_Implementadas × 0.35) + 
             (Riesgo_Residual_Bajo × 0.25)
```

---

# 4. RESULTADOS DE LA EVALUACIÓN

## 4.1 Datos de la Evaluación Principal

### Información General
| Campo | Valor |
|-------|-------|
| **ID Evaluación** | EVA-001 |
| **Nombre** | inicio |
| **Estado** | En Progreso |
| **Fecha de Creación** | 2026-01-29 23:54:34 |
| **Responsable** | seguridad |

---

### 4.2 Inventario de Activos

| Métrica | Valor |
|---------|-------|
| **Total de Activos** | 72 |
| **Servidores Virtuales** | 47 |
| **Servidores Físicos** | 25 |

#### Distribución por Tipo
```
Servidores Virtuales: 65.3%
Servidores Físicos: 34.7%
```

#### Listado de Activos (Muestra)
| Nombre | Tipo |
|--------|------|
| SNSQL10 | Servidor Virtual |
| SNSQL07 | Servidor Virtual |
| SNSQL01N1 | Servidor Virtual |
| OCREG04 | Servidor Físico |
| OCREG03 | Servidor Físico |
| BASTION_PROD | Servidor Físico |
| ... | ... |

---

### 4.3 Valoraciones D/I/C

| Métrica | Valor |
|---------|-------|
| **Activos Valorados** | 72 (100%) |

Todos los activos tienen valoración completa en las dimensiones:
- Disponibilidad (D)
- Integridad (I)
- Confidencialidad (C)

---

### 4.4 Análisis de Riesgos

| Métrica | Valor |
|---------|-------|
| **Total de Riesgos Identificados** | 409 |
| **Riesgo Promedio** | 5.81 |
| **Riesgo Máximo** | 9.00 |
| **Riesgo Mínimo** | 0.55 |

#### Distribución de Riesgos por Nivel

| Nivel | Cantidad | Porcentaje |
|-------|----------|------------|
| 🔴 ALTO (≥6) | 211 | 51.6% |
| 🟡 MEDIO (4-5.99) | 126 | 30.8% |
| 🟢 BAJO (<4) | 72 | 17.6% |

#### Gráfico de Distribución
```
ALTO   ████████████████████████████████████████████████████ 51.6%
MEDIO  ██████████████████████████████ 30.8%
BAJO   █████████████████ 17.6%
```

**Análisis**: Más del 50% de los riesgos identificados están en zona ALTA, lo que indica una situación crítica que requiere atención urgente.

---

### 4.5 Salvaguardas

| Métrica | Valor |
|---------|-------|
| **Total de Salvaguardas** | 409 |
| **Implementadas** | 169 (41.3%) |
| **Pendientes** | 240 (58.7%) |

#### Estado de Implementación
```
Implementadas ████████████████████████████████████████ 41.3%
Pendientes    ██████████████████████████████████████████████████████████ 58.7%
```

---

### 4.6 Nivel de Madurez

| Componente | Valor |
|------------|-------|
| **Puntuación Total** | 10.5/100 |
| **Nivel de Madurez** | 1 - Inicial |
| **Pct. Controles Implementados** | 18.3% |
| **Pct. Controles Medidos** | 0.0% |
| **Pct. Riesgos Mitigados** | 16.4% |

#### Gráfico de Madurez
```
Nivel 5 - Optimizado   [80-100] ░░░░░░░░░░░░░░░░░░░░
Nivel 4 - Gestionado   [60-79]  ░░░░░░░░░░░░░░░░░░░░
Nivel 3 - Definido     [40-59]  ░░░░░░░░░░░░░░░░░░░░
Nivel 2 - Básico       [20-39]  ░░░░░░░░░░░░░░░░░░░░
Nivel 1 - Inicial      [0-19]   ██████████░░░░░░░░░░ ← 10.5
```

#### Interpretación
El nivel de madurez **INICIAL (Nivel 1)** indica que:
- La gestión de riesgos de TI está en etapa temprana
- Más del 50% de los riesgos están en zona ALTA
- La mayoría de las salvaguardas no están implementadas
- Se requiere acción urgente para reducir riesgos críticos

---

### 4.7 Recomendaciones para Mejorar

Basado en el análisis, se recomiendan las siguientes acciones:

1. **Priorizar activos críticos**: Identificar los 10 activos con mayor riesgo y enfocar esfuerzos
2. **Reducir riesgos ALTOS**: Implementar salvaguardas urgentes para los 211 riesgos en zona ALTA
3. **Implementar controles básicos**: 
   - Backups automatizados
   - Control de acceso robusto
   - Actualizaciones de seguridad
   - Monitoreo de logs
4. **Capacitar al personal**: Concientización en seguridad informática
5. **Documentar procedimientos**: Crear SOPs de respuesta a incidentes

---

### 4.8 Reevaluación (Pendiente)

Al momento de la documentación, no se han realizado reevaluaciones formales.

Para realizar una reevaluación:
1. Ir al Tab 10 (Comparativa)
2. Marcar las salvaguardas implementadas desde la última evaluación
3. El sistema calculará automáticamente:
   - Nuevo nivel de riesgo
   - Nueva puntuación de madurez
   - Comparativa antes/después
4. Guardar los resultados para el historial

---

# 5. GUÍA DE DOCUMENTACIÓN

## 5.1 Estructura Recomendada

Para documentar el proyecto TITA, se recomienda la siguiente estructura:

```
📁 Documentación TITA
├── 📄 1. Introducción y Alcance
├── 📄 2. Marco Teórico (MAGERIT, ISO 27002)
├── 📄 3. Arquitectura del Sistema
├── 📄 4. Manual de Usuario (por Tab)
├── 📄 5. Resultados de Evaluación
│   ├── 5.1 Inventario de Activos
│   ├── 5.2 Valoraciones D/I/C
│   ├── 5.3 Análisis de Riesgos
│   ├── 5.4 Mapa de Riesgos
│   ├── 5.5 Salvaguardas
│   └── 5.6 Nivel de Madurez
├── 📄 6. Reevaluaciones y Comparativas
├── 📄 7. Conclusiones y Recomendaciones
└── 📄 8. Anexos (Catálogos, Cuestionarios)
```

## 5.2 Cómo Exportar Datos

El sistema permite exportar datos en varios formatos:

| Dato | Ubicación | Formato |
|------|-----------|---------|
| Matriz Completa | Sidebar → Descargar Excel | XLSX |
| Lista de Riesgos | Tab 6 → Descargar CSV | CSV |
| Riesgos por Activo | Tab 7 → Descargar CSV | CSV |
| Historial Reevaluaciones | Tab 9 → Exportar | CSV |
| Resumen Evaluación | Tab 9 → Historial → Exportar | CSV |

## 5.3 Capturas de Pantalla Recomendadas

Para documentación visual, capturar:

1. **Tab 1**: Escalas de valoración
2. **Tab 3**: Cuestionario D/I/C completado
3. **Tab 5**: Tabla de riesgos calculados
4. **Tab 6**: Mapa de calor de riesgos
5. **Tab 7**: Gráfico radar de riesgos por activo
6. **Tab 9**: Gauge de madurez con nivel
7. **Tab 10**: Comparativa antes/después (si hay reevaluación)

## 5.4 Métricas Clave a Reportar

| Métrica | Fórmula/Origen | Importancia |
|---------|----------------|-------------|
| Total Activos | Conteo Tab 2 | Alcance de la evaluación |
| Riesgo Promedio | Promedio Tab 5 | Estado general |
| % Riesgos ALTOS | (Altos/Total)×100 | Urgencia de acción |
| Nivel de Madurez | Cálculo Tab 9 | Estado de gestión |
| % Salvaguardas Impl. | (Impl/Total)×100 | Progreso de controles |
| Delta Madurez | Nuevo - Anterior | Mejora en reevaluación |

---

# ANEXO: DATOS TÉCNICOS

## Conexión a Base de Datos
```python
from services.database_service import get_connection
```

## Cálculo de Madurez
```python
from services.maturity_service import calcular_madurez_evaluacion

# Madurez inherente (sin controles)
resultado = calcular_madurez_evaluacion(eval_id, considerar_salvaguardas=False)

# Madurez con controles aplicados
resultado = calcular_madurez_evaluacion(eval_id, considerar_salvaguardas=True)
```

## Historial de Reevaluaciones
```python
from services.maturity_service import guardar_reevaluacion, get_historial_reevaluaciones

# Obtener historial
historial = get_historial_reevaluaciones(eval_id)
```

---

**Documento generado el**: 31 de Enero de 2026  
**Sistema**: TITA - Tool for IT Assessment  
**Versión**: Matriz de Referencia  
**Metodología**: MAGERIT v3 + ISO 27002:2022

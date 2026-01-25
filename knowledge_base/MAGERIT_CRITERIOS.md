# TITA - Sistema de Evaluación de Riesgos MAGERIT v3

## Descripción del Proyecto
TITA (Transformación Integral de TI y Activos) es un sistema de evaluación de riesgos para activos tecnológicos universitarios, basado en la metodología MAGERIT v3 (Metodología de Análisis y Gestión de Riesgos de los Sistemas de Información) y controles de seguridad ISO 27002:2022.

## Metodología MAGERIT v3

### Fundamentos
MAGERIT es la metodología oficial del Gobierno de España para el análisis y gestión de riesgos de los sistemas de información. Versión 3 publicada en 2012.

### Fórmula de Cálculo de Riesgo
```
RIESGO INHERENTE = PROBABILIDAD × IMPACTO
RIESGO RESIDUAL = RIESGO INHERENTE × (1 - COBERTURA × EFECTIVIDAD × 0.8)
```

### Escalas de Valoración

#### Probabilidad (1-5)
| Valor | Nivel | Descripción |
|-------|-------|-------------|
| 1 | Muy Baja | Menos de 1 vez cada 5 años |
| 2 | Baja | 1 vez cada 2-5 años |
| 3 | Media | 1 vez al año |
| 4 | Alta | Varias veces al año |
| 5 | Muy Alta | Frecuente (mensual o más) |

#### Impacto (1-5)
| Valor | Nivel | Descripción |
|-------|-------|-------------|
| 1 | Muy Bajo | Sin afectación significativa |
| 2 | Bajo | Afectación menor, recuperable fácilmente |
| 3 | Medio | Afectación moderada, requiere recursos |
| 4 | Alto | Afectación grave, impacto significativo |
| 5 | Muy Alto | Afectación crítica, pérdidas mayores |

#### Niveles de Riesgo (1-25)
| Rango | Nivel | Color | Acción |
|-------|-------|-------|--------|
| 1-4 | Muy Bajo | Verde | Aceptar |
| 5-8 | Bajo | Amarillo | Monitorear |
| 9-12 | Medio | Naranja | Mitigar |
| 13-20 | Alto | Rojo | Tratar urgente |
| 21-25 | Crítico | Rojo oscuro | Acción inmediata |

## Criterios D/I/C

### Disponibilidad (D)
Garantía de que los usuarios autorizados tengan acceso a la información y recursos cuando lo necesiten.

| Nivel | Criterio |
|-------|----------|
| 1 | Puede estar no disponible por días sin impacto significativo |
| 2 | Puede tolerar indisponibilidad por horas sin impacto importante |
| 3 | Requiere disponibilidad en horario laboral |
| 4 | Requiere alta disponibilidad (99%+) |
| 5 | Requiere disponibilidad continua 24x7 (99.9%+) |

### Integridad (I)
Garantía de la exactitud y completitud de la información y los métodos de procesamiento.

| Nivel | Criterio |
|-------|----------|
| 1 | Alteraciones menores sin consecuencias |
| 2 | Alteraciones detectables con bajo impacto |
| 3 | Alteraciones causan problemas moderados |
| 4 | Alteraciones causan problemas graves |
| 5 | Alteraciones tienen consecuencias críticas |

### Confidencialidad (C)
Garantía de que la información es accesible solo para quienes están autorizados.

| Nivel | Criterio |
|-------|----------|
| 1 | Información pública |
| 2 | Información de uso interno |
| 3 | Información confidencial |
| 4 | Información altamente confidencial |
| 5 | Información secreta/crítica |

## Categorías de Amenazas MAGERIT

### [D] Desastres Naturales
Fenómenos naturales que pueden afectar la infraestructura tecnológica:
- D.1 Fuego (incendio)
- D.2 Daños por agua (inundación)
- D.* Otros desastres naturales (terremotos, tormentas, etc.)

### [I] De Origen Industrial
Fallos en servicios, infraestructura o equipamiento:
- I.1 Fuego de origen industrial
- I.2 Daños por agua de origen industrial
- I.3 Contaminación mecánica
- I.4 Contaminación electromagnética
- I.5 Avería de origen físico o lógico
- I.6 Corte del suministro eléctrico
- I.7 Condiciones inadecuadas de temperatura o humedad
- I.8 Fallo de servicios de comunicaciones
- I.9 Interrupción de otros servicios y suministros esenciales
- I.10 Degradación de los soportes de almacenamiento
- I.11 Emanaciones electromagnéticas

### [E] Errores y Fallos No Intencionados
Errores humanos, de configuración, software o hardware:
- E.1 Errores de los usuarios
- E.2 Errores del administrador
- E.3 Errores de monitorización
- E.4 Errores de configuración
- E.7 Deficiencias en la organización
- E.8 Difusión de software dañino
- E.9 Errores de [re-]encaminamiento
- E.10 Errores de secuencia
- E.14 Escapes de información
- E.15 Alteración accidental de la información
- E.18 Destrucción de información
- E.19 Fugas de información
- E.20 Vulnerabilidades de los programas (software)
- E.21 Errores de mantenimiento/actualización de programas
- E.23 Errores de mantenimiento/actualización de equipos
- E.24 Caída del sistema por agotamiento de recursos
- E.25 Pérdida de equipos
- E.28 Indisponibilidad del personal

### [A] Ataques Intencionados
Acciones maliciosas deliberadas:
- A.3 Manipulación de los registros de actividad (log)
- A.4 Manipulación de la configuración
- A.5 Suplantación de la identidad del usuario
- A.6 Abuso de privilegios de acceso
- A.7 Uso no previsto
- A.8 Difusión de software dañino
- A.9 [Re-]encaminamiento de mensajes
- A.10 Alteración de secuencia
- A.11 Acceso no autorizado
- A.12 Análisis de tráfico
- A.13 Repudio
- A.14 Interceptación de información (escucha)
- A.15 Modificación deliberada de la información
- A.18 Destrucción de información
- A.19 Divulgación de información
- A.22 Manipulación de programas
- A.23 Manipulación de los equipos
- A.24 Denegación de servicio
- A.25 Robo
- A.26 Ataque destructivo
- A.27 Ocupación enemiga
- A.28 Indisponibilidad del personal
- A.29 Extorsión
- A.30 Ingeniería social

## Controles ISO 27002:2022

### Categoría 5: Controles Organizacionales (37 controles)
- 5.1 a 5.37: Políticas, roles, segregación, gestión de activos, clasificación, etc.

### Categoría 6: Controles de Personas (8 controles)
- 6.1 a 6.8: Verificación, términos, concienciación, capacitación, sanciones, trabajo remoto, etc.

### Categoría 7: Controles Físicos (14 controles)
- 7.1 a 7.14: Perímetro, entrada, oficinas, equipos, servicios, cableado, mantenimiento, etc.

### Categoría 8: Controles Tecnológicos (34 controles)
- 8.1 a 8.34: Dispositivos, acceso, autenticación, capacidad, protección malware, backups, logs, redes, criptografía, desarrollo seguro, etc.

## Integración con IA Local

### Ollama
El sistema utiliza Ollama como motor de IA local para:
- Análisis inteligente de activos
- Identificación automática de amenazas MAGERIT
- Recomendación de controles ISO 27002
- Generación de justificaciones técnicas

### Requisitos
- Ollama instalado localmente (http://localhost:11434)
- Modelo LLM compatible (llama2, llama3, mistral, etc.)
- Sin conexión a Internet requerida

### Validación de IA
El sistema incluye validación para garantizar:
- IA funciona 100% local
- No hay datos hardcodeados o aleatorios
- Respuestas dependen del input real
- Códigos de amenazas/controles son válidos

## Flujo de Evaluación

1. **Registro de Activo**: Nombre, tipo, criticidad, características
2. **Cuestionario de Seguridad**: Preguntas sobre controles existentes
3. **Análisis IA**: Identificación de amenazas y controles
4. **Cálculo MAGERIT**: Riesgo inherente y residual
5. **Dashboard**: Visualización de resultados
6. **Informes**: Exportación de evaluaciones

## Arquitectura Técnica

```
┌─────────────────────────────────────────┐
│           Streamlit (UI)                │
├─────────────────────────────────────────┤
│   Services Layer                        │
│   ├── magerit_engine.py                 │
│   ├── ollama_magerit_service.py         │
│   ├── ia_validation_service.py          │
│   ├── knowledge_base_service.py         │
│   └── database_service.py               │
├─────────────────────────────────────────┤
│   SQLite Database                       │
│   ├── CATALOGO_AMENAZAS_MAGERIT         │
│   ├── CATALOGO_CONTROLES_ISO27002       │
│   ├── ACTIVOS                           │
│   ├── EVALUACIONES                      │
│   └── IA_EXECUTION_EVIDENCE             │
├─────────────────────────────────────────┤
│   Ollama (IA Local)                     │
│   └── localhost:11434                   │
└─────────────────────────────────────────┘
```

## Referencias

- MAGERIT v3 - Ministerio de Hacienda y Administraciones Públicas de España
- ISO/IEC 27002:2022 - Information security controls
- Centro Criptológico Nacional (CCN) - Guías de Seguridad

# CONTEXTO ENRIQUECIDO PARA IA 🧠📚

## Resumen Ejecutivo

La IA del sistema TITA ha sido **completamente alimentada** con conocimiento especializado en seguridad de la información, abarcando:

✅ **52 Amenazas MAGERIT v3** (con descripciones completas)  
✅ **93 Controles ISO 27002:2022** (con descripciones completas)  
✅ **64 Vulnerabilidades** específicas por tipo de activo  
✅ **7 Aplicaciones Críticas UDLA** con contexto de negocio  
✅ **Mapeos Amenazas → Controles** para recomendaciones precisas  
✅ **Degradaciones calibradas** por amenaza y dimensión  
✅ **Ejemplos de análisis** correcto en formato JSON  

**Total: ~23,500 caracteres (~5,900 tokens) de conocimiento especializado**

---

## Arquitectura del Sistema

### 1. Fuentes de Datos

```
📁 knowledge_base/
├── amenazas_magerit_completo.json     (52 amenazas)
├── controles_iso27002_completo.json   (93 controles)
└── MAGERIT_CRITERIOS.md               (metodología)

📁 services/
├── ia_context_enriquecido.py          (contexto completo)
├── ollama_magerit_service.py          (integración IA)
└── ollama_monitor.py                   (disponibilidad 100%)
```

### 2. Flujo de Alimentación

```
Base de Datos (tita_database.db)
    ↓
cargar_catalogos_ia.py
    ↓
JSON en knowledge_base/
    ↓
ia_context_enriquecido.py (carga + construye contexto)
    ↓
ollama_magerit_service.py (construir_prompt_magerit)
    ↓
Ollama (llama3.2:1b) con contexto completo
    ↓
Evaluación JSON estructurada
```

---

## Catálogos Disponibles para la IA

### 📊 Amenazas MAGERIT v3 (52 amenazas)

#### Ataques Intencionados (21 amenazas)
- **A.5**: Suplantación de identidad
- **A.6**: Abuso de privilegios
- **A.7**: Uso no autorizado de recursos
- **A.8**: Software malicioso (malware)
- **A.11**: Acceso no autorizado
- **A.15**: Alteración de información
- **A.18**: Destrucción de información
- **A.19**: Revelación de información
- **A.22**: Manipulación de equipo
- **A.23**: Interceptación de información
- **A.24**: Denegación de servicio (DoS/DDoS)
- **A.25**: Robo de equipos o documentos
- **A.26**: Ataque destructivo
- **A.27**: Ocupación enemiga
- **A.28**: Indisponibilidad del personal
- **A.29**: Extorsión
- **A.30**: Ingeniería social

#### Desastres Naturales (3 amenazas)
- **N.1**: Fuego
- **N.2**: Daños por agua
- **N.***: Desastres naturales (terremoto, inundación)

#### Errores no Intencionados (17 amenazas)
- **E.1**: Errores de usuario
- **E.2**: Errores del administrador
- **E.3**: Errores de monitoreo
- **E.4**: Errores de configuración
- **E.7**: Deficiencias en la organización
- **E.8**: Difusión de software dañino
- **E.9**: Errores de mantenimiento/actualización
- **E.14**: Escapes de información
- **E.15**: Alteración accidental de información
- **E.18**: Destrucción de información
- **E.19**: Fuga de información
- **E.20**: Vulnerabilidades de programas
- **E.21**: Errores de mantenimiento
- **E.23**: Errores de uso
- **E.24**: Daño por agua (accidental)
- **E.25**: Desastres naturales

#### Origen Industrial (11 amenazas)
- **I.1**: Fallo de servicios de comunicaciones
- **I.2**: Corte de suministro eléctrico
- **I.3**: Corte de agua
- **I.4**: Condiciones inadecuadas de temperatura/humedad
- **I.5**: Avería de origen físico o lógico
- **I.6**: Corte de suministros diversos
- **I.7**: Degradación de soportes de almacenamiento
- **I.8**: Fallo de equipos
- **I.9**: Interrupción de servicios
- **I.10**: Degradación de sistemas de información

### 🛡️ Controles ISO 27002:2022 (93 controles)

#### 5.x - Organizacionales (37 controles)
- **5.1**: Políticas de seguridad de la información
- **5.2**: Roles y responsabilidades de seguridad
- **5.3**: Segregación de funciones
- **5.7**: Inteligencia de amenazas
- **5.9**: Inventario de información y activos
- **5.10**: Uso aceptable de información y activos
- **5.12**: Clasificación de información
- **5.13**: Etiquetado de información
- **5.14**: Transferencia de información
- **5.15**: Control de acceso
- **5.16**: Gestión de identidades
- **5.17**: Información de autenticación
- **5.18**: Derechos de acceso
- **5.23**: Seguridad de la información en el uso de servicios en la nube
- **5.29**: Seguridad de la información durante disrupción
- **5.30**: Preparación de TIC para continuidad del negocio

#### 6.x - Personas (8 controles)
- **6.1**: Verificación de antecedentes
- **6.2**: Términos y condiciones de empleo
- **6.3**: Concientización, educación y capacitación en seguridad
- **6.4**: Proceso disciplinario
- **6.5**: Responsabilidades después de la terminación
- **6.6**: Acuerdos de confidencialidad y no divulgación
- **6.7**: Trabajo remoto
- **6.8**: Reporte de eventos de seguridad

#### 7.x - Físicos (14 controles)
- **7.1**: Perímetros de seguridad física
- **7.2**: Entrada física
- **7.3**: Seguridad de oficinas, recintos e instalaciones
- **7.4**: Monitoreo de seguridad física
- **7.5**: Protección contra amenazas físicas y ambientales
- **7.7**: Escritorio limpio y pantalla limpia
- **7.8**: Ubicación y protección de equipos
- **7.9**: Seguridad de activos fuera de las instalaciones
- **7.10**: Medios de almacenamiento
- **7.11**: Servicios de apoyo
- **7.12**: Seguridad del cableado
- **7.13**: Mantenimiento de equipos
- **7.14**: Disposición segura o reutilización de equipos

#### 8.x - Tecnológicos (34 controles)
- **8.1**: Dispositivos de punto final de usuario
- **8.2**: Derechos de acceso privilegiados
- **8.3**: Restricción de acceso a la información
- **8.4**: Acceso al código fuente
- **8.5**: Autenticación segura
- **8.7**: Protección contra malware
- **8.8**: Gestión de vulnerabilidades técnicas
- **8.9**: Gestión de configuración
- **8.10**: Borrado de información
- **8.11**: Enmascaramiento de datos
- **8.12**: Prevención de fuga de datos
- **8.13**: Respaldo de información
- **8.14**: Redundancia de instalaciones de procesamiento de información
- **8.15**: Registro (logging)
- **8.16**: Actividades de monitoreo
- **8.19**: Instalación de software en sistemas operativos
- **8.20**: Seguridad de redes
- **8.21**: Seguridad de servicios de red
- **8.22**: Segregación de redes
- **8.23**: Filtrado web
- **8.24**: Uso de criptografía
- **8.25**: Ciclo de vida de desarrollo seguro
- **8.26**: Requisitos de seguridad de aplicaciones
- **8.28**: Codificación segura
- **8.29**: Pruebas de seguridad en desarrollo y aceptación
- **8.30**: Desarrollo externalizado
- **8.31**: Separación de entornos de desarrollo, prueba y producción

### 🔍 Vulnerabilidades por Tipo (64 vulnerabilidades)

- **SW (Software)**: 10 vulnerabilidades
- **HW (Hardware)**: 7 vulnerabilidades
- **COM (Comunicaciones)**: 8 vulnerabilidades
- **D (Datos)**: 8 vulnerabilidades
- **S (Servicios)**: 8 vulnerabilidades
- **PS (Personal)**: 8 vulnerabilidades
- **L (Locales)**: 7 vulnerabilidades
- **AUX (Auxiliares)**: 8 vulnerabilidades

### 🏛️ Aplicaciones Críticas UDLA (7 aplicaciones)

1. **Banner** - SIS (CRÍTICO)
2. **D2L - Desire2Learn** - Aula Virtual (CRÍTICO)
3. **Portal de Pagos** - Financiero (CRÍTICO)
4. **Carpeta Online** - Documentos (ALTO)
5. **Uni+** - App Móvil (ALTO)
6. **Página Web** - Portal Institucional (MEDIO)
7. **BX** - Biblioteca Digital (MEDIO)

---

## Mapeos Inteligentes

### Amenazas → Controles ISO 27002

La IA conoce las relaciones entre amenazas y controles:

| Amenaza | Dimensión | Controles Recomendados |
|---------|-----------|------------------------|
| A.24 (DDoS) | D | 8.20, 8.22, 8.14 |
| A.8 (Malware) | I | 8.7, 8.8, 8.23 |
| A.11 (Acceso no autorizado) | C | 5.15, 5.16, 8.5 |
| A.5 (Suplantación) | C | 5.15, 5.16, 8.5 |
| E.1 (Errores usuario) | D/I | 6.3, 8.9, 8.16 |
| E.2 (Errores admin) | I | 5.18, 8.2, 6.3 |
| N.1 (Fuego) | D | 7.5, 8.14, 5.29 |

### Degradaciones Típicas (% de pérdida)

| Amenaza | D | I | C |
|---------|---|---|---|
| A.24 (DDoS) | 100% | 10% | 10% |
| A.8 (Malware) | 50% | 80% | 60% |
| A.11 (Acceso no autorizado) | 10% | 100% | 100% |
| N.1 (Fuego) | 100% | 100% | 100% |
| E.1 (Errores usuario) | 30% | 60% | 40% |

---

## Formato de Respuesta JSON

La IA SIEMPRE responde con este formato estructurado:

```json
{
  "probabilidad": 3,
  "amenazas": [
    {
      "codigo": "A.24",
      "dimension": "D",
      "justificacion": "El activo no cuenta con protección DDoS...",
      "controles_iso_recomendados": [
        {
          "control": "8.20",
          "prioridad": "Alta",
          "motivo": "Implementar seguridad de redes con protección DDoS"
        }
      ]
    }
  ],
  "observaciones": "Resumen del perfil de riesgo..."
}
```

---

## Reglas Críticas de la IA

1. ✅ **SOLO usa códigos del catálogo** (no inventa amenazas)
2. ✅ **SOLO recomienda controles ISO 27002 del catálogo**
3. ✅ **Dimensiones válidas**: D, I, C únicamente
4. ✅ **Prioridades válidas**: "Alta", "Media", "Baja"
5. ✅ **Probabilidad**: 1-5 (entero)
6. ✅ **Justificaciones específicas** al activo analizado
7. ✅ **Motivos de controles** explican CÓMO mitigan la amenaza

---

## Ejemplos de Análisis Correcto

### Ejemplo 1: Servidor Web sin Protección

```json
{
  "probabilidad": 4,
  "amenazas": [
    {
      "codigo": "A.24",
      "dimension": "D",
      "justificacion": "Servidor expuesto a Internet sin protección DDoS ni WAF",
      "controles_iso_recomendados": [
        {"control": "8.20", "prioridad": "Alta", "motivo": "Implementar WAF"},
        {"control": "8.22", "prioridad": "Alta", "motivo": "Segmentar red DMZ"}
      ]
    },
    {
      "codigo": "A.8",
      "dimension": "I",
      "justificacion": "Sin antimalware ni análisis de vulnerabilidades regular",
      "controles_iso_recomendados": [
        {"control": "8.7", "prioridad": "Alta", "motivo": "Instalar antimalware"},
        {"control": "8.8", "prioridad": "Media", "motivo": "Análisis mensual"}
      ]
    }
  ],
  "observaciones": "Servidor web crítico con exposición alta. Requiere hardening urgente."
}
```

### Ejemplo 2: Base de Datos con Datos Sensibles

```json
{
  "probabilidad": 3,
  "amenazas": [
    {
      "codigo": "A.11",
      "dimension": "C",
      "justificacion": "Datos personales sin cifrado, controles débiles",
      "controles_iso_recomendados": [
        {"control": "8.24", "prioridad": "Alta", "motivo": "Cifrar con AES-256"},
        {"control": "5.15", "prioridad": "Alta", "motivo": "Implementar RBAC"}
      ]
    }
  ],
  "observaciones": "Base de datos requiere protección técnica y administrativa urgente."
}
```

---

## Estadísticas del Contexto

| Métrica | Valor |
|---------|-------|
| **Caracteres totales** | 23,493 |
| **Palabras** | 3,160 |
| **Líneas** | 857 |
| **Tokens aproximados** | ~5,900 |
| **Secciones principales** | 48 |
| **Amenazas MAGERIT** | 52 códigos |
| **Controles ISO 27002** | 93 códigos |
| **Vulnerabilidades** | 64 tipos |
| **Aplicaciones UDLA** | 7 críticas |

---

## Uso en el Sistema

### Integración con Ollama

```python
from services.ia_context_enriquecido import get_contexto_completo_ia

# Obtener contexto completo
contexto = get_contexto_completo_ia()

# Construir prompt con información del activo
prompt = f"""{contexto}

---

## ACTIVO A ANALIZAR

Nombre: Banner (SIS)
Tipo: Aplicación Web
Criticidad: 4 (Crítico)
...

## TU TAREA
Analiza el activo usando todo el conocimiento...
"""

# Enviar a Ollama
respuesta = llamar_ollama(prompt, modelo="llama3.2:1b")
```

### Disponibilidad 100%

El sistema garantiza que la IA siempre esté disponible:

- ✅ **5 reintentos** con backoff exponencial (1s → 16s)
- ✅ **Timeout progresivo** (5s → 25s)
- ✅ **Cache de 24 horas** para resiliencia
- ✅ **Auto-inicio** de Ollama si está caído
- ✅ **Monitoreo activo** cada 30 segundos

Ver: `services/ollama_monitor.py`

---

## Próximas Mejoras

### 🔮 Futuras Funcionalidades

1. **Aprendizaje de Evaluaciones**
   - Guardar evaluaciones validadas por expertos
   - La IA aprende de casos reales aprobados

2. **Contexto Dinámico**
   - Ajustar contexto según tipo de activo
   - Reducir tokens innecesarios

3. **Integración con LangChain**
   - RAG (Retrieval-Augmented Generation)
   - Embeddings para búsqueda semántica

4. **Fine-tuning del Modelo**
   - Entrenar modelo específico para MAGERIT
   - Usar dataset de evaluaciones reales UDLA

---

## Validación y Pruebas

### Script de Verificación

```bash
python test_ia_enriquecida.py
```

**Verifica:**
- ✅ 52 amenazas cargadas correctamente
- ✅ 93 controles cargados correctamente
- ✅ Contexto completo generado (23KB)
- ✅ Todas las secciones presentes
- ✅ Ejemplos de análisis incluidos

---

## Referencias

- **MAGERIT v3**: [Ministerio de Asuntos Económicos y Transformación Digital (España)](https://administracionelectronica.gob.es/pae_Home/pae_Documentacion/pae_Metodolog/pae_Magerit.html)
- **ISO/IEC 27002:2022**: Information security controls
- **Proyecto UDLA**: Sistema TITA - Evaluación de Riesgos de Seguridad

---

**Creado:** 2025-01-XX  
**Última actualización:** 2025-01-XX  
**Autor:** Sistema TITA - UDLA  
**Versión:** 2.0 - Contexto Enriquecido

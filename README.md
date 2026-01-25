# 🛡️ Proyecto TITA - Sistema de Evaluación de Riesgos

**Sistema de Gestión de Auditoría de Activos Críticos**  
Metodología: MAGERIT + ISO/IEC 27001-27002  
Tecnología: Streamlit + Ollama (IA Local)

---

## 📋 Descripción

Proyecto TITA es un sistema web para realizar evaluaciones de riesgos de activos críticos TI siguiendo la metodología **MAGERIT** (Metodología de Análisis y Gestión de Riesgos de los Sistemas de Información) integrada con controles **ISO/IEC 27002:2022**.

### Características Principales

✅ **Gestión de Evaluaciones:** Crear y gestionar evaluaciones periódicas  
✅ **Inventario de Activos:** Registro de activos físicos y virtuales  
✅ **Cuestionarios Inteligentes:** Generación asistida por IA (Ollama)  
✅ **Versionado:** Sistema de versionado de cuestionarios por timestamp  
✅ **Cálculo de Impacto:** Análisis dimensional DIC (Disponibilidad, Integridad, Confidencialidad)  
🔄 **Análisis de Riesgos IA:** (En desarrollo)  
🔄 **Dashboards Visuales:** (En desarrollo)  
🔄 **Autenticación:** (Planeado)

---

## 🚀 Instalación Rápida

### Prerrequisitos

- Python 3.12+
- Ollama instalado y corriendo ([ollama.ai](https://ollama.ai))
- Git

### Pasos

```bash
# 1. Clonar repositorio
git clone <url-repositorio>
cd capston_riesgos

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar Ollama
ollama pull llama3

# 6. Crear estructura Excel inicial
python setup_excel_v2.py

# 7. Sembrar catálogos MAGERIT/ISO
python seed_catalogos.py

# 8. Ejecutar aplicación
streamlit run app.py
```

La aplicación estará disponible en: **http://localhost:8501**

---

## 📁 Estructura del Proyecto

```
capston_riesgos/
├── app.py                          # Aplicación principal Streamlit
├── setup_excel_v2.py               # Setup de estructura Excel
├── seed_catalogos.py               # Seeding de catálogos
├── generate_questions.py           # CLI generación preguntas IA
├── add_bia_columns.py              # Migración esquema BIA
├── matriz_riesgos_v2.xlsx          # Base de datos Excel
├── CONTEXTO_PROYECTO_TITA.md       # Documentación arquitectura
├── ANALISIS_ARQUITECTURA_GAP.md    # Análisis técnico
├── ROADMAP_DESARROLLO.md           # Plan de desarrollo
├── requirements.txt                # Dependencias Python
└── .gitignore                      # Archivos ignorados Git
```

---

## 🎯 Uso del Sistema

### 1️⃣ Tab 1: Inventario

Visualiza los activos críticos registrados.

**Requisito:** Crear activos manualmente en Excel (hoja `INVENTARIO_ACTIVOS`)

### 2️⃣ Tab 2: Generar Cuestionario (IA)

1. Seleccionar activo del inventario
2. Definir ID y nombre de evaluación
3. Elegir modelo Ollama (llama3, phi3, mistral)
4. Click "🚀 Ejecutar"

**Resultado:** Cuestionario versionado con preguntas base + IA

### 3️⃣ Tab 3: Responder Cuestionario

1. Seleccionar Evaluación/Activo/Versión
2. Responder preguntas (0/1 o escala 1-5)
3. Guardar respuestas

**Opcional:** Editar preguntas antes de responder

### 4️⃣ Tab 4: Cálculo de Impacto DIC

1. Seleccionar Evaluación/Activo/Versión respondida
2. Ver cálculo de impactos por dimensión:
   - **D:** Disponibilidad
   - **I:** Integridad
   - **C:** Confidencialidad
3. Guardar impacto calculado

---

## 🧠 Integración con IA (Ollama)

### Configuración

El sistema usa **Ollama** corriendo localmente en: `http://localhost:11434`

### Modelos Soportados

- `llama3` (recomendado)
- `phi3`
- `mistral`

### Funcionalidad Actual

✅ **Generación de Preguntas:** IA crea preguntas técnicas contextualizadas  
🔄 **Análisis de Riesgos:** (Próximamente - ver roadmap)

### Ejemplo de Prompt

```python
Genera EXACTAMENTE 15 preguntas TÉCNICAS para continuidad:
- arquitectura, HA, redundancia, backups, replicación
- Formato: JSON con Pregunta, Tipo_Respuesta, Peso, Dimension
```

---

## 📊 Estructura Excel (Base de Datos)

El sistema usa Excel como persistencia con 15+ hojas:

### Hojas Principales

| Hoja | Descripción |
|------|-------------|
| `EVALUACIONES` | Registro maestro de evaluaciones |
| `INVENTARIO_ACTIVOS` | Activos críticos (físicos/virtuales) |
| `BANCO_PREGUNTAS` | Preguntas base reutilizables |
| `CUESTIONARIOS` | Cuestionarios generados (versionados) |
| `RESPUESTAS` | Respuestas de usuarios |
| `IMPACTO_ACTIVOS` | Cálculo impacto DIC |
| `ANALISIS_RIESGO` | Resultados análisis IA (futuro) |
| `CATALOGO_AMENAZAS_MAGERIT` | Catálogo oficial amenazas |
| `CATALOGO_ISO27002_2022` | Controles ISO 27002 |

---

## 🔧 Configuración

### Variables de Entorno

Editar en `app.py`:

```python
EXCEL_PATH = "matriz_riesgos_v2.xlsx"
OLLAMA_URL = "http://localhost:11434/api/generate"
```

### Personalizar Cuestionarios

Editar `n_base` y `n_ia` en Tab 2:

```python
n_base = 5   # Preguntas del banco
n_ia = 15    # Preguntas generadas por IA
```

---

## 🛠️ Desarrollo

### Ejecutar Tests

```bash
pytest tests/ -v
```

### Contribuir

1. Fork del proyecto
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "feat: Descripción"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Pull Request

---

## 📚 Documentación Adicional

- [CONTEXTO_PROYECTO_TITA.md](CONTEXTO_PROYECTO_TITA.md) - Arquitectura detallada
- [ANALISIS_ARQUITECTURA_GAP.md](ANALISIS_ARQUITECTURA_GAP.md) - Análisis técnico
- [ROADMAP_DESARROLLO.md](ROADMAP_DESARROLLO.md) - Plan de desarrollo futuro

---

## 🐛 Problemas Conocidos

- [ ] IA solo genera preguntas (análisis completo en desarrollo)
- [ ] Sin dashboards visuales (usar Plotly próximamente)
- [ ] Sin autenticación (implementar streamlit-authenticator)
- [ ] Excel no soporta edición simultánea

---

## 📝 Metodología MAGERIT

El sistema implementa:

### Dimensiones de Valoración (DIC)

- **D** - Disponibilidad
- **I** - Integridad
- **C** - Confidencialidad

### Escala de Impacto (1-5)

1. **Insignificante**
2. **Menor**
3. **Moderado**
4. **Mayor**
5. **Catastrófico**

### Criterios de Riesgo

- **Probabilidad:** 1-5
- **Impacto:** 1-5
- **Riesgo Inherente:** Probabilidad × Impacto (1-25)

---

## 🔐 Seguridad

⚠️ **IMPORTANTE:** Sistema en desarrollo sin autenticación.

### Para Producción (Roadmap):

- [ ] Implementar autenticación
- [ ] Control de acceso basado en roles (RBAC)
- [ ] Auditoría de acciones
- [ ] Cifrado de datos sensibles
- [ ] HTTPS obligatorio

---

## 📞 Soporte

Para dudas o problemas:

1. Revisar documentación en `/docs`
2. Consultar issues en repositorio
3. Contactar al equipo de desarrollo

---

## 📄 Licencia

[Definir licencia]

---

## 👥 Autores

- Equipo Proyecto TITA
- Universidad [Nombre]
- Capstone/Tesis 2026

---

## 🙏 Agradecimientos

- MAGERIT (Ministerio de Asuntos Económicos y Transformación Digital - España)
- ISO/IEC 27001-27002
- Ollama (Framework LLM local)
- Comunidad Streamlit

---

**Versión:** 1.0  
**Última actualización:** 22 Enero 2026

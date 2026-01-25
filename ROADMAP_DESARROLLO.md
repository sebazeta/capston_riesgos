# 🚀 ROADMAP DE DESARROLLO - PROYECTO TITA
## Plan Estratégico de Continuidad

**Fecha:** 22 de Enero de 2026  
**Estado Actual:** MVP funcional (24% completitud vs. documentación)  
**Objetivo:** Sistema completo de evaluación de riesgos MAGERIT/ISO 27002

---

## 🎯 DECISIÓN ESTRATÉGICA

Antes de continuar, define el objetivo:

### Opción A: Proyecto Académico (3-4 semanas)
- ✅ Demostrar concepto funcional
- ✅ Documentar metodología MAGERIT
- ✅ Presentar resultados en defensa
- 🎯 **Prioridad:** Completar funcionalidad core + documentación

### Opción B: Sistema Productivo (3-6 meses)
- ✅ Implementación completa con seguridad
- ✅ Arquitectura escalable
- ✅ Deployment profesional
- 🎯 **Prioridad:** Calidad, seguridad, mantenibilidad

---

## 📊 FASE 0: FUNDAMENTOS (1-2 semanas)
*Estabilizar lo existente antes de agregar funcionalidad*

### ✅ Tarea 0.1: Configuración de Desarrollo Profesional

**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 2 horas  
**Impacto:** ⭐⭐⭐⭐⭐

**Acciones:**
```bash
# 1. Crear requirements.txt formal
pip freeze > requirements.txt

# 2. Configurar .gitignore
echo "*.xlsx" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".venv/" >> .gitignore
echo "*.pyc" >> .gitignore

# 3. Inicializar tests
mkdir tests
touch tests/__init__.py
touch tests/test_excel_service.py
```

**Entregables:**
- [ ] `requirements.txt` actualizado
- [ ] `.gitignore` configurado
- [ ] Estructura de tests creada

---

### ✅ Tarea 0.2: Refactorización Básica

**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 4-6 horas  
**Impacto:** ⭐⭐⭐⭐

**Objetivo:** Separar `app.py` (668 líneas) en módulos manejables.

**Estructura propuesta:**
```
capston_riesgos/
├── app.py                  # Solo UI Streamlit (< 200 líneas)
├── services/
│   ├── __init__.py
│   ├── excel_service.py    # Funciones Excel
│   ├── ollama_service.py   # Cliente IA
│   └── evaluation_service.py # Lógica de negocio
├── utils/
│   ├── __init__.py
│   └── validators.py       # Validaciones
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuración
└── tests/
    └── ...
```

**Pasos:**
1. Crear carpetas `services/`, `utils/`, `config/`
2. Mover funciones Excel a `services/excel_service.py`
3. Mover funciones Ollama a `services/ollama_service.py`
4. Actualizar imports en `app.py`

**Entregables:**
- [ ] Código modularizado
- [ ] Tests básicos funcionando
- [ ] `app.py` < 200 líneas

---

### ✅ Tarea 0.3: Documentación Sincronizada

**Prioridad:** 🔴 ALTA  
**Esfuerzo:** 2-3 horas  
**Impacto:** ⭐⭐⭐⭐⭐

**Acciones:**
1. Actualizar `CONTEXTO_PROYECTO_TITA.md`:
   - Cambiar "PySide6" → "Streamlit"
   - Documentar arquitectura real
   - Actualizar diagramas de flujo

2. Crear `README.md` completo:
   ```markdown
   # Proyecto TITA - Evaluación de Riesgos MAGERIT
   
   ## Instalación
   ## Configuración
   ## Uso
   ## Arquitectura
   ## Limitaciones conocidas
   ```

**Entregables:**
- [ ] `CONTEXTO_PROYECTO_TITA.md` actualizado
- [ ] `README.md` completo
- [ ] Diagramas actualizados

---

## 🚀 FASE 1: COMPLETAR FUNCIONALIDAD CORE (2-3 semanas)

### ✅ Tarea 1.1: Extender IA para Análisis Completo de Riesgos

**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo:** 8-12 horas  
**Impacto:** ⭐⭐⭐⭐⭐

**Gap Actual:**
La IA solo genera preguntas. **Falta:**
- Análisis de riesgos (probabilidad × impacto)
- Identificación de amenazas
- Detección de vulnerabilidades
- Propuesta de salvaguardas ISO 27002

**Implementación:**

**Paso 1.1.1:** Crear Tab 5 "Análisis de Riesgos IA"

```python
# Agregar a app.py después de Tab 4

# -------- TAB 5: ANÁLISIS IA --------
with tab5:
    st.subheader("🤖 Análisis de Riesgos con IA")
    
    # Cargar activo con respuestas completas
    inv = read_sheet("INVENTARIO_ACTIVOS")
    resp = read_sheet("RESPUESTAS")
    impactos = read_sheet("IMPACTO_ACTIVOS")
    
    # Selector de activo
    activos_con_respuestas = resp["ID_Activo"].unique()
    activo_sel = st.selectbox("Activo a analizar", activos_con_respuestas)
    
    if st.button("🧠 Analizar con IA"):
        # Construir contexto completo
        contexto = build_risk_analysis_context(activo_sel)
        
        # Llamar Ollama con prompt especializado
        resultado = ollama_analyze_risk(contexto)
        
        # Mostrar resultados
        display_risk_results(resultado)
```

**Paso 1.1.2:** Crear función de análisis de riesgos

```python
def ollama_analyze_risk(contexto: dict) -> dict:
    """
    Analiza riesgos usando Ollama.
    
    Returns:
        {
            "probabilidad": 1-5,
            "impacto": 1-5,
            "riesgo_inherente": 1-25,
            "amenazas": [...],
            "vulnerabilidades": [...],
            "salvaguardas": [...],
            "justificacion": "texto"
        }
    """
    prompt = f"""
    Eres un experto en análisis de riesgos siguiendo MAGERIT.
    
    ACTIVO:
    {json.dumps(contexto['activo'], ensure_ascii=False)}
    
    RESPUESTAS CUESTIONARIO:
    {json.dumps(contexto['respuestas'], ensure_ascii=False)}
    
    IMPACTOS DIC:
    Disponibilidad: {contexto['impacto_d']}
    Integridad: {contexto['impacto_i']}
    Confidencialidad: {contexto['impacto_c']}
    
    TAREA:
    1. Analiza el activo y sus vulnerabilidades
    2. Identifica amenazas relevantes de MAGERIT
    3. Calcula probabilidad (1-5) e impacto (1-5)
    4. Propón salvaguardas ISO 27002
    
    DEVUELVE SOLO JSON:
    {{
      "probabilidad": 1-5,
      "impacto": 1-5,
      "amenazas": [
        {{"codigo": "A.01", "nombre": "...", "descripcion": "..."}}
      ],
      "vulnerabilidades": [
        {{"nombre": "...", "severidad": 1-5, "descripcion": "..."}}
      ],
      "salvaguardas": [
        {{"control_iso": "8.13", "nombre": "...", "prioridad": 1-5}}
      ],
      "justificacion": "explicación detallada"
    }}
    """
    
    raw = ollama_generate("llama3", prompt)
    return extract_and_validate_risk_json(raw)
```

**Entregables:**
- [ ] Tab 5 "Análisis IA" implementado
- [ ] Función `ollama_analyze_risk()` funcional
- [ ] Guardado de resultados en `ANALISIS_RIESGO`
- [ ] Visualización de amenazas/vulnerabilidades/salvaguardas

**Tiempo estimado:** 10 horas

---

### ✅ Tarea 1.2: Implementar Dashboards Interactivos

**Prioridad:** 🟡 ALTA  
**Esfuerzo:** 6-8 horas  
**Impacto:** ⭐⭐⭐⭐

**Gap Actual:**
No hay visualizaciones gráficas. Solo métricas numéricas.

**Implementación:**

**Paso 1.2.1:** Instalar dependencias de visualización

```bash
pip install plotly
pip install altair
```

**Paso 1.2.2:** Crear Tab 6 "Dashboards"

```python
import plotly.express as px
import plotly.graph_objects as go

with tab6:
    st.subheader("📊 Dashboards y Visualizaciones")
    
    # Dashboard 1: Mapa de Calor (Probabilidad × Impacto)
    st.markdown("### 🔥 Mapa de Calor de Riesgos")
    
    analisis = read_sheet("ANALISIS_RIESGO")
    if not analisis.empty:
        # Crear matriz de calor
        fig = go.Figure(data=go.Heatmap(
            x=analisis['Impacto'],
            y=analisis['Probabilidad'],
            z=analisis['Riesgo_Inherente'],
            colorscale='RdYlGn_r',
            text=analisis['ID_Activo'],
            hovertemplate='Activo: %{text}<br>Prob: %{y}<br>Imp: %{x}<br>Riesgo: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            xaxis_title="Impacto",
            yaxis_title="Probabilidad",
            title="Matriz de Riesgos (Probabilidad × Impacto)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Dashboard 2: Ranking de Activos Críticos
    st.markdown("### 🏆 Ranking de Activos por Riesgo")
    
    if not analisis.empty:
        top_activos = analisis.nlargest(10, 'Riesgo_Inherente')
        
        fig = px.bar(
            top_activos,
            x='Riesgo_Inherente',
            y='ID_Activo',
            orientation='h',
            color='Riesgo_Inherente',
            color_continuous_scale='Reds',
            title='Top 10 Activos Críticos'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Dashboard 3: Distribución por Dimensión DIC
    st.markdown("### 📈 Distribución de Impactos DIC")
    
    impactos = read_sheet("IMPACTO_ACTIVOS")
    if not impactos.empty:
        # Crear datos para gráfico
        dic_data = {
            'Dimensión': ['Disponibilidad', 'Integridad', 'Confidencialidad'],
            'Promedio': [
                impactos['Impacto_D'].mean(),
                impactos['Impacto_I'].mean(),
                impactos['Impacto_C'].mean()
            ]
        }
        
        fig = px.bar(
            dic_data,
            x='Dimensión',
            y='Promedio',
            color='Dimensión',
            title='Impacto Promedio por Dimensión DIC'
        )
        
        st.plotly_chart(fig, use_container_width=True)
```

**Entregables:**
- [ ] Tab 6 "Dashboards" implementado
- [ ] Mapa de calor funcional
- [ ] Ranking de activos
- [ ] Gráficos de distribución DIC

**Tiempo estimado:** 8 horas

---

### ✅ Tarea 1.3: Implementar Comparativas entre Evaluaciones

**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 4-6 horas  
**Impacto:** ⭐⭐⭐

**Implementación:**

```python
with tab7:
    st.subheader("🔄 Comparar Evaluaciones")
    
    evals = read_sheet("EVALUACIONES")
    if len(evals) < 2:
        st.warning("Necesitas al menos 2 evaluaciones para comparar.")
        st.stop()
    
    col1, col2 = st.columns(2)
    with col1:
        eval_a = st.selectbox("Evaluación A", evals["ID_Evaluacion"])
    with col2:
        eval_b = st.selectbox("Evaluación B", evals["ID_Evaluacion"])
    
    if st.button("Comparar"):
        # Cargar análisis de ambas evaluaciones
        analisis = read_sheet("ANALISIS_RIESGO")
        
        analisis_a = analisis[analisis["ID_Evaluacion"] == eval_a]
        analisis_b = analisis[analisis["ID_Evaluacion"] == eval_b]
        
        # Métricas comparativas
        col1, col2, col3 = st.columns(3)
        
        riesgo_a = analisis_a["Riesgo_Inherente"].mean()
        riesgo_b = analisis_b["Riesgo_Inherente"].mean()
        delta = riesgo_b - riesgo_a
        
        col1.metric("Eval A - Riesgo Promedio", f"{riesgo_a:.2f}")
        col2.metric("Eval B - Riesgo Promedio", f"{riesgo_b:.2f}")
        col3.metric("Diferencia", f"{delta:.2f}", delta_color="inverse")
        
        # Gráfico de evolución
        # ... implementar visualización temporal
```

**Entregables:**
- [ ] Tab 7 "Comparativas" funcional
- [ ] Métricas de diferencia
- [ ] Gráficos de evolución

**Tiempo estimado:** 5 horas

---

## 🔒 FASE 2: SEGURIDAD BÁSICA (1 semana)

### ✅ Tarea 2.1: Implementar Autenticación

**Prioridad:** 🔴 CRÍTICA (si va a producción)  
**Esfuerzo:** 3-4 horas  
**Impacto:** ⭐⭐⭐⭐⭐

**Implementación:**

```bash
pip install streamlit-authenticator
```

```python
# Agregar al inicio de app.py
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Cargar configuración de usuarios
with open('config/users.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Usuario/contraseña incorrectos')
    st.stop()
elif authentication_status == None:
    st.warning('Por favor ingresa usuario y contraseña')
    st.stop()

# Si llegamos aquí, usuario autenticado
st.sidebar.write(f"👤 Usuario: {name}")
authenticator.logout('Logout', 'sidebar')

# Resto de la aplicación...
```

**Archivo `config/users.yaml`:**
```yaml
credentials:
  usernames:
    admin:
      email: admin@tita.local
      name: Administrador
      password: $2b$12$...  # hash bcrypt
      rol: admin
    auditor1:
      email: auditor@tita.local
      name: Auditor
      password: $2b$12$...
      rol: auditor

cookie:
  name: tita_auth
  key: tita_secret_key_change_me
  expiry_days: 1
```

**Entregables:**
- [ ] Autenticación funcional
- [ ] Gestión de roles básica
- [ ] Logout implementado

**Tiempo estimado:** 4 horas

---

### ✅ Tarea 2.2: Control de Acceso Basado en Roles (RBAC)

**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 2-3 horas  
**Impacto:** ⭐⭐⭐

**Implementación:**

```python
# Crear decorador para verificar roles
def require_role(allowed_roles: list):
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_role = st.session_state.get('role', 'viewer')
            if user_role not in allowed_roles:
                st.error("No tienes permisos para esta acción")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Ejemplo de uso en tabs
with tab2:
    st.subheader("Generar cuestionario (IA+BIA)")
    
    # Solo admins y auditores pueden generar
    if st.session_state.get('role') not in ['admin', 'auditor']:
        st.warning("Solo usuarios con rol Admin/Auditor pueden generar cuestionarios")
        st.stop()
    
    # ... resto del código
```

**Roles sugeridos:**
- `admin`: Acceso total
- `auditor`: Crear/editar evaluaciones
- `analyst`: Ver/responder cuestionarios
- `viewer`: Solo lectura

**Entregables:**
- [ ] RBAC implementado
- [ ] Permisos por tab
- [ ] Mensajes de error claros

**Tiempo estimado:** 3 horas

---

## 🏗️ FASE 3: PROFESIONALIZACIÓN (2-4 semanas)
*Para sistema productivo*

### ✅ Tarea 3.1: Migrar a FastAPI Backend

**Prioridad:** 🟡 MEDIA (solo si objetivo es producción)  
**Esfuerzo:** 20-30 horas  
**Impacto:** ⭐⭐⭐⭐⭐

**Arquitectura propuesta:**

```
proyecto-tita/
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   ├── evaluations.py
│   │   │   │   ├── assets.py
│   │   │   │   ├── questionnaires.py
│   │   │   │   └── risk_analysis.py
│   │   │   └── deps.py
│   │   ├── services/
│   │   │   ├── excel_service.py
│   │   │   └── ollama_service.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/                   # React/Vue (opcional)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
│
└── streamlit-ui/              # Mantener Streamlit como alternativa
    └── app.py
```

**Entregables:**
- [ ] API REST FastAPI funcional
- [ ] Endpoints documentados (Swagger)
- [ ] Tests de API
- [ ] Autenticación JWT

**Tiempo estimado:** 25 horas

---

### ✅ Tarea 3.2: Migrar a PostgreSQL

**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** 10-15 horas  
**Impacto:** ⭐⭐⭐⭐

**Schema SQL propuesto:**

```sql
-- evaluaciones
CREATE TABLE evaluaciones (
    id_evaluacion VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'Activa',
    creada_desde VARCHAR(50),
    usuario_creador VARCHAR(100),
    responsable VARCHAR(100)
);

-- activos
CREATE TABLE activos (
    id_activo VARCHAR(50) PRIMARY KEY,
    id_evaluacion VARCHAR(50) REFERENCES evaluaciones(id_evaluacion),
    nombre_activo VARCHAR(200),
    tipo_activo VARCHAR(50),
    ubicacion VARCHAR(100),
    propietario VARCHAR(100),
    rto_objetivo_horas INT,
    rpo_objetivo_horas INT,
    bia_impacto INT CHECK (bia_impacto BETWEEN 1 AND 5),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_activo_base VARCHAR(50)
);

-- cuestionarios (versionados)
CREATE TABLE cuestionarios (
    id SERIAL PRIMARY KEY,
    id_evaluacion VARCHAR(50),
    id_activo VARCHAR(50),
    fecha_version TIMESTAMP,
    id_pregunta VARCHAR(50),
    pregunta TEXT,
    tipo_respuesta VARCHAR(10),
    peso INT CHECK (peso BETWEEN 1 AND 5),
    dimension CHAR(1) CHECK (dimension IN ('D','I','C')),
    fuente VARCHAR(10),
    FOREIGN KEY (id_activo) REFERENCES activos(id_activo)
);

-- ... resto de tablas
```

**Migración con SQLAlchemy ORM:**

```python
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Evaluacion(Base):
    __tablename__ = 'evaluaciones'
    
    id_evaluacion = Column(String(50), primary_key=True)
    nombre = Column(String(200), nullable=False)
    # ... resto de columnas
    
    activos = relationship("Activo", back_populates="evaluacion")

class Activo(Base):
    __tablename__ = 'activos'
    
    id_activo = Column(String(50), primary_key=True)
    id_evaluacion = Column(String(50), ForeignKey('evaluaciones.id_evaluacion'))
    # ... resto de columnas
    
    evaluacion = relationship("Evaluacion", back_populates="activos")
```

**Entregables:**
- [ ] Schema PostgreSQL creado
- [ ] Modelos SQLAlchemy
- [ ] Script de migración desde Excel
- [ ] Mantener exportación a Excel

**Tiempo estimado:** 12 horas

---

## 📝 FASE 4: TESTING Y CALIDAD (1 semana)

### ✅ Tarea 4.1: Tests Unitarios

**Prioridad:** 🟡 ALTA  
**Esfuerzo:** 6-8 horas  
**Impacto:** ⭐⭐⭐⭐

```python
# tests/test_excel_service.py
import pytest
from services.excel_service import read_sheet, append_rows

def test_read_sheet():
    df = read_sheet("INVENTARIO_ACTIVOS")
    assert not df.empty
    assert "ID_Activo" in df.columns

def test_append_rows():
    rows = [{"ID_Activo": "TEST-001", "Nombre": "Test"}]
    append_rows("INVENTARIO_ACTIVOS", rows)
    # Verificar que se guardó
    df = read_sheet("INVENTARIO_ACTIVOS")
    assert "TEST-001" in df["ID_Activo"].values
```

```bash
# Ejecutar tests
pytest tests/ -v
```

**Entregables:**
- [ ] Tests de servicios Excel
- [ ] Tests de servicios Ollama
- [ ] Tests de validaciones
- [ ] Coverage > 70%

**Tiempo estimado:** 8 horas

---

## 🎓 ALTERNATIVA ACADÉMICA RÁPIDA (2 semanas)

Si tu objetivo es **solo académico**, puedes seguir este camino simplificado:

### Semana 1:
- ✅ Tarea 0.3: Actualizar documentación
- ✅ Tarea 1.1: Extender IA (análisis de riesgos)
- ✅ Tarea 1.2: Dashboards básicos

### Semana 2:
- ✅ Tarea 2.1: Autenticación simple
- ✅ Tests básicos
- ✅ Preparar demo/presentación

**Resultado:** Sistema funcional demostrable para defensa de tesis.

---

## 📊 MÉTRICAS DE PROGRESO

Usa esta checklist para medir avance:

### Funcionalidad
- [ ] Generación de preguntas IA ✅ (ya existe)
- [ ] Respuesta de cuestionarios ✅ (ya existe)
- [ ] Cálculo impacto DIC ✅ (ya existe)
- [ ] Análisis de riesgos IA ❌ (Tarea 1.1)
- [ ] Dashboards visuales ❌ (Tarea 1.2)
- [ ] Comparativas ❌ (Tarea 1.3)

### Seguridad
- [ ] Autenticación ❌ (Tarea 2.1)
- [ ] RBAC ❌ (Tarea 2.2)
- [ ] Auditoría de acciones ❌

### Arquitectura
- [ ] Código modularizado ❌ (Tarea 0.2)
- [ ] Tests unitarios ❌ (Tarea 4.1)
- [ ] API REST ❌ (Tarea 3.1)
- [ ] Base de datos SQL ❌ (Tarea 3.2)

### Documentación
- [ ] README completo ❌ (Tarea 0.3)
- [ ] Documentación técnica ❌
- [ ] Manual de usuario ❌

---

## 🚦 PRÓXIMOS PASOS INMEDIATOS

### HOY (2 horas):
1. ✅ Lee este roadmap completo
2. ✅ Decide: ¿Académico o Productivo?
3. ✅ Crea branch de desarrollo: `git checkout -b feature/fase-1`
4. ✅ Completa Tarea 0.1 (requirements.txt + .gitignore)

### ESTA SEMANA (10 horas):
1. ✅ Tarea 0.2: Refactorizar código
2. ✅ Tarea 0.3: Actualizar documentación
3. ✅ Tarea 1.1: Iniciar análisis de riesgos IA

### MES 1:
1. ✅ Completar Fase 1 (funcionalidad core)
2. ✅ Implementar seguridad básica
3. ✅ Primeros tests

---

## 💡 TIPS DE DESARROLLO

### 1. Trabaja por Iteraciones
No intentes hacer todo a la vez. Completa una tarea, testea, commitea.

```bash
# Ejemplo de workflow Git
git checkout -b feature/analisis-ia
# ... hacer cambios
git add .
git commit -m "feat: Implementar análisis de riesgos con IA (Tarea 1.1)"
git push origin feature/analisis-ia
```

### 2. Testing Continuo
Después de cada cambio importante, verifica que todo siga funcionando:

```bash
# Ejecutar app localmente
streamlit run app.py

# Verificar tests
pytest tests/ -v
```

### 3. Documenta Decisiones
Crea un archivo `DECISIONES.md` para registrar:
- ¿Por qué elegiste X tecnología?
- ¿Por qué implementaste Y de esta forma?
- Limitaciones conocidas

### 4. Commits Descriptivos
Usa convención de commits:
- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `refactor:` Refactorización
- `docs:` Documentación
- `test:` Tests

---

## 📞 SOPORTE Y RECURSOS

### Documentación Técnica
- Streamlit: https://docs.streamlit.io/
- Ollama: https://ollama.ai/docs
- Plotly: https://plotly.com/python/
- FastAPI: https://fastapi.tiangolo.com/

### MAGERIT
- Guía oficial MAGERIT v3: https://administracionelectronica.gob.es/pae_Home/pae_Documentacion/pae_Metodolog/pae_Magerit.html
- ISO/IEC 27002:2022: Controles de seguridad

---

## 🎯 RESULTADO ESPERADO

### Proyecto Académico (Fase 0 + Fase 1):
- ✅ Sistema funcional de evaluación de riesgos
- ✅ Integración IA para análisis
- ✅ Dashboards visuales
- ✅ Documentación completa
- ✅ Demo preparada para defensa

### Sistema Productivo (Todas las fases):
- ✅ Aplicación web profesional
- ✅ API REST con autenticación
- ✅ Base de datos PostgreSQL
- ✅ Tests automatizados
- ✅ Deployment a servidor
- ✅ Seguridad implementada

---

**¡Éxito en el desarrollo! 🚀**

Para dudas o soporte, consulta el análisis arquitectónico completo en `ANALISIS_ARQUITECTURA_GAP.md`.

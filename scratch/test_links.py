import streamlit as st
import pandas as pd

st.set_page_config(page_title="Prueba de Enlaces en Tabla", layout="wide")

st.markdown("### Visualización de Opción 3: LinkColumns")
st.markdown("Así se vería la tabla usando columnas de enlaces. Cada enlace abriría la URL especificada (lo que forzaría una recarga de página).")

# Crear datos falsos
data = {
    "ID_Evaluacion": ["EVAL-001", "EVAL-002", "EVAL-003"],
    "Nombre": ["Evaluación Servidores", "Redes Externas", "Bases de Datos HQ"],
    "Estado": ["Completada", "En Progreso", "Pendiente"],
    # URLs falsas para los enlaces. En la vida real llevarían query params: /?eval=EVAL-001&nav=Activos
    "Activos": ["http://localhost:8501/?nav=Activos&eval=EVAL-001", "http://localhost:8501/?nav=Activos&eval=EVAL-002", "http://localhost:8501/?nav=Activos&eval=EVAL-003"],
    "Cuestionarios": ["http://localhost:8501/?nav=Cuestionarios&eval=EVAL-001", "http://localhost:8501/?nav=Cuestionarios&eval=EVAL-002", "http://localhost:8501/?nav=Cuestionarios&eval=EVAL-003"],
    "Madurez": ["http://localhost:8501/?nav=Madurez&eval=EVAL-001", "http://localhost:8501/?nav=Madurez&eval=EVAL-002", "http://localhost:8501/?nav=Madurez&eval=EVAL-003"]
}

df = pd.DataFrame(data)

st.dataframe(
    df,
    column_config={
        "ID_Evaluacion": "ID",
        "Nombre": "Nombre de Evaluación",
        "Estado": "Estado",
        "Activos": st.column_config.LinkColumn(
            "🖴 Activos", 
            help="Ir a los activos de la evaluación",
            display_text="Ver Activos"
        ),
        "Cuestionarios": st.column_config.LinkColumn(
            "📋 Cuestionarios", 
            help="Ir a los cuestionarios",
            display_text="Ver Cuestionarios"
        ),
        "Madurez": st.column_config.LinkColumn(
            "🏅 Madurez", 
            help="Ir a la vista de Madurez",
            display_text="Ver Madurez"
        )
    },
    hide_index=True,
    use_container_width=True
)

st.info("En Streamlit, las columnas de enlaces muestran el texto configurado y un ícono de enlace que aparece al pasar el cursor (o permanentemente). Sin embargo, al hacer clic, el navegador navegará a esa URL realizando una recarga completa.")

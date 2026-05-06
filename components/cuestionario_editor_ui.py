"""
EDITOR DE CUESTIONARIOS - Panel Admin
======================================
Permite al administrador ver, editar, agregar y eliminar
preguntas del banco de cuestionarios D/I/C/RTO/RPO/BIA.
Las modificaciones se guardan en la tabla CUESTIONARIOS_CUSTOM de la BD.
"""
import json
import copy
import streamlit as st
from services.database_service import get_connection
from services.cuestionario_dic_service import BANCO_PREGUNTAS_DIC

# ==================== FUNCIONES DE BD ====================

def _init_custom_table():
    """Crea la tabla de preguntas personalizadas si no existe."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS CUESTIONARIOS_CUSTOM (
                tipo_activo TEXT NOT NULL,
                dimension   TEXT NOT NULL,
                preguntas   TEXT NOT NULL,
                PRIMARY KEY (tipo_activo, dimension)
            )
        """)
        conn.commit()


def _load_custom(tipo_activo: str, dimension: str):
    """Carga preguntas personalizadas de la BD. Retorna None si no hay."""
    _init_custom_table()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT preguntas FROM CUESTIONARIOS_CUSTOM WHERE tipo_activo=? AND dimension=?",
            (tipo_activo, dimension)
        ).fetchone()
    if row:
        return json.loads(row[0])
    return None


def _save_custom(tipo_activo: str, dimension: str, preguntas: list):
    """Guarda preguntas personalizadas en la BD."""
    _init_custom_table()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO CUESTIONARIOS_CUSTOM (tipo_activo, dimension, preguntas)
               VALUES (?, ?, ?)
               ON CONFLICT(tipo_activo, dimension) DO UPDATE SET preguntas=excluded.preguntas""",
            (tipo_activo, dimension, json.dumps(preguntas, ensure_ascii=False))
        )
        conn.commit()


def _delete_custom(tipo_activo: str, dimension: str):
    """Elimina la personalización, volviendo al banco por defecto."""
    _init_custom_table()
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM CUESTIONARIOS_CUSTOM WHERE tipo_activo=? AND dimension=?",
            (tipo_activo, dimension)
        )
        conn.commit()


def get_preguntas_efectivas(tipo_activo: str, dimension: str) -> list:
    """Retorna las preguntas efectivas: custom si existen, sino las del banco."""
    custom = _load_custom(tipo_activo, dimension)
    if custom is not None:
        return custom
    banco = BANCO_PREGUNTAS_DIC.get(tipo_activo, {})
    return banco.get(dimension, [])


def hay_custom(tipo_activo: str, dimension: str) -> bool:
    """Verifica si hay preguntas personalizadas para ese tipo/dimensión."""
    return _load_custom(tipo_activo, dimension) is not None


# ==================== UI ====================

DIMENSIONES = ["D", "I", "C", "RTO", "RPO", "BIA"]
DIM_NOMBRES = {
    "D": "Disponibilidad",
    "I": "Integridad",
    "C": "Confidencialidad",
    "RTO": "Recovery Time Objective",
    "RPO": "Recovery Point Objective",
    "BIA": "Business Impact Analysis"
}


def render_editor_cuestionarios():
    """Renderiza el editor de cuestionarios para el administrador."""
    st.markdown("## 📝 Editor de Cuestionarios")
    st.caption("Administra las preguntas del banco de cuestionarios D/I/C/RTO/RPO/BIA por tipo de activo")

    _init_custom_table()

    tipos_activo = list(BANCO_PREGUNTAS_DIC.keys())

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        tipo_sel = st.selectbox("Tipo de activo", tipos_activo, key="editor_tipo_activo")
    with col_sel2:
        dim_sel = st.selectbox(
            "Dimensión",
            DIMENSIONES,
            format_func=lambda d: f"{d} — {DIM_NOMBRES[d]}",
            key="editor_dimension"
        )

    # Preguntas efectivas (custom o banco)
    preguntas = get_preguntas_efectivas(tipo_sel, dim_sel)
    es_custom = hay_custom(tipo_sel, dim_sel)

    if es_custom:
        st.info(f"✏️ Estas preguntas han sido **personalizadas**. Se usan en lugar del banco por defecto.")
    else:
        st.success(f"📋 Se muestran las preguntas del **banco por defecto** ({len(preguntas)} preguntas).")

    st.markdown("---")

    # ---- Mostrar / Editar preguntas ----
    if not preguntas:
        st.warning("No hay preguntas definidas para esta dimensión.")
    else:
        # Clonar para edición
        edited_preguntas = []
        something_changed = False

        for idx, preg in enumerate(preguntas):
            with st.expander(f"**{preg['id']}** — {preg['pregunta'][:80]}...", expanded=False):
                new_pregunta = st.text_area(
                    "Texto de la pregunta",
                    value=preg["pregunta"],
                    key=f"ed_preg_{tipo_sel}_{dim_sel}_{idx}",
                    height=80
                )

                st.markdown("**Opciones de respuesta:**")
                new_opciones = []
                for oidx, opt in enumerate(preg.get("opciones", [])):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        new_texto = st.text_input(
                            f"Opción {oidx+1}",
                            value=opt["texto"],
                            key=f"ed_opt_{tipo_sel}_{dim_sel}_{idx}_{oidx}"
                        )
                    with c2:
                        new_valor = st.number_input(
                            "Valor",
                            min_value=0, max_value=10,
                            value=int(opt["valor"]),
                            key=f"ed_val_{tipo_sel}_{dim_sel}_{idx}_{oidx}"
                        )
                    new_opciones.append({"texto": new_texto, "valor": new_valor})

                edited_q = {
                    "id": preg["id"],
                    "pregunta": new_pregunta,
                    "opciones": new_opciones
                }
                edited_preguntas.append(edited_q)

                if new_pregunta != preg["pregunta"] or new_opciones != preg.get("opciones", []):
                    something_changed = True

                # Botón eliminar pregunta
                if st.button(f"🗑️ Eliminar pregunta {preg['id']}", key=f"del_preg_{tipo_sel}_{dim_sel}_{idx}"):
                    preguntas_after = [p for i, p in enumerate(preguntas) if i != idx]
                    _save_custom(tipo_sel, dim_sel, preguntas_after)
                    st.success(f"Pregunta {preg['id']} eliminada.")
                    st.rerun()

        # Botón guardar cambios
        st.markdown("---")
        col_save, col_reset, col_add = st.columns(3)

        with col_save:
            if st.button("💾 Guardar cambios", key=f"save_{tipo_sel}_{dim_sel}", type="primary"):
                _save_custom(tipo_sel, dim_sel, edited_preguntas)
                st.success("✅ Preguntas guardadas correctamente.")
                st.rerun()

        with col_reset:
            if es_custom:
                if st.button("🔄 Restaurar banco por defecto", key=f"reset_{tipo_sel}_{dim_sel}"):
                    _delete_custom(tipo_sel, dim_sel)
                    st.success("🔄 Preguntas restauradas al banco por defecto.")
                    st.rerun()

        with col_add:
            if st.button("➕ Agregar pregunta", key=f"add_{tipo_sel}_{dim_sel}"):
                # Generar ID automático
                existing_ids = [p["id"] for p in preguntas]
                prefix = preguntas[0]["id"].rsplit("-", 1)[0] if preguntas else f"CUSTOM-{dim_sel}"
                new_num = len(preguntas) + 1
                new_id = f"{prefix}-{new_num}"
                while new_id in existing_ids:
                    new_num += 1
                    new_id = f"{prefix}-{new_num}"

                new_q = {
                    "id": new_id,
                    "pregunta": "Nueva pregunta — editar texto aquí",
                    "opciones": [
                        {"texto": "Opción de mayor impacto", "valor": 3},
                        {"texto": "Opción de impacto medio-alto", "valor": 2},
                        {"texto": "Opción de impacto medio-bajo", "valor": 1},
                        {"texto": "Opción de menor impacto", "valor": 0}
                    ]
                }
                current = list(preguntas) + [new_q]
                _save_custom(tipo_sel, dim_sel, current)
                st.success(f"✅ Pregunta {new_id} agregada.")
                st.rerun()

    # ---- Estadísticas ----
    st.markdown("---")
    st.markdown("### 📊 Resumen del banco de preguntas")
    stats_data = []
    for tipo in tipos_activo:
        for dim in DIMENSIONES:
            pregs = get_preguntas_efectivas(tipo, dim)
            is_c = hay_custom(tipo, dim)
            stats_data.append({
                "Tipo Activo": tipo,
                "Dimensión": dim,
                "Preguntas": len(pregs),
                "Estado": "✏️ Personalizado" if is_c else "📋 Por defecto"
            })

    import pandas as pd
    df_stats = pd.DataFrame(stats_data)
    st.dataframe(df_stats, use_container_width=True, hide_index=True)

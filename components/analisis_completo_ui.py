"""
COMPONENTE UI: ANÁLISIS COMPLETO CON UN SOLO BOTÓN
====================================================
Ejecuta todo el pipeline de análisis de riesgos en secuencia:
  Fase 1 → Evaluación IA de activos pendientes (amenazas + motor MAGERIT)
  Fase 2 → Generación de planes de tratamiento
  Fase 3 → Cálculo de nivel de madurez
  Fase 4 → Resumen ejecutivo de la evaluación
  Fase 5 → Priorización de controles por ROI de seguridad
"""

import streamlit as st
import pandas as pd
import datetime as dt
from typing import Optional


def render_analisis_completo(eval_id: str, eval_nombre: str, modelo_ia: Optional[str] = None):
    """
    Renderiza el botón de Análisis Completo y ejecuta todas las fases cuando se presiona.

    Parameters
    ----------
    eval_id : str
        ID de la evaluación activa.
    eval_nombre : str
        Nombre de la evaluación (para mostrar).
    modelo_ia : str | None
        Modelo de Ollama seleccionado (None = manual/no disponible).
    """
    from services import (
        get_activos_por_evaluacion,
        get_cuestionario,
        get_resultado_magerit,
        read_table,
        analizar_activo_con_ia,
        evaluar_activo_magerit,
        guardar_resultado_magerit,
        calcular_madurez_evaluacion,
        guardar_madurez,
        verificar_ollama_disponible,
    )
    from services.ia_advanced_service import (
        generar_planes_evaluacion,
        generar_resumen_ejecutivo,
        generar_priorizacion_controles,
    )
    from services.process_log_service import registrar_proceso_rapido, log_proceso

    st.markdown("---")
    st.markdown(
        """
        ### 🚀 Análisis Completo (Un Solo Clic)
        Ejecuta **todo el pipeline** de análisis de riesgos en secuencia:

        | Fase | Descripción |
        |------|-------------|
        | **1** | Evaluación IA de activos pendientes (amenazas + motor MAGERIT) |
        | **2** | Generación de planes de tratamiento para riesgos ALTO/CRÍTICO |
        | **3** | Cálculo del nivel de madurez de ciberseguridad |
        | **4** | Resumen ejecutivo de la evaluación |
        | **5** | Priorización de controles por ROI de seguridad |
        """
    )

    # ── Verificaciones previas ──────────────────────────────────────────────
    activos = get_activos_por_evaluacion(eval_id)
    if activos.empty:
        st.warning("⚠️ No hay activos en esta evaluación.")
        return

    respuestas_df = read_table("RESPUESTAS")

    # Clasificar activos
    activos_listos = []
    activos_evaluados = []
    activos_sin_cuestionario = []

    for _, activo in activos.iterrows():
        activo_id = activo["ID_Activo"]
        cuest = get_cuestionario(eval_id, activo_id)
        resp_activo = (
            respuestas_df[
                (respuestas_df["ID_Evaluacion"] == eval_id)
                & (respuestas_df["ID_Activo"] == activo_id)
            ]
            if not respuestas_df.empty
            else pd.DataFrame()
        )
        resultado_existente = get_resultado_magerit(eval_id, activo_id)

        if resultado_existente:
            activos_evaluados.append(activo_id)
        elif len(cuest) > 0 and len(resp_activo) >= len(cuest):
            activos_listos.append(activo_id)
        else:
            activos_sin_cuestionario.append(activo_id)

    # Resumen previo
    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Listos para IA", len(activos_listos))
    col2.metric("✅ Ya evaluados", len(activos_evaluados))
    col3.metric("⚪ Sin cuestionario", len(activos_sin_cuestionario))

    if not activos_listos and not activos_evaluados:
        st.info("ℹ️ No hay activos listos ni evaluados. Completa los cuestionarios primero.")
        return

    ollama_ok = modelo_ia is not None

    # ── Botón principal ─────────────────────────────────────────────────────
    btn_disabled = not ollama_ok and len(activos_listos) > 0
    btn_label = "⚡ Ejecutar Análisis Completo" if not btn_disabled else "⚡ Análisis (Ollama no disponible)"

    if st.button(btn_label, type="primary", use_container_width=True, disabled=btn_disabled, key="btn_analisis_completo"):
        _inicio_global = dt.datetime.now()

        # Container para toda la salida
        output_container = st.container()

        with output_container:
            # ═══════════════════════════════════════════════════════════════
            # FASE 1: Evaluación IA de activos pendientes
            # ═══════════════════════════════════════════════════════════════
            st.markdown("#### 📡 Fase 1/5 — Evaluación IA de Activos")

            if activos_listos:
                progress_fase1 = st.progress(0, text="Iniciando evaluación IA...")
                resultados_fase1 = []
                total_f1 = len(activos_listos)

                for i, activo_id in enumerate(activos_listos):
                    progress_fase1.progress(
                        i / total_f1,
                        text=f"Analizando {activo_id}... ({i + 1}/{total_f1})",
                    )
                    try:
                        exito_ia, resultado_ia, mensaje_ia = analizar_activo_con_ia(
                            eval_id, activo_id, modelo_ia
                        )
                        if exito_ia:
                            resultado_magerit = evaluar_activo_magerit(
                                eval_id,
                                activo_id,
                                resultado_ia.get("amenazas", []),
                                resultado_ia.get("probabilidad", 3),
                                resultado_ia.get("observaciones", ""),
                                modelo_ia,
                            )
                            guardar_resultado_magerit(resultado_magerit)
                            resultados_fase1.append(
                                f"✅ {activo_id}: {len(resultado_magerit.amenazas)} amenazas"
                            )
                        else:
                            resultados_fase1.append(f"⚠️ {activo_id}: {mensaje_ia[:150]}")
                    except Exception as e:
                        resultados_fase1.append(f"❌ {activo_id}: {str(e)[:150]}")

                    progress_fase1.progress((i + 1) / total_f1)

                progress_fase1.progress(1.0, text="✅ Fase 1 completada")
                exitos_f1 = sum(1 for r in resultados_fase1 if r.startswith("✅"))
                st.success(f"Fase 1: {exitos_f1}/{total_f1} activos evaluados correctamente")

                _dur_f1 = (dt.datetime.now() - _inicio_global).total_seconds()
                registrar_proceso_rapido(
                    eval_id,
                    "analisis_completo_fase1",
                    "IA",
                    f"Fase 1 análisis completo: {exitos_f1}/{total_f1} activos en {_dur_f1:.1f}s",
                    detalles={"activos": total_f1, "exitosos": exitos_f1, "duracion_seg": _dur_f1},
                )

                with st.expander("📋 Detalles Fase 1", expanded=False):
                    for log in resultados_fase1:
                        if log.startswith("✅"):
                            st.success(log)
                        elif log.startswith("⚠️"):
                            st.warning(log)
                        else:
                            st.error(log)
            else:
                st.info("ℹ️ Todos los activos ya están evaluados. Saltando Fase 1.")

            # ═══════════════════════════════════════════════════════════════
            # FASE 2: Generación de planes de tratamiento
            # ═══════════════════════════════════════════════════════════════
            st.markdown("#### 🛡️ Fase 2/5 — Planes de Tratamiento")

            _inicio_f2 = dt.datetime.now()
            progress_fase2 = st.progress(0, text="Generando planes de tratamiento...")

            try:
                progress_fase2.progress(0.3, text="Analizando riesgos ALTO y CRÍTICO...")
                planes = generar_planes_evaluacion(eval_id, modelo_ia)
                progress_fase2.progress(1.0, text="✅ Fase 2 completada")

                if planes:
                    st.success(f"Fase 2: {len(planes)} planes de tratamiento generados")
                else:
                    st.info("ℹ️ No se encontraron riesgos ALTO/CRÍTICO que requieran planes.")

                _dur_f2 = (dt.datetime.now() - _inicio_f2).total_seconds()
                registrar_proceso_rapido(
                    eval_id,
                    "analisis_completo_fase2",
                    "TRATAMIENTO",
                    f"Fase 2: {len(planes)} planes generados en {_dur_f2:.1f}s",
                    detalles={"planes": len(planes), "duracion_seg": _dur_f2},
                )
            except Exception as e:
                progress_fase2.progress(1.0, text="⚠️ Fase 2 con errores")
                st.warning(f"⚠️ Error generando planes: {str(e)[:200]}")

            # ═══════════════════════════════════════════════════════════════
            # FASE 3: Cálculo de nivel de madurez
            # ═══════════════════════════════════════════════════════════════
            st.markdown("#### 🎯 Fase 3/5 — Nivel de Madurez")

            _inicio_f3 = dt.datetime.now()
            progress_fase3 = st.progress(0, text="Calculando nivel de madurez...")

            try:
                progress_fase3.progress(0.5, text="Procesando dominios de seguridad...")
                resultado_madurez = calcular_madurez_evaluacion(eval_id)

                if resultado_madurez:
                    guardar_madurez(resultado_madurez)
                    progress_fase3.progress(1.0, text="✅ Fase 3 completada")
                    st.success(
                        f"Fase 3: Madurez calculada — **{resultado_madurez.puntuacion_total:.0f}%** "
                        f"({resultado_madurez.nombre_nivel})"
                    )
                else:
                    progress_fase3.progress(1.0, text="⚠️ Sin datos suficientes")
                    st.warning("⚠️ No se pudo calcular madurez. Verifique activos y respuestas.")

                _dur_f3 = (dt.datetime.now() - _inicio_f3).total_seconds()
                registrar_proceso_rapido(
                    eval_id,
                    "analisis_completo_fase3",
                    "MADUREZ",
                    f"Fase 3: Madurez {resultado_madurez.puntuacion_total:.0f}% en {_dur_f3:.1f}s"
                    if resultado_madurez
                    else f"Fase 3: Sin datos suficientes ({_dur_f3:.1f}s)",
                    detalles={"duracion_seg": _dur_f3},
                )
            except Exception as e:
                progress_fase3.progress(1.0, text="⚠️ Fase 3 con errores")
                st.warning(f"⚠️ Error calculando madurez: {str(e)[:200]}")

            # ═══════════════════════════════════════════════════════════════
            # FASE 4: Resumen Ejecutivo
            # ═══════════════════════════════════════════════════════════════
            st.markdown("#### 📄 Fase 4/5 — Resumen Ejecutivo")

            _inicio_f4 = dt.datetime.now()
            progress_fase4 = st.progress(0, text="Generando resumen ejecutivo...")
            resumen_exec = None

            try:
                progress_fase4.progress(0.3, text="Recopilando datos de la evaluación...")
                exito_resumen, resumen_exec, msg_resumen = generar_resumen_ejecutivo(
                    eval_id, modelo_ia
                )
                progress_fase4.progress(1.0, text="✅ Fase 4 completada")

                if exito_resumen and resumen_exec:
                    st.success(
                        f"Fase 4: Resumen ejecutivo generado — "
                        f"Nivel general: {getattr(resumen_exec, 'nivel_riesgo_general', 'N/A')}"
                    )
                else:
                    st.info(f"ℹ️ {msg_resumen}")

                _dur_f4 = (dt.datetime.now() - _inicio_f4).total_seconds()
                registrar_proceso_rapido(
                    eval_id,
                    "analisis_completo_fase4",
                    "RESUMEN",
                    f"Fase 4: Resumen ejecutivo en {_dur_f4:.1f}s",
                    detalles={"exito": exito_resumen, "duracion_seg": _dur_f4},
                )
            except Exception as e:
                progress_fase4.progress(1.0, text="⚠️ Fase 4 con errores")
                st.warning(f"⚠️ Error generando resumen: {str(e)[:200]}")

            # ═══════════════════════════════════════════════════════════════
            # FASE 5: Priorización de Controles
            # ═══════════════════════════════════════════════════════════════
            st.markdown("#### ⚡ Fase 5/5 — Priorización de Controles")

            _inicio_f5 = dt.datetime.now()
            progress_fase5 = st.progress(0, text="Priorizando controles por ROI...")
            controles_priorizados = []

            try:
                progress_fase5.progress(0.3, text="Analizando controles recomendados...")
                exito_prio, controles_priorizados, msg_prio = generar_priorizacion_controles(
                    eval_id, modelo_ia
                )
                progress_fase5.progress(1.0, text="✅ Fase 5 completada")

                if exito_prio and controles_priorizados:
                    st.success(
                        f"Fase 5: {len(controles_priorizados)} controles priorizados por ROI"
                    )
                else:
                    st.info(f"ℹ️ {msg_prio}")

                _dur_f5 = (dt.datetime.now() - _inicio_f5).total_seconds()
                registrar_proceso_rapido(
                    eval_id,
                    "analisis_completo_fase5",
                    "PRIORIZACION",
                    f"Fase 5: {len(controles_priorizados)} controles priorizados en {_dur_f5:.1f}s",
                    detalles={"controles": len(controles_priorizados), "duracion_seg": _dur_f5},
                )
            except Exception as e:
                progress_fase5.progress(1.0, text="⚠️ Fase 5 con errores")
                st.warning(f"⚠️ Error priorizando controles: {str(e)[:200]}")

            # ═══════════════════════════════════════════════════════════════
            # RESUMEN FINAL
            # ═══════════════════════════════════════════════════════════════
            _duracion_total = (dt.datetime.now() - _inicio_global).total_seconds()

            st.divider()
            st.markdown("### 📊 Resumen del Análisis Completo")

            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            col_r1.metric("⏱️ Duración Total", f"{_duracion_total:.1f}s")
            col_r2.metric(
                "📡 Activos Analizados",
                f"{len(activos_listos)} nuevos + {len(activos_evaluados)} previos",
            )
            col_r3.metric(
                "🛡️ Planes Generados",
                len(planes) if "planes" in dir() else 0,
            )
            col_r4.metric(
                "⚡ Controles Priorizados",
                len(controles_priorizados) if controles_priorizados else 0,
            )

            registrar_proceso_rapido(
                eval_id,
                "analisis_completo",
                "PIPELINE",
                f"Análisis completo finalizado en {_duracion_total:.1f}s",
                detalles={
                    "activos_nuevos": len(activos_listos),
                    "activos_previos": len(activos_evaluados),
                    "duracion_total_seg": _duracion_total,
                },
            )

            st.success("🎉 **Análisis completo finalizado.** Revisa el Dashboard y Madurez para ver resultados.")

            if st.button("🔄 Actualizar Vista", key="btn_refresh_analisis_completo"):
                st.rerun()

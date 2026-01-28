"""
Componentes visuales del Proyecto TITA
"""

from .dashboard_magerit import (
    render_mapa_calor_riesgos,
    render_ranking_activos,
    render_comparativo_riesgos,
    render_distribucion_amenazas,
    render_cobertura_controles,
    render_resumen_ejecutivo,
    render_detalle_activo,
    render_gauge_riesgo,
    render_gauge_madurez,
    render_radar_dominios,
    render_madurez_completo,
    render_comparativa_madurez,
    render_controles_existentes,
    render_ranking_activos_criticos,
    render_activos_urgente_tratamiento,
    render_dashboard_amenazas,
    render_dashboard_amenazas_mejorado,
    render_dashboard_controles_salvaguardas,
    render_dashboard_evaluacion_completo,
    render_matriz_5x5_activos,
    COLORES_RIESGO,
    COLORES_MADUREZ,
    NOMBRES_MADUREZ
)

from .ia_validation_ui import (
    render_tab_validacion_ia,
    render_estado_ia_badge,
    render_boton_evaluar_bloqueado,
    verificar_ia_lista_para_evaluar,
    render_indicador_ia_en_header,
    render_resultado_validacion,
    render_seccion_evidencias
)

from .carga_masiva_ui import (
    render_carga_masiva,
    render_carga_masiva_modal
)

from .concentration_risk_ui import (
    render_asignacion_dependencias,
    render_dashboard_concentracion,
    render_concentracion_mini_card,
    render_concentracion_tab
)

from .ia_advanced_ui import (
    render_ia_avanzada_ui
)

from .degradacion_ui import (
    render_degradacion_tab
)

from .vulnerabilidades_ui import (
    render_vulnerabilidades_tab
)

from .tratamiento_ui import (
    render_tratamiento_tab
)

from .comparativa_ui import (
    render_comparativa_tab
)

from .auditoria_ui import (
    render_auditoria_tab
)

__all__ = [
    # Dashboard MAGERIT
    'render_mapa_calor_riesgos',
    'render_ranking_activos',
    'render_comparativo_riesgos',
    'render_distribucion_amenazas',
    'render_cobertura_controles',
    'render_resumen_ejecutivo',
    'render_detalle_activo',
    'render_gauge_riesgo',
    'render_gauge_madurez',
    'render_radar_dominios',
    'render_madurez_completo',
    'render_comparativa_madurez',
    'render_controles_existentes',
    'COLORES_RIESGO',
    'COLORES_MADUREZ',
    'NOMBRES_MADUREZ',
    # Validación IA
    'render_tab_validacion_ia',
    'render_estado_ia_badge',
    'render_boton_evaluar_bloqueado',
    'verificar_ia_lista_para_evaluar',
    'render_indicador_ia_en_header',
    'render_resultado_validacion',
    'render_seccion_evidencias',
    # Carga Masiva
    'render_carga_masiva',
    'render_carga_masiva_modal',
    # Riesgo por Concentración
    'render_asignacion_dependencias',
    'render_dashboard_concentracion',
    'render_concentracion_mini_card',
    'render_concentracion_tab',
    # IA Avanzada
    'render_ia_avanzada_ui',
    # Degradación
    'render_degradacion_tab',
    # Vulnerabilidades
    'render_vulnerabilidades_tab',
    # Tratamiento
    'render_tratamiento_tab',
    # Comparativa
    'render_comparativa_tab',
    # Auditoría
    'render_auditoria_tab'
]

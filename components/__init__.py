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
    'render_carga_masiva_modal'
]

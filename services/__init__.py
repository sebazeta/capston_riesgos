"""
Servicios del Proyecto TITA - Versión SQLite (anti-corrupción)
"""

# Base de datos SQLite (reemplaza Excel para evitar corrupción)
from .database_service import (
    init_database,
    read_table,
    insert_rows,
    insert_row,
    update_row,
    delete_row,
    delete_rows,
    query_rows,
    row_exists,
    upsert_row,
    read_sheet,      # Compatibilidad con código existente
    append_rows,     # Compatibilidad con código existente
    set_eval_active, # Compatibilidad con código existente
    ensure_workbook,
    ensure_sheet_exists,
    update_cuestionarios_version,
    exportar_a_excel,
    DB_PATH
)

from .ollama_service import (
    ollama_generate,
    ollama_analyze_risk,
    extract_json_array,
    validate_ia_questions
)

from .evaluacion_service import (
    crear_evaluacion,
    get_evaluaciones,
    actualizar_estado_evaluacion,
    get_activos_por_evaluacion,
    get_estadisticas_evaluacion
)

from .activo_service import (
    crear_activo,
    editar_activo,
    eliminar_activo,
    get_activo,
    actualizar_estado_activo,
    validar_duplicado
)

from .cuestionario_service import (
    generar_cuestionario,
    get_cuestionario,
    get_versiones_cuestionario,
    guardar_respuestas,
    get_respuestas,
    verificar_cuestionario_completo,
    get_banco_preguntas,
    invalidar_analisis_ia,
    verificar_respuestas_existentes
)

# Motor de Evaluación MAGERIT v3
from .magerit_engine import (
    ImpactoDIC,
    AmenazaIdentificada,
    ResultadoEvaluacionMagerit,
    get_nivel_riesgo,
    get_color_riesgo,
    get_accion_riesgo,
    calcular_impacto_desde_respuestas,
    identificar_controles_existentes,
    evaluar_activo_magerit,
    guardar_resultado_magerit,
    get_resultado_magerit,
    get_amenazas_activo,
    get_resumen_evaluacion
)

# Servicio de IA para MAGERIT
from .ollama_magerit_service import (
    analizar_activo_con_ia,
    verificar_ollama_disponible,
    crear_evaluacion_manual,
    get_catalogo_amenazas,
    get_catalogo_controles
)

# Servicio de Validación de IA Local
from .ia_validation_service import (
    ejecutar_validacion_completa,
    obtener_estado_ia,
    obtener_evidencias_recientes,
    obtener_logs_validacion,
    verificar_ollama_local,
    guardar_evidencia,
    IAValidationResult,
    IAExecutionEvidence
)

# Knowledge Base Service
from .knowledge_base_service import (
    construir_knowledge_context,
    construir_prompt_evaluacion_activo,
    obtener_resumen_catalogos,
    validar_respuesta_ia_contra_catalogos,
    exportar_knowledge_base_json,
    KnowledgeContext
)

# Servicio de Madurez de Ciberseguridad
from .maturity_service import (
    calcular_madurez_evaluacion,
    guardar_madurez,
    get_madurez_evaluacion,
    comparar_madurez,
    get_controles_existentes_detallados,
    analizar_controles_desde_respuestas,
    ResultadoMadurez
)

# Servicio de Carga Masiva de Activos
from .carga_masiva_service import (
    procesar_json,
    procesar_excel,
    generar_plantilla_json,
    generar_plantilla_excel,
    get_campos_info,
    ResultadoCarga,
    ErrorValidacion
)

# Servicio de Riesgo por Concentración (Host-VM)
from .concentration_risk_service import (
    init_concentration_tables,
    asignar_host_a_vm,
    get_vms_de_host,
    get_hosts_evaluacion,
    calcular_blast_radius,
    calcular_riesgo_heredado,
    calcular_concentracion_evaluacion,
    calcular_herencia_evaluacion,
    get_hosts_spof,
    get_ranking_hosts_blast_radius,
    get_vms_con_riesgo_heredado,
    get_resumen_concentracion,
    DependenciaVM,
    ResultadoConcentracion,
    RiesgoHeredado
)

# Servicio de IA Avanzada
from .ia_advanced_service import (
    generar_plan_tratamiento,
    generar_planes_evaluacion,
    consultar_chatbot_magerit,
    generar_resumen_ejecutivo,
    generar_prediccion_riesgo,
    generar_priorizacion_controles,
    verificar_ia_disponible,
    obtener_amenazas_evaluacion,
    obtener_controles_evaluacion,
    guardar_resultado_ia,
    cargar_resultado_ia,
    eliminar_resultado_ia,
    PlanTratamiento,
    ResumenEjecutivo,
    PrediccionRiesgo,
    ControlPriorizado
)

# Servicio de Exportación
from .export_service import (
    generar_documento_ejecutivo,
    generar_datos_powerbi,
    exportar_powerbi_excel,
    exportar_powerbi_csv
)

__all__ = [
    # Database SQLite
    'init_database',
    'read_table',
    'insert_rows',
    'update_row',
    'delete_row',
    'query_rows',
    'read_sheet',
    'append_rows',
    'set_eval_active',
    'export_to_excel',
    'DB_PATH',
    # Ollama
    'ollama_generate',
    'ollama_analyze_risk',
    'extract_json_array',
    'validate_ia_questions',
    # Evaluaciones
    'crear_evaluacion',
    'get_evaluaciones',
    'actualizar_estado_evaluacion',
    'get_activos_por_evaluacion',
    'get_estadisticas_evaluacion',
    # Activos
    'crear_activo',
    'editar_activo',
    'eliminar_activo',
    'get_activo',
    'actualizar_estado_activo',
    'validar_duplicado',
    # Cuestionarios
    'generar_cuestionario',
    'get_cuestionario',
    'get_versiones_cuestionario',
    'guardar_respuestas',
    'get_respuestas',
    'verificar_cuestionario_completo',
    'get_banco_preguntas',
    'invalidar_analisis_ia',
    'verificar_respuestas_existentes',
    # MAGERIT Engine
    'ImpactoDIC',
    'AmenazaIdentificada',
    'ResultadoEvaluacionMagerit',
    'get_nivel_riesgo',
    'get_color_riesgo',
    'get_accion_riesgo',
    'calcular_impacto_desde_respuestas',
    'identificar_controles_existentes',
    'evaluar_activo_magerit',
    'guardar_resultado_magerit',
    'get_resultado_magerit',
    'get_amenazas_activo',
    'get_resumen_evaluacion',
    # IA MAGERIT Service
    'analizar_activo_con_ia',
    'verificar_ollama_disponible',
    'crear_evaluacion_manual',
    'get_catalogo_amenazas',
    'get_catalogo_controles',
    # IA Validation Service
    'ejecutar_validacion_completa',
    'obtener_estado_ia',
    'obtener_evidencias_recientes',
    'obtener_logs_validacion',
    'verificar_ollama_local',
    'guardar_evidencia',
    'IAValidationResult',
    'IAExecutionEvidence',
    # Knowledge Base Service
    'construir_knowledge_context',
    'construir_prompt_evaluacion_activo',
    'obtener_resumen_catalogos',
    'validar_respuesta_ia_contra_catalogos',
    'exportar_knowledge_base_json',
    'KnowledgeContext',
    # Maturity Service
    'calcular_madurez_evaluacion',
    'guardar_madurez',
    'get_madurez_evaluacion',
    'comparar_madurez',
    'get_controles_existentes_detallados',
    'analizar_controles_desde_respuestas',
    'ResultadoMadurez',
    # Carga Masiva Service
    'procesar_json',
    'procesar_excel',
    'generar_plantilla_json',
    'generar_plantilla_excel',
    'get_campos_info',
    'ResultadoCarga',
    'ErrorValidacion',
    # Concentration Risk Service
    'init_concentration_tables',
    'asignar_host_a_vm',
    'get_vms_de_host',
    'get_hosts_evaluacion',
    'calcular_blast_radius',
    'calcular_riesgo_heredado',
    'calcular_concentracion_evaluacion',
    'calcular_herencia_evaluacion',
    'get_hosts_spof',
    'get_ranking_hosts_blast_radius',
    'get_vms_con_riesgo_heredado',
    'get_resumen_concentracion',
    'DependenciaVM',
    'ResultadoConcentracion',
    'RiesgoHeredado',
    # IA Advanced Service
    'generar_plan_tratamiento',
    'generar_planes_evaluacion',
    'consultar_chatbot_magerit',
    'generar_resumen_ejecutivo',
    'generar_prediccion_riesgo',
    'generar_priorizacion_controles',
    'verificar_ia_disponible',
    'PlanTratamiento',
    'ResumenEjecutivo',
    'PrediccionRiesgo',
    'ControlPriorizado'
]

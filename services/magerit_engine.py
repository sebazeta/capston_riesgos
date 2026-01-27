"""
MOTOR DE EVALUACIÓN MAGERIT v3 COMPLETO
========================================
Calcula:
- Impacto DIC (Disponibilidad, Integridad, Confidencialidad)
- Probabilidad MAGERIT (1-5)
- Riesgo Inherente por amenaza
- Controles existentes (del cuestionario)
- Riesgo Residual
- Recomendaciones de controles ISO 27002

Todo con trazabilidad completa guardada en SQLite.
"""
import json
import datetime as dt
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from services.database_service import (
    read_table, insert_rows, update_row, delete_row,
    query_rows, get_connection
)


# ==================== MODELOS DE DATOS ====================

@dataclass
class ImpactoDIC:
    """Valoración de impacto en las tres dimensiones"""
    disponibilidad: int  # 1-5
    integridad: int      # 1-5
    confidencialidad: int  # 1-5
    justificacion_d: str = ""
    justificacion_i: str = ""
    justificacion_c: str = ""
    
    @property
    def impacto_global(self) -> int:
        """Impacto global = máximo de las tres dimensiones"""
        return max(self.disponibilidad, self.integridad, self.confidencialidad)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AmenazaIdentificada:
    """Una amenaza identificada para un activo"""
    codigo: str              # Código MAGERIT (ej: A.24)
    amenaza: str             # Nombre de la amenaza
    tipo_amenaza: str        # Categoría
    dimension_afectada: str  # D, I, C o combinaciones
    probabilidad: int        # 1-5
    impacto: int             # 1-5 (de la dimensión afectada)
    riesgo_inherente: int    # probabilidad × impacto
    nivel_riesgo: str        # MUY BAJO, BAJO, MEDIO, ALTO, CRÍTICO
    justificacion: str       # Por qué aplica esta amenaza
    controles_existentes: List[str]  # Códigos de controles ya implementados
    efectividad_controles: float  # 0.0 - 1.0
    riesgo_residual: float   # Riesgo después de controles
    nivel_riesgo_residual: str
    controles_recomendados: List[Dict]  # [{codigo, nombre, prioridad, motivo}]
    tratamiento: str         # mitigar, aceptar, transferir, evitar
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ResultadoEvaluacionMagerit:
    """Resultado completo de evaluación MAGERIT para un activo"""
    id_evaluacion: str
    id_activo: str
    nombre_activo: str
    tipo_activo: str
    fecha_evaluacion: str
    impacto: ImpactoDIC
    amenazas: List[AmenazaIdentificada]
    riesgo_inherente_global: float
    nivel_riesgo_inherente_global: str
    riesgo_residual_global: float
    nivel_riesgo_residual_global: str
    controles_existentes_global: List[str]
    controles_recomendados_global: List[Dict]
    observaciones: str
    modelo_ia: str
    
    def to_dict(self) -> Dict:
        return {
            "id_evaluacion": self.id_evaluacion,
            "id_activo": self.id_activo,
            "nombre_activo": self.nombre_activo,
            "tipo_activo": self.tipo_activo,
            "fecha_evaluacion": self.fecha_evaluacion,
            "impacto": self.impacto.to_dict(),
            "amenazas": [a.to_dict() for a in self.amenazas],
            "riesgo_inherente_global": self.riesgo_inherente_global,
            "nivel_riesgo_inherente_global": self.nivel_riesgo_inherente_global,
            "riesgo_residual_global": self.riesgo_residual_global,
            "nivel_riesgo_residual_global": self.nivel_riesgo_residual_global,
            "controles_existentes_global": self.controles_existentes_global,
            "controles_recomendados_global": self.controles_recomendados_global,
            "observaciones": self.observaciones,
            "modelo_ia": self.modelo_ia
        }


# ==================== FUNCIONES DE CRITERIOS ====================

def get_nivel_riesgo(valor: float) -> str:
    """Determina el nivel de riesgo según el valor (1-25)"""
    if valor >= 20:
        return "CRÍTICO"
    elif valor >= 12:
        return "ALTO"
    elif valor >= 6:
        return "MEDIO"
    elif valor >= 3:
        return "BAJO"
    else:
        return "MUY BAJO"


def get_color_riesgo(nivel: str) -> str:
    """Retorna el color asociado al nivel de riesgo"""
    colores = {
        "CRÍTICO": "#8B0000",  # Dark Red
        "ALTO": "#FF4500",     # Orange Red
        "MEDIO": "#FFA500",    # Orange
        "BAJO": "#32CD32",     # Lime Green
        "MUY BAJO": "#228B22"  # Forest Green
    }
    return colores.get(nivel, "#808080")


def get_accion_riesgo(nivel: str) -> str:
    """Retorna la acción recomendada según nivel de riesgo"""
    acciones = {
        "CRÍTICO": "Acción inmediata obligatoria",
        "ALTO": "Acción prioritaria en corto plazo",
        "MEDIO": "Planificar mitigación",
        "BAJO": "Monitorear",
        "MUY BAJO": "Aceptar"
    }
    return acciones.get(nivel, "Evaluar")


def get_tratamiento_sugerido(nivel: str, efectividad_controles: float) -> str:
    """Sugiere tratamiento basado en nivel y controles existentes"""
    if nivel in ["CRÍTICO", "ALTO"]:
        if efectividad_controles < 0.5:
            return "mitigar"
        else:
            return "mitigar"  # Aún con controles, requiere más acción
    elif nivel == "MEDIO":
        if efectividad_controles >= 0.7:
            return "aceptar"
        else:
            return "mitigar"
    elif nivel == "BAJO":
        return "monitorear"
    else:
        return "aceptar"


# ==================== CÁLCULO DE IMPACTO DIC ====================

# Preguntas que miden IMPACTO DIRECTO (valor alto = impacto alto)
# Estas son preguntas donde la opción más alta indica MAYOR IMPACTO
PREGUNTAS_IMPACTO_DIRECTO = {
    # Bloque A - Criticidad e Impacto (Crítico = 4 = impacto alto)
    # Físicos (PF-*)
    "PF-A01", "PF-A02", "PF-A03", "PF-A04", "PF-A05",
    # Virtuales (PV-*)
    "PV-A01", "PV-A02", "PV-A03", "PV-A04",
    # NOTA: PV-A05 (cluster) es CONTROL - valor alto = menor riesgo
}

# Preguntas que miden CONTROLES (valor bajo = sin control = impacto alto)
# Se INVIERTE la escala: 1 (sin control) → 4 (impacto alto), 4 (buen control) → 1 (impacto bajo)
PREGUNTAS_CONTROL_INVERTIDO = {
    # Bloque A - PV-A05 es control (cluster = protección)
    "PV-A05",
    # Bloque B - Continuidad y recuperación
    "PF-B01", "PF-B02", "PF-B03", "PF-B04",
    "PV-B01", "PV-B02", "PV-B03", "PV-B04",
    # Bloque C - Controles operativos
    "PF-C01", "PF-C02", "PF-C03", "PF-C04", "PF-C05",
    "PV-C01", "PV-C02", "PV-C03", "PV-C04", "PV-C05",
    # Bloque D - Ciberseguridad
    "PF-D01", "PF-D02", "PF-D03", "PF-D04",
    "PV-D01", "PV-D02", "PV-D03", "PV-D04",
    # Bloque E - Exposición (valor alto = menos exposición = menor riesgo)
    "PF-E01", "PF-E02", "PF-E03",
    "PV-E01", "PV-E02", "PV-E03",
}

# ==================== ESCALA INTERNA MAGERIT v3 (CALIBRADA) ====================
# Conversión de escala lineal (1-4) a escala MAGERIT calibrada
# CALIBRACIÓN v6: Escala con mejor distribución para 5 niveles
ESCALA_MAGERIT = {
    1: 1,  # Opción 1 → Impacto 1 (Muy Bajo)
    2: 2,  # Opción 2 → Impacto 2 (Bajo)
    3: 3,  # Opción 3 → Impacto 3 (Medio)
    4: 5,  # Opción 4 → Impacto 5 (Crítico)
}

def aplicar_escala_magerit(valor_original: int) -> int:
    """
    Convierte valor de escala lineal (1-4) a escala MAGERIT calibrada.
    CALIBRACIÓN: Escala más gradual (1,2,3,5) en lugar de (1,2,4,5)
    """
    return ESCALA_MAGERIT.get(valor_original, valor_original)


def calcular_impacto_desde_respuestas(respuestas: pd.DataFrame) -> ImpactoDIC:
    """
    Calcula el impacto DIC a partir de las respuestas del cuestionario.
    
    MAGERIT v3 - CALIBRADO para distribución equilibrada:
    1. Escala calibrada: 1→1, 2→2, 3→3, 4→5
    2. Fórmula HÍBRIDA: (MAX × 0.6) + (Promedio × 0.4)
    3. SOLO preguntas del BLOQUE A afectan el impacto
    4. Bloques B, C, D, E son controles y afectan solo PROBABILIDAD
    
    Las respuestas tienen:
    - Dimension: D, I o C
    - Valor_Numerico: 1-4
    - Peso: 1-5
    - ID_Pregunta: para identificar tipo de pregunta
    """
    if respuestas.empty:
        return ImpactoDIC(3, 3, 3, "Sin respuestas", "Sin respuestas", "Sin respuestas")
    
    impactos = {"D": [], "I": [], "C": []}
    pesos = {"D": [], "I": [], "C": []}
    
    def safe_int(val, default=3):
        """Convierte valor a entero de forma segura"""
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, bytes):
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
    
    for _, resp in respuestas.iterrows():
        dim = str(resp.get("Dimension", "")).upper()
        if dim not in impactos:
            continue
            
        id_pregunta = str(resp.get("ID_Pregunta", "")).upper()
        valor_original = safe_int(resp.get("Valor_Numerico", 2), 2)
        peso = safe_int(resp.get("Peso", 3), 3)
        
        # SOLO las preguntas del BLOQUE A (impacto directo) afectan el impacto
        # EXCEPCIÓN: PV-A05 (cluster) es un CONTROL, no afecta impacto
        # Las preguntas de los bloques B, C, D, E son CONTROLES y afectan PROBABILIDAD, no impacto
        es_bloque_a = any(x in id_pregunta for x in ["-A0", "-A-0"])
        es_control_a05 = "A05" in id_pregunta and "PV" in id_pregunta  # PV-A05 es control
        
        if not es_bloque_a or es_control_a05:
            # Ignorar bloques B, C, D, E y PV-A05 para el cálculo de impacto
            continue
        
        # Para Bloque A: valor alto = impacto alto
        valor_base = valor_original
        
        # Aplicar escala MAGERIT calibrada (1,2,3,5)
        valor_magerit = aplicar_escala_magerit(valor_base)
        
        impactos[dim].append(valor_magerit)
        pesos[dim].append(peso)
    
    def calcular_impacto_dimension(valores: List, pesos_list: List) -> Tuple[int, str]:
        """
        Calcula impacto por dimensión usando FÓRMULA HÍBRIDA.
        CALIBRACIÓN: (MAX × 0.6) + (Promedio ponderado × 0.4)
        Esto evita que un solo valor extremo eleve todo a CRÍTICO.
        """
        if not valores:
            return 3, "Sin datos suficientes"
        
        # Calcular MAX
        max_valor = max(valores)
        
        # Calcular promedio ponderado
        total_peso = sum(pesos_list) if pesos_list else 1
        if total_peso > 0:
            promedio_ponderado = sum(v * p for v, p in zip(valores, pesos_list)) / total_peso
        else:
            promedio_ponderado = sum(valores) / len(valores)
        
        # FÓRMULA HÍBRIDA CALIBRADA
        # MAX tiene peso 60%, Promedio tiene peso 40%
        impacto_hibrido = (max_valor * 0.6) + (promedio_ponderado * 0.4)
        
        # Solo si hay MUCHOS valores críticos (>=4 de 5), asegurar impacto máximo
        valores_criticos = sum(1 for v in valores if v >= 5)
        proporcion_criticos = valores_criticos / len(valores) if valores else 0
        
        if proporcion_criticos >= 0.7 and max_valor >= 5:
            # Más del 70% de respuestas críticas → impacto 5
            impacto_final = 5
        elif proporcion_criticos >= 0.5 and max_valor >= 5:
            # Más del 50% críticas → al menos 4
            impacto_final = max(round(impacto_hibrido), 4)
        else:
            # Caso normal: usar fórmula híbrida redondeada
            impacto_final = round(impacto_hibrido)
        
        impacto_final = max(1, min(5, impacto_final))
        
        justificacion = f"MAX={max_valor}, Prom={promedio_ponderado:.1f}, Híbrido={impacto_hibrido:.1f}, {len(valores)} resp"
        return impacto_final, justificacion
    
    d_valor, d_just = calcular_impacto_dimension(impactos["D"], pesos["D"])
    i_valor, i_just = calcular_impacto_dimension(impactos["I"], pesos["I"])
    c_valor, c_just = calcular_impacto_dimension(impactos["C"], pesos["C"])
    
    return ImpactoDIC(
        disponibilidad=d_valor,
        integridad=i_valor,
        confidencialidad=c_valor,
        justificacion_d=d_just,
        justificacion_i=i_just,
        justificacion_c=c_just
    )


# ==================== IDENTIFICACIÓN DE CONTROLES EXISTENTES ====================

# Mapeo de preguntas del cuestionario a controles ISO 27002
MAPEO_PREGUNTAS_CONTROLES = {
    # Bloque A - Impacto (RTO/RPO -> Continuidad)
    "A01": ["5.29", "5.30"],  # RTO -> Continuidad
    "A02": ["5.9"],           # Dependencias -> Inventario
    "A03": ["8.13"],          # RPO -> Backups
    "A04": ["5.12", "5.13"],  # Clasificación información
    "A05": ["5.29"],          # Impacto financiero -> Continuidad
    
    # Bloque B - Continuidad
    "B01": ["8.14", "5.30"],  # Failover -> Redundancia, Continuidad
    "B02": ["8.13"],          # Backups
    "B03": ["8.13", "5.30"],  # Restauración probada
    "B04": ["7.11"],          # UPS -> Servicios de apoyo
    
    # Bloque C - Controles
    "C01": ["5.15", "5.16", "5.17", "8.5"],  # Control de acceso, MFA
    "C02": ["8.8"],           # Parches -> Gestión vulnerabilidades
    "C03": ["8.16"],          # Monitoreo
    "C04": ["8.15"],          # Logs
    "C05": ["8.22"],          # Segmentación de red
    
    # Bloque D - Ciberseguridad
    "D01": ["8.7"],           # Antimalware
    "D02": ["8.24"],          # Cifrado
    "D03": ["8.8"],           # Análisis vulnerabilidades
    "D04": ["8.13", "8.7"],   # Protección ransomware
    
    # Bloque E - Exposición
    "E01": ["8.20", "8.21"],  # Exposición Internet -> Seguridad redes
    "E02": ["7.1", "7.2"],    # Acceso físico
    "E03": ["5.19", "5.21"],  # Dependencias externas -> Proveedores
}


def identificar_controles_existentes(respuestas: pd.DataFrame) -> Tuple[List[str], float, Dict]:
    """
    Identifica controles existentes basándose en respuestas del cuestionario.
    
    IMPORTANTE: Esta función NUNCA retorna "no se identificaron controles"
    si hay respuestas. Siempre hace el mapeo y reporta el estado real.
    
    Valor_Numerico:
    - 1 = No implementado (0% efectividad)
    - 2 = Parcial/Ad-hoc (33% efectividad)
    - 3 = Implementado (66% efectividad)
    - 4 = Implementado y medido (100% efectividad)
    
    Returns:
        (lista de códigos de controles implementados, efectividad promedio 0-1, detalle)
    """
    detalle = {
        "controles_implementados": [],
        "controles_parciales": [],
        "controles_no_implementados": [],
        "por_pregunta": {}
    }
    
    if respuestas.empty:
        return [], 0.0, detalle
    
    controles_por_nivel = {
        "implementados": set(),
        "parciales": set(),
        "no_implementados": set()
    }
    efectividades = []
    
    for _, resp in respuestas.iterrows():
        id_pregunta = str(resp.get("ID_Pregunta", ""))
        valor = int(resp.get("Valor_Numerico", 1))
        pregunta_texto = str(resp.get("Pregunta", ""))[:100]
        
        # Extraer código de pregunta (ej: PF-A01 -> A01, PV-B02 -> B02)
        partes = id_pregunta.split("-")
        if len(partes) >= 2:
            codigo_pregunta = partes[-1]  # A01, B02, etc.
        else:
            codigo_pregunta = id_pregunta
        
        # Buscar controles asociados
        if codigo_pregunta in MAPEO_PREGUNTAS_CONTROLES:
            controles = MAPEO_PREGUNTAS_CONTROLES[codigo_pregunta]
            
            # Calcular efectividad (1=0%, 2=33%, 3=66%, 4=100%)
            efectividad = (valor - 1) / 3.0
            efectividades.append(efectividad)
            
            # Clasificar controles según nivel
            for ctrl in controles:
                if valor >= 3:  # Implementado o mejor
                    controles_por_nivel["implementados"].add(ctrl)
                elif valor == 2:  # Parcial
                    controles_por_nivel["parciales"].add(ctrl)
                else:  # No implementado
                    controles_por_nivel["no_implementados"].add(ctrl)
            
            # Guardar detalle por pregunta
            detalle["por_pregunta"][codigo_pregunta] = {
                "pregunta": pregunta_texto,
                "valor": valor,
                "efectividad": efectividad,
                "controles": controles,
                "estado": "Implementado" if valor >= 3 else "Parcial" if valor == 2 else "No implementado"
            }
    
    # Consolidar (un control puede aparecer en varias preguntas, tomar el mejor nivel)
    controles_implementados = list(controles_por_nivel["implementados"])
    controles_parciales = list(controles_por_nivel["parciales"] - controles_por_nivel["implementados"])
    controles_no_impl = list(controles_por_nivel["no_implementados"] - controles_por_nivel["implementados"] - controles_por_nivel["parciales"])
    
    detalle["controles_implementados"] = controles_implementados
    detalle["controles_parciales"] = controles_parciales
    detalle["controles_no_implementados"] = controles_no_impl
    
    # Todos los controles identificados (cualquier nivel)
    todos_controles = controles_implementados + controles_parciales
    
    efectividad_promedio = sum(efectividades) / len(efectividades) if efectividades else 0.0
    
    return todos_controles, efectividad_promedio, detalle


# ==================== MAPEO AMENAZAS -> CONTROLES ====================

# Qué controles mitigan cada tipo de amenaza
MAPEO_AMENAZAS_CONTROLES = {
    # Desastres Naturales
    "N.1": ["7.5", "7.11", "8.14", "5.29", "5.30"],  # Fuego
    "N.2": ["7.5", "7.11", "8.14", "5.29", "5.30"],  # Agua
    "N.*": ["7.5", "8.14", "5.29", "5.30"],          # Otros desastres
    
    # Origen Industrial
    "I.1": ["7.5", "7.11"],
    "I.2": ["7.5", "7.11"],
    "I.3": ["7.8", "7.13"],
    "I.4": ["7.8", "7.12"],
    "I.5": ["7.13", "8.13", "8.14"],
    "I.6": ["7.11", "8.14"],
    "I.7": ["7.11"],
    "I.8": ["8.14", "8.20", "8.21"],
    "I.9": ["5.19", "5.22", "8.14"],
    "I.10": ["7.10", "8.13"],
    "I.11": ["7.8", "7.12"],
    
    # Errores no Intencionados
    "E.1": ["6.3", "5.10", "8.9"],
    "E.2": ["6.3", "8.9", "8.2"],
    "E.3": ["8.15", "8.16"],
    "E.4": ["8.9", "8.32"],
    "E.7": ["5.1", "5.2", "5.37"],
    "E.8": ["8.7", "6.3"],
    "E.9": ["8.20", "8.21"],
    "E.10": ["8.9", "8.32"],
    "E.14": ["8.12", "5.14"],
    "E.15": ["8.13", "8.9"],
    "E.18": ["8.13", "8.10"],
    "E.19": ["5.12", "5.14", "8.12"],
    "E.20": ["8.8", "8.28", "8.29"],
    "E.21": ["8.8", "8.32", "7.13"],
    "E.23": ["6.3", "5.10"],
    "E.25": ["7.9", "5.11"],
    "E.28": ["5.3", "5.30"],
    
    # Ataques Intencionados
    "A.3": ["8.15", "8.16", "8.9"],
    "A.4": ["8.9", "8.32", "8.2"],
    "A.5": ["8.5", "5.16", "5.17"],
    "A.6": ["8.2", "5.18", "8.15"],
    "A.7": ["5.10", "8.19"],
    "A.8": ["8.7", "8.8", "8.23"],
    "A.9": ["8.20", "8.21", "8.22"],
    "A.10": ["8.9", "8.15"],
    "A.11": ["5.15", "8.5", "8.20", "8.3"],
    "A.15": ["8.9", "8.15", "8.13"],
    "A.18": ["8.13", "8.10", "5.28"],
    "A.19": ["5.12", "8.12", "8.24"],
    "A.22": ["8.4", "8.28", "8.29"],
    "A.23": ["7.1", "7.2", "7.4"],
    "A.24": ["8.20", "8.6", "8.14"],
    "A.25": ["7.1", "7.2", "7.9", "7.10"],
    "A.26": ["7.1", "7.5", "8.14", "5.29"],
    "A.27": ["7.1", "7.6", "5.29"],
    "A.28": ["5.3", "6.5", "5.30"],
    "A.29": ["8.13", "8.7", "5.24", "5.26"],
    "A.30": ["6.3", "6.8", "8.5"],
}


def get_controles_para_amenaza(codigo_amenaza: str) -> List[str]:
    """Retorna los controles ISO que mitigan una amenaza específica"""
    return MAPEO_AMENAZAS_CONTROLES.get(codigo_amenaza, [])


# ==================== CÁLCULO DE RIESGO RESIDUAL ====================

def calcular_riesgo_residual(
    riesgo_inherente: int,
    controles_requeridos: List[str],
    controles_existentes: List[str],
    efectividad_base: float
) -> Tuple[float, float]:
    """
    Calcula el riesgo residual después de aplicar controles.
    
    Fórmula: Riesgo Residual = Riesgo Inherente × (1 - Cobertura × Efectividad)
    
    Cobertura = controles existentes / controles requeridos
    Efectividad = qué tan bien están implementados (0-1)
    
    Returns:
        (riesgo_residual, efectividad_real)
    """
    if not controles_requeridos:
        return float(riesgo_inherente), 0.0
    
    # Calcular cobertura
    controles_cubiertos = set(controles_requeridos) & set(controles_existentes)
    cobertura = len(controles_cubiertos) / len(controles_requeridos)
    
    # Efectividad real = cobertura × efectividad base
    efectividad_real = cobertura * efectividad_base
    
    # Riesgo residual
    factor_reduccion = 1 - (efectividad_real * 0.8)  # Máximo 80% reducción
    riesgo_residual = riesgo_inherente * factor_reduccion
    
    return max(1.0, riesgo_residual), efectividad_real


# ==================== MOTOR PRINCIPAL ====================

def evaluar_activo_magerit(
    eval_id: str,
    activo_id: str,
    amenazas_ia: List[Dict],
    probabilidad_ia: int,
    observaciones_ia: str = "",
    modelo_ia: str = "manual"
) -> ResultadoEvaluacionMagerit:
    """
    Ejecuta la evaluación MAGERIT completa para un activo.
    
    Args:
        eval_id: ID de la evaluación
        activo_id: ID del activo
        amenazas_ia: Lista de amenazas identificadas por IA con estructura:
            [{codigo, dimension, justificacion, controles_iso_recomendados: [{control, prioridad, motivo}]}]
        probabilidad_ia: Probabilidad base (1-5) determinada por IA
        observaciones_ia: Observaciones adicionales de la IA
        modelo_ia: Modelo de IA usado
    
    Returns:
        ResultadoEvaluacionMagerit con todos los cálculos
    """
    # 1. Obtener datos del activo
    activos = read_table("INVENTARIO_ACTIVOS")
    activo = activos[activos["ID_Activo"] == activo_id]
    
    if activo.empty:
        raise ValueError(f"Activo {activo_id} no encontrado")
    
    activo = activo.iloc[0]
    nombre_activo = activo.get("Nombre_Activo", "")
    tipo_activo = activo.get("Tipo_Activo", "")
    
    # 2. Obtener respuestas del cuestionario
    respuestas = read_table("RESPUESTAS")
    respuestas_activo = respuestas[
        (respuestas["ID_Evaluacion"] == eval_id) &
        (respuestas["ID_Activo"] == activo_id)
    ]
    
    # 3. Calcular impacto DIC desde respuestas
    impacto = calcular_impacto_desde_respuestas(respuestas_activo)
    
    # 4. Identificar controles existentes (NUNCA retorna vacío si hay respuestas)
    controles_existentes, efectividad_base, detalle_controles = identificar_controles_existentes(respuestas_activo)
    
    # 5. Obtener catálogo de amenazas para validación
    catalogo_amenazas = read_table("CATALOGO_AMENAZAS_MAGERIT")
    codigos_validos = set(catalogo_amenazas["codigo"].tolist()) if not catalogo_amenazas.empty else set()
    
    # 6. Obtener catálogo de controles para validación
    catalogo_controles = read_table("CATALOGO_CONTROLES_ISO27002")
    controles_validos = set(catalogo_controles["codigo"].tolist()) if not catalogo_controles.empty else set()
    
    # 7. Procesar cada amenaza identificada por la IA
    amenazas_procesadas = []
    riesgos_inherentes = []
    riesgos_residuales = []
    todos_controles_recomendados = []
    
    for amenaza_data in amenazas_ia:
        codigo = amenaza_data.get("codigo", "")
        
        # Validar código de amenaza
        if codigo not in codigos_validos:
            continue  # Ignorar amenazas no válidas
        
        # Obtener info de la amenaza del catálogo
        amenaza_info = catalogo_amenazas[catalogo_amenazas["codigo"] == codigo].iloc[0]
        
        # Determinar dimensión afectada e impacto
        dimension = amenaza_data.get("dimension", "D").upper()
        if dimension == "D":
            impacto_amenaza = impacto.disponibilidad
        elif dimension == "I":
            impacto_amenaza = impacto.integridad
        elif dimension == "C":
            impacto_amenaza = impacto.confidencialidad
        else:
            impacto_amenaza = impacto.impacto_global
        
        # Calcular riesgo inherente
        riesgo_inherente = probabilidad_ia * impacto_amenaza
        nivel_riesgo = get_nivel_riesgo(riesgo_inherente)
        
        # Obtener controles que mitigan esta amenaza
        controles_para_amenaza = get_controles_para_amenaza(codigo)
        
        # Calcular riesgo residual
        riesgo_residual, efectividad = calcular_riesgo_residual(
            riesgo_inherente,
            controles_para_amenaza,
            controles_existentes,
            efectividad_base
        )
        nivel_riesgo_residual = get_nivel_riesgo(riesgo_residual)
        
        # Procesar controles recomendados por la IA
        controles_rec = []
        for ctrl in amenaza_data.get("controles_iso_recomendados", []):
            codigo_ctrl = ctrl.get("control", "")
            if codigo_ctrl in controles_validos:
                # Obtener info del control
                ctrl_info = catalogo_controles[catalogo_controles["codigo"] == codigo_ctrl]
                if not ctrl_info.empty:
                    ctrl_info = ctrl_info.iloc[0]
                    controles_rec.append({
                        "codigo": codigo_ctrl,
                        "nombre": ctrl_info.get("nombre", ""),
                        "categoria": ctrl_info.get("categoria", ""),
                        "prioridad": ctrl.get("prioridad", "Media"),
                        "motivo": ctrl.get("motivo", "")
                    })
                    todos_controles_recomendados.append({
                        "codigo": codigo_ctrl,
                        "nombre": ctrl_info.get("nombre", ""),
                        "categoria": ctrl_info.get("categoria", ""),
                        "prioridad": ctrl.get("prioridad", "Media"),
                        "motivo": ctrl.get("motivo", ""),
                        "amenaza_origen": codigo
                    })
        
        # Determinar tratamiento
        tratamiento = get_tratamiento_sugerido(nivel_riesgo_residual, efectividad)
        
        # Crear objeto de amenaza identificada
        amenaza_procesada = AmenazaIdentificada(
            codigo=codigo,
            amenaza=amenaza_info.get("amenaza", ""),
            tipo_amenaza=amenaza_info.get("tipo_amenaza", ""),
            dimension_afectada=dimension,
            probabilidad=probabilidad_ia,
            impacto=impacto_amenaza,
            riesgo_inherente=riesgo_inherente,
            nivel_riesgo=nivel_riesgo,
            justificacion=amenaza_data.get("justificacion", ""),
            controles_existentes=[c for c in controles_para_amenaza if c in controles_existentes],
            efectividad_controles=efectividad,
            riesgo_residual=round(riesgo_residual, 2),
            nivel_riesgo_residual=nivel_riesgo_residual,
            controles_recomendados=controles_rec,
            tratamiento=tratamiento
        )
        
        amenazas_procesadas.append(amenaza_procesada)
        riesgos_inherentes.append(riesgo_inherente)
        riesgos_residuales.append(riesgo_residual)
    
    # 8. Calcular riesgos globales (máximo de todas las amenazas)
    riesgo_inherente_global = max(riesgos_inherentes) if riesgos_inherentes else 0
    riesgo_residual_global = max(riesgos_residuales) if riesgos_residuales else 0
    
    # 9. Crear resultado final
    resultado = ResultadoEvaluacionMagerit(
        id_evaluacion=eval_id,
        id_activo=activo_id,
        nombre_activo=nombre_activo,
        tipo_activo=tipo_activo,
        fecha_evaluacion=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        impacto=impacto,
        amenazas=amenazas_procesadas,
        riesgo_inherente_global=riesgo_inherente_global,
        nivel_riesgo_inherente_global=get_nivel_riesgo(riesgo_inherente_global),
        riesgo_residual_global=round(riesgo_residual_global, 2),
        nivel_riesgo_residual_global=get_nivel_riesgo(riesgo_residual_global),
        controles_existentes_global=controles_existentes,
        controles_recomendados_global=todos_controles_recomendados,
        observaciones=observaciones_ia,
        modelo_ia=modelo_ia
    )
    
    return resultado


def guardar_resultado_magerit(resultado: ResultadoEvaluacionMagerit) -> bool:
    """
    Guarda el resultado de la evaluación MAGERIT en SQLite.
    Usa la tabla RESULTADOS_MAGERIT existente.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que la tabla RESULTADOS_MAGERIT existe (debería existir desde init)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS RESULTADOS_MAGERIT (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_Evaluacion TEXT,
                    ID_Activo TEXT,
                    Nombre_Activo TEXT,
                    Impacto_D INTEGER,
                    Impacto_I INTEGER,
                    Impacto_C INTEGER,
                    Riesgo_Inherente REAL,
                    Riesgo_Residual REAL,
                    Nivel_Riesgo TEXT,
                    Amenazas_JSON TEXT,
                    Controles_JSON TEXT,
                    Observaciones TEXT,
                    Modelo_IA TEXT,
                    Fecha_Evaluacion TEXT
                )
            ''')
            
            # Eliminar resultados anteriores para este activo
            cursor.execute(
                'DELETE FROM RESULTADOS_MAGERIT WHERE ID_Evaluacion = ? AND ID_Activo = ?',
                [resultado.id_evaluacion, resultado.id_activo]
            )
            
            # Preparar amenazas como JSON
            amenazas_json = json.dumps([{
                "codigo": a.codigo,
                "amenaza": a.amenaza,
                "tipo_amenaza": a.tipo_amenaza,
                "dimension": a.dimension_afectada,
                "probabilidad": a.probabilidad,
                "impacto": a.impacto,
                "riesgo_inherente": a.riesgo_inherente,
                "nivel_riesgo": a.nivel_riesgo,
                "riesgo_residual": a.riesgo_residual,
                "tratamiento": a.tratamiento,
                "controles_recomendados": a.controles_recomendados
            } for a in resultado.amenazas], ensure_ascii=False)
            
            # Preparar controles como JSON
            controles_json = json.dumps(resultado.controles_existentes_global, ensure_ascii=False)
            
            # Insertar resultado
            cursor.execute('''
                INSERT INTO RESULTADOS_MAGERIT (
                    ID_Evaluacion, ID_Activo, Nombre_Activo,
                    Impacto_D, Impacto_I, Impacto_C,
                    Riesgo_Inherente, Riesgo_Residual, Nivel_Riesgo,
                    Amenazas_JSON, Controles_JSON, Observaciones, Modelo_IA, Fecha_Evaluacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                resultado.id_evaluacion,
                resultado.id_activo,
                resultado.nombre_activo,
                resultado.impacto.disponibilidad,
                resultado.impacto.integridad,
                resultado.impacto.confidencialidad,
                resultado.riesgo_inherente_global,
                resultado.riesgo_residual_global,
                resultado.nivel_riesgo_inherente_global,
                amenazas_json,
                controles_json,
                resultado.observaciones,
                resultado.modelo_ia,
                resultado.fecha_evaluacion
            ])
        
        return True
    
    except Exception as e:
        print(f"Error guardando resultado MAGERIT: {e}")
        return False


def get_resultado_magerit(eval_id: str, activo_id: str) -> Optional[Dict]:
    """Obtiene el resultado MAGERIT guardado para un activo"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT ID_Activo, Nombre_Activo, Impacto_D, Impacto_I, Impacto_C,
                   Riesgo_Inherente, Riesgo_Residual, Nivel_Riesgo, 
                   Amenazas_JSON, Controles_JSON, Observaciones, Modelo_IA, Fecha_Evaluacion
                FROM RESULTADOS_MAGERIT WHERE ID_Evaluacion = ? AND ID_Activo = ?''',
                [eval_id, activo_id]
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id_activo": row[0],
                    "nombre_activo": row[1],
                    "impacto_d": row[2],
                    "impacto_i": row[3],
                    "impacto_c": row[4],
                    "riesgo_inherente": row[5],
                    "riesgo_residual": row[6],
                    "nivel_riesgo": row[7],
                    "amenazas": json.loads(row[8]) if row[8] else [],
                    "controles": json.loads(row[9]) if row[9] else [],
                    "observaciones": row[10],
                    "modelo_ia": row[11],
                    "fecha": row[12]
                }
    except Exception as e:
        print(f"Error obteniendo resultado MAGERIT: {e}")
    return None


def get_amenazas_activo(eval_id: str, activo_id: str) -> pd.DataFrame:
    """Obtiene las amenazas identificadas para un activo desde RESULTADOS_MAGERIT"""
    try:
        resultado = get_resultado_magerit(eval_id, activo_id)
        if resultado and resultado.get("amenazas"):
            return pd.DataFrame(resultado["amenazas"])
    except:
        pass
    return pd.DataFrame()


def get_resumen_evaluacion(eval_id: str) -> pd.DataFrame:
    """Obtiene resumen de evaluación MAGERIT para todos los activos de una evaluación"""
    try:
        with get_connection() as conn:
            return pd.read_sql_query(
                '''SELECT 
                    rm.ID_Activo as id_activo, 
                    rm.Nombre_Activo as nombre_activo,
                    COALESCE(ia.tipo_activo, 'Otro') as tipo_activo,
                    rm.Impacto_D as impacto_d, 
                    rm.Impacto_I as impacto_i, 
                    rm.Impacto_C as impacto_c,
                    ROUND((rm.Impacto_D + rm.Impacto_I + rm.Impacto_C) / 3.0, 1) as impacto_global,
                    rm.Riesgo_Inherente as riesgo_inherente_global, 
                    rm.Nivel_Riesgo as nivel_riesgo_inherente,
                    rm.Riesgo_Residual as riesgo_residual_global,
                    rm.Nivel_Riesgo as nivel_riesgo_residual,
                    rm.Fecha_Evaluacion as fecha_evaluacion
                FROM RESULTADOS_MAGERIT rm
                LEFT JOIN INVENTARIO_ACTIVOS ia ON rm.ID_Activo = ia.ID_Activo AND rm.ID_Evaluacion = ia.ID_Evaluacion
                WHERE rm.ID_Evaluacion = ?
                ORDER BY rm.Riesgo_Inherente DESC''',
                conn,
                params=[eval_id]
            )
    except Exception as e:
        print(f"Error obteniendo resumen evaluación: {e}")
        return pd.DataFrame()

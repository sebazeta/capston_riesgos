"""
SERVICIO DE AUDITORÍA
======================
Registra todos los cambios en el sistema para trazabilidad completa.
Columnas de la tabla: id, Tabla_Afectada, ID_Registro, Tipo_Operacion, Valores_JSON, Usuario, Fecha_Hora
"""
import json
import datetime as dt
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from services.database_service import get_connection


@dataclass
class RegistroAuditoria:
    """Representa un registro de auditoría"""
    id: int = None
    tabla_afectada: str = ""
    id_registro: str = ""
    accion: str = ""  # Para mantener compatibilidad con la UI
    valores_anteriores: Dict = None
    valores_nuevos: Dict = None
    usuario: str = "sistema"
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.valores_anteriores is None:
            self.valores_anteriores = {}
        if self.valores_nuevos is None:
            self.valores_nuevos = {}


# Tipos de operaciones
ACCIONES = {
    "INSERT": "Creación",
    "UPDATE": "Modificación",
    "DELETE": "Eliminación",
    "IA_SUGERENCIA": "Sugerencia IA",
    "IA_VALIDACION": "Validación IA",
    "EVALUACION": "Evaluación MAGERIT",
    "CARGA_MASIVA": "Carga Masiva",
    "EXPORTACION": "Exportación"
}


def registrar_cambio(
    tabla: str,
    id_registro: str,
    accion: str,
    valores_anteriores: Dict = None,
    valores_nuevos: Dict = None,
    usuario: str = "sistema"
) -> bool:
    """
    Registra un cambio en la tabla de auditoría.
    """
    try:
        # Combinar valores en un solo JSON
        valores = {}
        if valores_anteriores:
            valores["antes"] = valores_anteriores
        if valores_nuevos:
            valores["despues"] = valores_nuevos
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO AUDITORIA_CAMBIOS (
                    Tabla_Afectada, ID_Registro, Tipo_Operacion,
                    Valores_JSON, Usuario, Fecha_Hora
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', [
                tabla,
                str(id_registro),
                accion,
                json.dumps(valores, ensure_ascii=False, default=str),
                usuario,
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
        return True
    except Exception as e:
        print(f"Error registrando auditoría: {e}")
        return False


def registrar_sugerencia_ia(
    tabla: str,
    id_registro: str,
    modelo_ia: str,
    prompt: str,
    respuesta: Dict,
    valores_aplicados: Dict = None
) -> bool:
    """Registra una sugerencia de IA con trazabilidad completa"""
    valores = {
        "modelo": modelo_ia,
        "prompt": prompt[:500],
        "respuesta": respuesta,
        "aplicado": valores_aplicados is not None,
        "valores_aplicados": valores_aplicados or {}
    }
    return registrar_cambio(
        tabla=tabla,
        id_registro=id_registro,
        accion="IA_SUGERENCIA",
        valores_nuevos=valores,
        usuario=f"IA:{modelo_ia}"
    )


def registrar_evaluacion(
    id_evaluacion: str,
    tipo: str,
    total_activos: int,
    resultados_resumen: Dict
) -> bool:
    """Registra una evaluación MAGERIT"""
    return registrar_cambio(
        tabla="EVALUACIONES",
        id_registro=id_evaluacion,
        accion="EVALUACION",
        valores_nuevos={
            "tipo": tipo,
            "total_activos": total_activos,
            "resumen": resultados_resumen
        }
    )


def registrar_carga_masiva(
    archivo: str,
    registros_cargados: int,
    errores: List[str] = None
) -> bool:
    """Registra una carga masiva de datos"""
    return registrar_cambio(
        tabla="CARGA_MASIVA",
        id_registro=archivo,
        accion="CARGA_MASIVA",
        valores_nuevos={
            "archivo": archivo,
            "registros": registros_cargados,
            "errores": errores or [],
            "exitoso": len(errores or []) == 0
        }
    )


def obtener_historial(
    tabla: str = None,
    id_registro: str = None,
    accion: str = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    limite: int = 100
) -> List[RegistroAuditoria]:
    """
    Obtiene el historial de auditoría con filtros opcionales.
    """
    historial = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT id, Tabla_Afectada, ID_Registro, Tipo_Operacion,
                       Valores_JSON, Usuario, Fecha_Hora
                FROM AUDITORIA_CAMBIOS
                WHERE 1=1
            '''
            params = []
            
            if tabla:
                query += " AND Tabla_Afectada = ?"
                params.append(tabla)
            
            if id_registro:
                query += " AND ID_Registro = ?"
                params.append(id_registro)
            
            if accion:
                query += " AND Tipo_Operacion = ?"
                params.append(accion)
            
            if fecha_desde:
                query += " AND Fecha_Hora >= ?"
                params.append(fecha_desde)
            
            if fecha_hasta:
                query += " AND Fecha_Hora <= ?"
                params.append(fecha_hasta)
            
            query += " ORDER BY Fecha_Hora DESC LIMIT ?"
            params.append(limite)
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                try:
                    valores = json.loads(row[4]) if row[4] else {}
                except:
                    valores = {}
                
                # Extraer valores anteriores y nuevos del JSON combinado
                valores_anteriores = valores.get("antes", {})
                valores_nuevos = valores.get("despues", valores)  # fallback al JSON completo
                
                historial.append(RegistroAuditoria(
                    id=row[0],
                    tabla_afectada=row[1],
                    id_registro=row[2],
                    accion=row[3],
                    valores_anteriores=valores_anteriores,
                    valores_nuevos=valores_nuevos,
                    usuario=row[5],
                    timestamp=row[6]
                ))
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
    
    return historial


def obtener_historial_activo(id_activo: str) -> List[RegistroAuditoria]:
    """Obtiene todo el historial de cambios de un activo específico"""
    return obtener_historial(id_registro=id_activo)


def obtener_estadisticas_auditoria(fecha_desde: str = None) -> Dict:
    """Obtiene estadísticas de auditoría"""
    estadisticas = {
        "total_registros": 0,
        "por_accion": {},
        "por_tabla": {},
        "por_usuario": {},
        "ultimos_7_dias": []
    }
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Total registros
            cursor.execute("SELECT COUNT(*) FROM AUDITORIA_CAMBIOS")
            estadisticas["total_registros"] = cursor.fetchone()[0]
            
            # Por operación
            cursor.execute('''
                SELECT Tipo_Operacion, COUNT(*) FROM AUDITORIA_CAMBIOS
                GROUP BY Tipo_Operacion ORDER BY COUNT(*) DESC
            ''')
            for row in cursor.fetchall():
                estadisticas["por_accion"][row[0] or "Sin tipo"] = row[1]
            
            # Por tabla
            cursor.execute('''
                SELECT Tabla_Afectada, COUNT(*) FROM AUDITORIA_CAMBIOS
                GROUP BY Tabla_Afectada ORDER BY COUNT(*) DESC
            ''')
            for row in cursor.fetchall():
                estadisticas["por_tabla"][row[0] or "Sin tabla"] = row[1]
            
            # Por usuario
            cursor.execute('''
                SELECT Usuario, COUNT(*) FROM AUDITORIA_CAMBIOS
                GROUP BY Usuario ORDER BY COUNT(*) DESC
            ''')
            for row in cursor.fetchall():
                estadisticas["por_usuario"][row[0] or "Sin usuario"] = row[1]
            
            # Últimos 7 días
            fecha_limite = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
            cursor.execute('''
                SELECT DATE(Fecha_Hora) as fecha, COUNT(*)
                FROM AUDITORIA_CAMBIOS
                WHERE Fecha_Hora >= ?
                GROUP BY DATE(Fecha_Hora)
                ORDER BY fecha DESC
            ''', [fecha_limite])
            for row in cursor.fetchall():
                estadisticas["ultimos_7_dias"].append({
                    "fecha": row[0],
                    "cantidad": row[1]
                })
            
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
    
    return estadisticas


def limpiar_auditoria_antigua(dias_retener: int = 90) -> int:
    """
    Limpia registros de auditoría más antiguos que X días.
    Retorna número de registros eliminados.
    """
    try:
        fecha_limite = (dt.datetime.now() - dt.timedelta(days=dias_retener)).strftime("%Y-%m-%d")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM AUDITORIA_CAMBIOS WHERE Fecha_Hora < ?
            ''', [fecha_limite])
            
            eliminados = cursor.rowcount
            
            # Registrar la limpieza
            registrar_cambio(
                tabla="AUDITORIA_CAMBIOS",
                id_registro="LIMPIEZA",
                accion="DELETE",
                valores_nuevos={
                    "dias_retencion": dias_retener,
                    "registros_eliminados": eliminados,
                    "fecha_limite": fecha_limite
                }
            )
            
            return eliminados
    except Exception as e:
        print(f"Error limpiando auditoría: {e}")
        return 0

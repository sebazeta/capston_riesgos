"""
SERVICIO DE VULNERABILIDADES
=============================
CRUD completo para gestión de vulnerabilidades por activo.
Vinculación con amenazas MAGERIT y sugerencia IA.
"""
import json
import datetime as dt
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from services.database_service import get_connection


# Mapeo de severidades
SEVERIDADES = {
    "Critica": {"valor": 4, "color": "#FF0000", "descripcion": "Impacto crítico en el negocio"},
    "Alta": {"valor": 3, "color": "#FF6600", "descripcion": "Impacto alto en operaciones"},
    "Media": {"valor": 2, "color": "#FFCC00", "descripcion": "Impacto moderado"},
    "Baja": {"valor": 1, "color": "#66CC00", "descripcion": "Impacto menor"},
    "Info": {"valor": 0, "color": "#0099CC", "descripcion": "Informativo"}
}


@dataclass
class Vulnerabilidad:
    """Vulnerabilidad identificada en un activo"""
    id: int = None
    id_evaluacion: str = ""
    id_activo: str = ""
    codigo: str = ""
    nombre: str = ""
    descripcion: str = ""
    severidad: str = "Media"
    cvss_score: float = None
    amenazas_asociadas: str = ""  # Separadas por coma
    controles_mitigantes: str = ""  # Separados por coma
    fuente: str = "Manual"
    fecha_registro: str = ""
    estado: str = "Identificada"
    
    def __post_init__(self):
        if not self.fecha_registro:
            self.fecha_registro = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# CRUD VULNERABILIDADES
# =============================================================================

def crear_vulnerabilidad(vuln: Vulnerabilidad) -> Optional[int]:
    """Crea una nueva vulnerabilidad. Retorna el ID o None si falla."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO VULNERABILIDADES_ACTIVO (
                    ID_Evaluacion, ID_Activo, Codigo_Vulnerabilidad, Nombre,
                    Descripcion, Severidad, CVSS_Score, Amenazas_Asociadas_JSON,
                    Controles_Mitigantes_JSON, Fuente, Fecha_Identificacion, Estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                vuln.id_evaluacion,
                vuln.id_activo,
                vuln.codigo,
                vuln.nombre,
                vuln.descripcion,
                vuln.severidad,
                vuln.cvss_score,
                vuln.amenazas_asociadas,
                vuln.controles_mitigantes,
                vuln.fuente,
                vuln.fecha_registro,
                vuln.estado
            ])
            return cursor.lastrowid
    except Exception as e:
        print(f"Error creando vulnerabilidad: {e}")
        return None


def obtener_vulnerabilidad(vuln_id: int) -> Optional[Vulnerabilidad]:
    """Obtiene una vulnerabilidad por su ID"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, ID_Evaluacion, ID_Activo, Codigo_Vulnerabilidad, Nombre,
                       Descripcion, Severidad, CVSS_Score, Amenazas_Asociadas_JSON,
                       Controles_Mitigantes_JSON, Fuente, Fecha_Identificacion, Estado
                FROM VULNERABILIDADES_ACTIVO
                WHERE id = ?
            ''', [vuln_id])
            
            row = cursor.fetchone()
            if row:
                return Vulnerabilidad(
                    id=row[0],
                    id_evaluacion=row[1],
                    id_activo=row[2],
                    codigo=row[3],
                    nombre=row[4],
                    descripcion=row[5] or "",
                    severidad=row[6] or "Media",
                    cvss_score=row[7],
                    amenazas_asociadas=row[8] or "",
                    controles_mitigantes=row[9] or "",
                    fuente=row[10] or "Manual",
                    fecha_registro=row[11] or "",
                    estado=row[12] or "Identificada"
                )
            return None
    except Exception as e:
        print(f"Error obteniendo vulnerabilidad: {e}")
        return None


def actualizar_vulnerabilidad(vuln: Vulnerabilidad) -> bool:
    """Actualiza una vulnerabilidad existente"""
    if not vuln.id:
        return False
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE VULNERABILIDADES_ACTIVO SET
                    Codigo_Vulnerabilidad = ?,
                    Nombre = ?,
                    Descripcion = ?,
                    Severidad = ?,
                    CVSS_Score = ?,
                    Amenazas_Asociadas_JSON = ?,
                    Controles_Mitigantes_JSON = ?,
                    Fuente = ?,
                    Estado = ?
                WHERE id = ?
            ''', [
                vuln.codigo,
                vuln.nombre,
                vuln.descripcion,
                vuln.severidad,
                vuln.cvss_score,
                vuln.amenazas_asociadas,
                vuln.controles_mitigantes,
                vuln.fuente,
                vuln.estado,
                vuln.id
            ])
        return True
    except Exception as e:
        print(f"Error actualizando vulnerabilidad: {e}")
        return False


def eliminar_vulnerabilidad(vuln_id: int) -> bool:
    """Elimina una vulnerabilidad por ID"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM VULNERABILIDADES_ACTIVO WHERE id = ?
            ''', [vuln_id])
        return True
    except Exception as e:
        print(f"Error eliminando vulnerabilidad: {e}")
        return False


def listar_vulnerabilidades_activo(id_activo: str) -> List[Vulnerabilidad]:
    """Lista todas las vulnerabilidades de un activo"""
    vulnerabilidades = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, ID_Evaluacion, ID_Activo, Codigo_Vulnerabilidad, Nombre,
                       Descripcion, Severidad, CVSS_Score, Amenazas_Asociadas_JSON,
                       Controles_Mitigantes_JSON, Fuente, Fecha_Identificacion, Estado
                FROM VULNERABILIDADES_ACTIVO
                WHERE ID_Activo = ?
                ORDER BY 
                    CASE Severidad 
                        WHEN 'Critica' THEN 1 
                        WHEN 'Alta' THEN 2 
                        WHEN 'Media' THEN 3 
                        WHEN 'Baja' THEN 4
                        ELSE 5 
                    END
            ''', [id_activo])
            
            for row in cursor.fetchall():
                vulnerabilidades.append(Vulnerabilidad(
                    id=row[0],
                    id_evaluacion=row[1],
                    id_activo=row[2],
                    codigo=row[3],
                    nombre=row[4],
                    descripcion=row[5] or "",
                    severidad=row[6] or "Media",
                    cvss_score=row[7],
                    amenazas_asociadas=row[8] or "",
                    controles_mitigantes=row[9] or "",
                    fuente=row[10] or "Manual",
                    fecha_registro=row[11] or "",
                    estado=row[12] or "Identificada"
                ))
    except Exception as e:
        print(f"Error listando vulnerabilidades: {e}")
    return vulnerabilidades


def listar_vulnerabilidades_evaluacion(id_evaluacion: str) -> List[Vulnerabilidad]:
    """Lista todas las vulnerabilidades de una evaluación"""
    vulnerabilidades = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, ID_Evaluacion, ID_Activo, Codigo_Vulnerabilidad, Nombre,
                       Descripcion, Severidad, CVSS_Score, Amenazas_Asociadas_JSON,
                       Controles_Mitigantes_JSON, Fuente, Fecha_Identificacion, Estado
                FROM VULNERABILIDADES_ACTIVO
                WHERE ID_Evaluacion = ?
                ORDER BY 
                    CASE Severidad 
                        WHEN 'Critica' THEN 1 
                        WHEN 'Alta' THEN 2 
                        WHEN 'Media' THEN 3 
                        WHEN 'Baja' THEN 4
                        ELSE 5 
                    END
            ''', [id_evaluacion])
            
            for row in cursor.fetchall():
                vulnerabilidades.append(Vulnerabilidad(
                    id=row[0],
                    id_evaluacion=row[1],
                    id_activo=row[2],
                    codigo=row[3],
                    nombre=row[4],
                    descripcion=row[5] or "",
                    severidad=row[6] or "Media",
                    cvss_score=row[7],
                    amenazas_asociadas=row[8] or "",
                    controles_mitigantes=row[9] or "",
                    fuente=row[10] or "Manual",
                    fecha_registro=row[11] or "",
                    estado=row[12] or "Identificada"
                ))
    except Exception as e:
        print(f"Error listando vulnerabilidades: {e}")
    return vulnerabilidades


# =============================================================================
# SUGERENCIAS IA - HEURÍSTICAS LOCALES
# =============================================================================

VULNERABILIDADES_POR_TIPO = {
    "Servidor": [
        {"codigo": "SVR-001", "nombre": "Parches de seguridad desactualizados", "severidad": "Alta",
         "descripcion": "El servidor no tiene los últimos parches de seguridad aplicados"},
        {"codigo": "SVR-002", "nombre": "Servicios innecesarios expuestos", "severidad": "Media",
         "descripcion": "Servicios que no son requeridos están habilitados y expuestos"},
        {"codigo": "SVR-003", "nombre": "Configuración por defecto", "severidad": "Alta",
         "descripcion": "Credenciales o configuraciones por defecto no modificadas"},
        {"codigo": "SVR-004", "nombre": "Falta de hardening", "severidad": "Media",
         "descripcion": "El servidor no ha sido endurecido según mejores prácticas"}
    ],
    "Base de Datos": [
        {"codigo": "DB-001", "nombre": "Inyección SQL posible", "severidad": "Critica",
         "descripcion": "La base de datos puede ser vulnerable a inyección SQL"},
        {"codigo": "DB-002", "nombre": "Datos sensibles sin cifrar", "severidad": "Alta",
         "descripcion": "Datos sensibles almacenados en texto plano"},
        {"codigo": "DB-003", "nombre": "Acceso excesivo a usuarios", "severidad": "Media",
         "descripcion": "Usuarios con más privilegios de los necesarios"},
        {"codigo": "DB-004", "nombre": "Backups sin cifrar", "severidad": "Alta",
         "descripcion": "Copias de respaldo no están cifradas"}
    ],
    "Aplicación": [
        {"codigo": "APP-001", "nombre": "Vulnerabilidades en dependencias", "severidad": "Alta",
         "descripcion": "Librerías de terceros con vulnerabilidades conocidas"},
        {"codigo": "APP-002", "nombre": "Autenticación débil", "severidad": "Alta",
         "descripcion": "Mecanismos de autenticación inseguros"},
        {"codigo": "APP-003", "nombre": "Falta de validación de entrada", "severidad": "Alta",
         "descripcion": "Entradas de usuario no validadas correctamente"},
        {"codigo": "APP-004", "nombre": "Exposición de información sensible", "severidad": "Media",
         "descripcion": "Logs o errores exponen información sensible"}
    ],
    "Red": [
        {"codigo": "NET-001", "nombre": "Segmentación de red insuficiente", "severidad": "Alta",
         "descripcion": "Red plana sin segmentación adecuada"},
        {"codigo": "NET-002", "nombre": "Protocolos inseguros en uso", "severidad": "Alta",
         "descripcion": "Uso de protocolos como Telnet, FTP sin cifrar"},
        {"codigo": "NET-003", "nombre": "Firewall mal configurado", "severidad": "Alta",
         "descripcion": "Reglas de firewall demasiado permisivas"},
        {"codigo": "NET-004", "nombre": "Falta de monitoreo de red", "severidad": "Media",
         "descripcion": "No hay monitoreo de tráfico de red"}
    ],
    "VM": [
        {"codigo": "VM-001", "nombre": "Snapshot sin cifrar", "severidad": "Media",
         "descripcion": "Snapshots de VMs sin protección"},
        {"codigo": "VM-002", "nombre": "Aislamiento inadecuado", "severidad": "Alta",
         "descripcion": "VMs no aisladas correctamente del host"},
        {"codigo": "VM-003", "nombre": "Recursos compartidos inseguros", "severidad": "Media",
         "descripcion": "Carpetas compartidas con permisos excesivos"}
    ]
}


def sugerir_vulnerabilidades_ia(tipo_activo: str) -> List[Dict]:
    """
    Sugiere vulnerabilidades comunes basadas en el tipo de activo.
    Usa heurísticas locales (no requiere conexión a IA externa).
    """
    sugerencias = []
    
    # Buscar coincidencias exactas o parciales
    for tipo_key, vulns in VULNERABILIDADES_POR_TIPO.items():
        if tipo_key.lower() in tipo_activo.lower() or tipo_activo.lower() in tipo_key.lower():
            sugerencias.extend(vulns)
    
    # Si no hay coincidencias, dar sugerencias genéricas
    if not sugerencias:
        sugerencias = [
            {"codigo": "GEN-001", "nombre": "Configuración insegura", "severidad": "Media",
             "descripcion": "Posible configuración insegura en el activo"},
            {"codigo": "GEN-002", "nombre": "Control de acceso débil", "severidad": "Alta",
             "descripcion": "Controles de acceso pueden ser insuficientes"},
            {"codigo": "GEN-003", "nombre": "Falta de logs de auditoría", "severidad": "Media",
             "descripcion": "Registro de auditoría insuficiente o inexistente"}
        ]
    
    return sugerencias


# =============================================================================
# ESTADÍSTICAS
# =============================================================================

def get_estadisticas_vulnerabilidades(id_evaluacion: str) -> Dict:
    """Obtiene estadísticas de vulnerabilidades para una evaluación"""
    stats = {
        "total": 0,
        "por_severidad": {},
        "por_estado": {},
        "activos_con_vulnerabilidades": 0
    }
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Total
            cursor.execute('''
                SELECT COUNT(*) FROM VULNERABILIDADES_ACTIVO
                WHERE ID_Evaluacion = ?
            ''', [id_evaluacion])
            stats["total"] = cursor.fetchone()[0]
            
            # Por severidad
            cursor.execute('''
                SELECT Severidad, COUNT(*) FROM VULNERABILIDADES_ACTIVO
                WHERE ID_Evaluacion = ?
                GROUP BY Severidad
            ''', [id_evaluacion])
            for row in cursor.fetchall():
                stats["por_severidad"][row[0] or "Sin clasificar"] = row[1]
            
            # Por estado
            cursor.execute('''
                SELECT Estado, COUNT(*) FROM VULNERABILIDADES_ACTIVO
                WHERE ID_Evaluacion = ?
                GROUP BY Estado
            ''', [id_evaluacion])
            for row in cursor.fetchall():
                stats["por_estado"][row[0] or "Sin estado"] = row[1]
            
            # Activos únicos con vulnerabilidades
            cursor.execute('''
                SELECT COUNT(DISTINCT ID_Activo) FROM VULNERABILIDADES_ACTIVO
                WHERE ID_Evaluacion = ?
            ''', [id_evaluacion])
            stats["activos_con_vulnerabilidades"] = cursor.fetchone()[0]
            
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
    
    return stats

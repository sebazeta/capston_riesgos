"""
Servicio de Carga Masiva de Activos - Proyecto TITA
Soporta JSON (principal) y Excel (compatibilidad)

Decisión arquitectónica:
- JSON: Validación estricta, sin macros, auditable, preparado para API
- Excel: Compatibilidad con usuarios que prefieren hojas de cálculo
"""
import json
import pandas as pd
import datetime as dt
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field, asdict
import hashlib
import re

from services.database_service import read_table, insert_rows
from services.activo_service import validar_duplicado, normalizar_nombre


# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

TIPOS_ACTIVO_VALIDOS = ["Servidor Físico", "Servidor Virtual"]

CAMPOS_REQUERIDOS = ["nombre_activo", "tipo_activo", "ubicacion", "propietario", "tipo_servicio"]

CAMPOS_OPCIONALES = ["app_critica", "descripcion", "id_host", "tipo_dependencia"]

TIPOS_DEPENDENCIA_VALIDOS = ["total", "parcial", "ninguna"]

CAMPOS_MAPEO_BD = {
    "nombre_activo": "Nombre_Activo",
    "tipo_activo": "Tipo_Activo",
    "ubicacion": "Ubicacion",
    "propietario": "Propietario",
    "tipo_servicio": "Tipo_Servicio",
    "app_critica": "App_Critica",
    "descripcion": "Descripcion",
    "id_host": "ID_Host",
    "tipo_dependencia": "Tipo_Dependencia"
}


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class ErrorValidacion:
    """Representa un error de validación"""
    fila: int
    campo: str
    mensaje: str
    valor_recibido: str = ""


@dataclass
class ResultadoCarga:
    """Resultado de una operación de carga masiva"""
    exito: bool
    total_procesados: int = 0
    total_insertados: int = 0
    total_duplicados: int = 0
    total_errores: int = 0
    errores: List[ErrorValidacion] = field(default_factory=list)
    duplicados: List[str] = field(default_factory=list)
    insertados: List[str] = field(default_factory=list)
    hash_archivo: str = ""
    timestamp: str = ""
    formato_origen: str = ""
    mensaje: str = ""


# ============================================================================
# VALIDACIÓN DE DATOS
# ============================================================================

def validar_tipo_activo(valor: str) -> Tuple[bool, str]:
    """Valida que el tipo de activo sea válido"""
    if not valor:
        return False, "El tipo de activo es obligatorio"
    
    # Normalizar para comparación flexible
    valor_norm = valor.strip()
    
    # Mapeo de variantes comunes
    mapeo_tipos = {
        "servidor físico": "Servidor Físico",
        "servidor fisico": "Servidor Físico",
        "físico": "Servidor Físico",
        "fisico": "Servidor Físico",
        "physical": "Servidor Físico",
        "servidor virtual": "Servidor Virtual",
        "virtual": "Servidor Virtual",
        "vm": "Servidor Virtual",
        "virtualizado": "Servidor Virtual"
    }
    
    valor_lower = valor_norm.lower()
    if valor_lower in mapeo_tipos:
        return True, mapeo_tipos[valor_lower]
    
    if valor_norm in TIPOS_ACTIVO_VALIDOS:
        return True, valor_norm
    
    return False, f"Tipo inválido: '{valor}'. Valores permitidos: {', '.join(TIPOS_ACTIVO_VALIDOS)}"


def validar_campo_texto(valor: str, campo: str, min_len: int = 1) -> Tuple[bool, str]:
    """Valida un campo de texto"""
    if not valor or not str(valor).strip():
        return False, f"El campo '{campo}' es obligatorio"
    
    valor_limpio = str(valor).strip()
    
    if len(valor_limpio) < min_len:
        return False, f"El campo '{campo}' debe tener al menos {min_len} caracteres"
    
    # Sanitizar caracteres peligrosos
    patron_peligroso = r'[<>"\';(){}]'
    if re.search(patron_peligroso, valor_limpio):
        return False, f"El campo '{campo}' contiene caracteres no permitidos"
    
    return True, valor_limpio


def validar_activo(activo: Dict, fila: int) -> Tuple[bool, Dict, List[ErrorValidacion]]:
    """
    Valida un activo individual
    
    Returns:
        (es_valido, activo_normalizado, lista_errores)
    """
    errores = []
    activo_normalizado = {}
    
    # Normalizar claves a minúsculas
    activo_lower = {k.lower().strip(): v for k, v in activo.items()}
    
    # Validar campos requeridos
    for campo in CAMPOS_REQUERIDOS:
        valor = activo_lower.get(campo, "")
        
        if campo == "tipo_activo":
            es_valido, resultado = validar_tipo_activo(valor)
            if not es_valido:
                errores.append(ErrorValidacion(
                    fila=fila,
                    campo=campo,
                    mensaje=resultado,
                    valor_recibido=str(valor)
                ))
            else:
                activo_normalizado[CAMPOS_MAPEO_BD[campo]] = resultado
        else:
            es_valido, resultado = validar_campo_texto(valor, campo)
            if not es_valido:
                errores.append(ErrorValidacion(
                    fila=fila,
                    campo=campo,
                    mensaje=resultado,
                    valor_recibido=str(valor)
                ))
            else:
                activo_normalizado[CAMPOS_MAPEO_BD[campo]] = resultado
    
    # Procesar campos opcionales
    for campo in CAMPOS_OPCIONALES:
        valor = activo_lower.get(campo, "")
        if valor:
            valor_str = str(valor).strip()
            # Validar tipo_dependencia si se proporciona
            if campo == "tipo_dependencia" and valor_str:
                if valor_str.lower() not in TIPOS_DEPENDENCIA_VALIDOS:
                    errores.append(ErrorValidacion(
                        fila=fila,
                        campo=campo,
                        mensaje=f"Tipo dependencia inválido. Valores permitidos: {', '.join(TIPOS_DEPENDENCIA_VALIDOS)}",
                        valor_recibido=valor_str
                    ))
                else:
                    activo_normalizado[CAMPOS_MAPEO_BD[campo]] = valor_str.lower()
            else:
                activo_normalizado[CAMPOS_MAPEO_BD[campo]] = valor_str
        else:
            # Valores por defecto para campos de concentración
            if campo == "tipo_dependencia":
                activo_normalizado[CAMPOS_MAPEO_BD[campo]] = "total"
            else:
                activo_normalizado[CAMPOS_MAPEO_BD[campo]] = ""
    
    return len(errores) == 0, activo_normalizado, errores


# ============================================================================
# PROCESAMIENTO JSON
# ============================================================================

def procesar_json(contenido: str, eval_id: str) -> ResultadoCarga:
    """
    Procesa un archivo JSON con activos
    
    Formato esperado:
    {
        "activos": [
            {
                "nombre_activo": "Servidor BD",
                "tipo_activo": "Servidor Virtual",
                "ubicacion": "DataCenter 1",
                "propietario": "TI",
                "tipo_servicio": "Base de Datos",
                "app_critica": "ERP",
                "descripcion": "Servidor principal"
            }
        ]
    }
    """
    resultado = ResultadoCarga(
        exito=False,
        timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        formato_origen="JSON",
        hash_archivo=hashlib.sha256(contenido.encode()).hexdigest()[:16]
    )
    
    # Parsear JSON
    try:
        datos = json.loads(contenido)
    except json.JSONDecodeError as e:
        resultado.mensaje = f"❌ Error de sintaxis JSON en línea {e.lineno}: {e.msg}"
        return resultado
    
    # Validar estructura
    if not isinstance(datos, dict):
        resultado.mensaje = "❌ El JSON debe ser un objeto con la propiedad 'activos'"
        return resultado
    
    activos_raw = datos.get("activos", [])
    
    if not activos_raw:
        resultado.mensaje = "❌ No se encontró la propiedad 'activos' o está vacía"
        return resultado
    
    if not isinstance(activos_raw, list):
        resultado.mensaje = "❌ La propiedad 'activos' debe ser un array"
        return resultado
    
    # Procesar activos
    return _procesar_lista_activos(activos_raw, eval_id, resultado)


# ============================================================================
# PROCESAMIENTO EXCEL
# ============================================================================

def procesar_excel(archivo_bytes: bytes, eval_id: str) -> ResultadoCarga:
    """
    Procesa un archivo Excel con activos
    
    Columnas esperadas (case-insensitive):
    - nombre_activo (obligatorio)
    - tipo_activo (obligatorio)
    - ubicacion (obligatorio)
    - propietario (obligatorio)
    - tipo_servicio (obligatorio)
    - app_critica (opcional)
    - descripcion (opcional)
    """
    import io
    
    resultado = ResultadoCarga(
        exito=False,
        timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        formato_origen="Excel",
        hash_archivo=hashlib.sha256(archivo_bytes).hexdigest()[:16]
    )
    
    try:
        # Leer Excel - solo valores, no fórmulas
        df = pd.read_excel(
            io.BytesIO(archivo_bytes),
            engine='openpyxl',
            dtype=str  # Forzar todo como texto para evitar problemas de tipos
        )
    except Exception as e:
        resultado.mensaje = f"❌ Error al leer archivo Excel: {str(e)}"
        return resultado
    
    if df.empty:
        resultado.mensaje = "❌ El archivo Excel está vacío"
        return resultado
    
    # Normalizar nombres de columnas
    df.columns = [str(col).lower().strip().replace(" ", "_") for col in df.columns]
    
    # Verificar columnas requeridas
    columnas_faltantes = [c for c in CAMPOS_REQUERIDOS if c not in df.columns]
    if columnas_faltantes:
        resultado.mensaje = f"❌ Columnas faltantes: {', '.join(columnas_faltantes)}"
        return resultado
    
    # Convertir a lista de diccionarios
    activos_raw = df.fillna("").to_dict('records')
    
    return _procesar_lista_activos(activos_raw, eval_id, resultado)


# ============================================================================
# PROCESAMIENTO COMÚN
# ============================================================================

def _procesar_lista_activos(activos_raw: List[Dict], eval_id: str, 
                           resultado: ResultadoCarga) -> ResultadoCarga:
    """Procesa una lista de activos validando y creando registros"""
    
    resultado.total_procesados = len(activos_raw)
    
    activos_a_insertar = []
    
    # Obtener siguiente número de activo
    activos_existentes = read_table("INVENTARIO_ACTIVOS")
    if activos_existentes.empty:
        siguiente_num = 1
    else:
        activos_eval = activos_existentes[
            activos_existentes["ID_Evaluacion"].astype(str) == str(eval_id)
        ]
        siguiente_num = len(activos_eval) + 1
    
    # Validar y procesar cada activo
    for idx, activo_raw in enumerate(activos_raw, start=1):
        es_valido, activo_norm, errores = validar_activo(activo_raw, idx)
        
        if not es_valido:
            resultado.errores.extend(errores)
            resultado.total_errores += 1
            continue
        
        # Verificar duplicados
        es_dup, msg_dup = validar_duplicado(
            eval_id,
            activo_norm["Nombre_Activo"],
            activo_norm["Ubicacion"],
            activo_norm["Tipo_Servicio"]
        )
        
        if es_dup:
            resultado.duplicados.append(f"Fila {idx}: {activo_norm['Nombre_Activo']}")
            resultado.total_duplicados += 1
            continue
        
        # También verificar duplicados internos (dentro del mismo archivo)
        clave_interna = f"{normalizar_nombre(activo_norm['Nombre_Activo'])}_{normalizar_nombre(activo_norm['Ubicacion'])}_{normalizar_nombre(activo_norm['Tipo_Servicio'])}"
        claves_ya_procesadas = [
            f"{normalizar_nombre(a['Nombre_Activo'])}_{normalizar_nombre(a['Ubicacion'])}_{normalizar_nombre(a['Tipo_Servicio'])}"
            for a in activos_a_insertar
        ]
        
        if clave_interna in claves_ya_procesadas:
            resultado.duplicados.append(f"Fila {idx}: {activo_norm['Nombre_Activo']} (duplicado interno)")
            resultado.total_duplicados += 1
            continue
        
        # Crear registro completo
        nuevo_id = f"ACT-{eval_id}-{str(siguiente_num).zfill(3)}"
        
        activo_completo = {
            "ID_Activo": nuevo_id,
            "ID_Evaluacion": eval_id,
            "Nombre_Activo": activo_norm["Nombre_Activo"],
            "Tipo_Activo": activo_norm["Tipo_Activo"],
            "Ubicacion": activo_norm["Ubicacion"],
            "Propietario": activo_norm["Propietario"],
            "Tipo_Servicio": activo_norm["Tipo_Servicio"],
            "App_Critica": activo_norm.get("App_Critica", ""),
            "Descripcion": activo_norm.get("Descripcion", ""),
            "ID_Host": activo_norm.get("ID_Host", ""),
            "Tipo_Dependencia": activo_norm.get("Tipo_Dependencia", "total"),
            "Estado": "Pendiente",
            "Fecha_Creacion": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        activos_a_insertar.append(activo_completo)
        resultado.insertados.append(f"{nuevo_id}: {activo_norm['Nombre_Activo']}")
        siguiente_num += 1
    
    # Insertar en base de datos
    if activos_a_insertar:
        try:
            insert_rows("INVENTARIO_ACTIVOS", activos_a_insertar)
            resultado.total_insertados = len(activos_a_insertar)
        except Exception as e:
            resultado.mensaje = f"❌ Error al insertar en base de datos: {str(e)}"
            resultado.exito = False
            return resultado
    
    # Generar mensaje de resumen
    resultado.exito = resultado.total_insertados > 0
    
    partes_mensaje = []
    if resultado.total_insertados > 0:
        partes_mensaje.append(f"✅ {resultado.total_insertados} activos insertados")
    if resultado.total_duplicados > 0:
        partes_mensaje.append(f"⚠️ {resultado.total_duplicados} duplicados omitidos")
    if resultado.total_errores > 0:
        partes_mensaje.append(f"❌ {resultado.total_errores} con errores")
    
    resultado.mensaje = " | ".join(partes_mensaje) if partes_mensaje else "Sin cambios"
    
    return resultado


# ============================================================================
# GENERACIÓN DE PLANTILLAS
# ============================================================================

def generar_plantilla_json() -> str:
    """Genera una plantilla JSON de ejemplo"""
    plantilla = {
        "activos": [
            {
                "nombre_activo": "Host VMware Principal",
                "tipo_activo": "Servidor Físico",
                "ubicacion": "DataCenter Principal",
                "propietario": "Infraestructura",
                "tipo_servicio": "Virtualización",
                "app_critica": "VMware ESXi",
                "descripcion": "Host físico que aloja máquinas virtuales de producción"
            },
            {
                "nombre_activo": "Servidor Base de Datos",
                "tipo_activo": "Servidor Virtual",
                "ubicacion": "DataCenter Principal",
                "propietario": "Departamento TI",
                "tipo_servicio": "Base de Datos",
                "app_critica": "ERP Corporativo",
                "descripcion": "Servidor de producción para base de datos Oracle",
                "id_host": "ACT-EVA-001-001",
                "tipo_dependencia": "total"
            },
            {
                "nombre_activo": "Servidor Web Producción",
                "tipo_activo": "Servidor Virtual",
                "ubicacion": "DataCenter Principal",
                "propietario": "Departamento TI",
                "tipo_servicio": "Aplicación Web",
                "app_critica": "Portal Corporativo",
                "descripcion": "Servidor web con Apache y aplicaciones PHP",
                "id_host": "ACT-EVA-001-001",
                "tipo_dependencia": "parcial"
            },
            {
                "nombre_activo": "Servidor Backup",
                "tipo_activo": "Servidor Físico",
                "ubicacion": "DataCenter Secundario",
                "propietario": "Infraestructura",
                "tipo_servicio": "Respaldos",
                "app_critica": "No",
                "descripcion": "Servidor de respaldos con Veeam"
            }
        ]
    }
    return json.dumps(plantilla, indent=2, ensure_ascii=False)


def generar_plantilla_excel() -> pd.DataFrame:
    """Genera un DataFrame plantilla para Excel"""
    datos = [
        {
            "nombre_activo": "Host VMware Principal",
            "tipo_activo": "Servidor Físico",
            "ubicacion": "DataCenter Principal",
            "propietario": "Infraestructura",
            "tipo_servicio": "Virtualización",
            "app_critica": "VMware ESXi",
            "descripcion": "Host físico que aloja máquinas virtuales",
            "id_host": "",
            "tipo_dependencia": ""
        },
        {
            "nombre_activo": "Servidor Base de Datos",
            "tipo_activo": "Servidor Virtual",
            "ubicacion": "DataCenter Principal",
            "propietario": "Departamento TI",
            "tipo_servicio": "Base de Datos",
            "app_critica": "ERP Corporativo",
            "descripcion": "Servidor de producción para base de datos Oracle",
            "id_host": "ACT-EVA-001-001",
            "tipo_dependencia": "total"
        },
        {
            "nombre_activo": "Servidor Web Producción",
            "tipo_activo": "Servidor Virtual",
            "ubicacion": "DataCenter Principal",
            "propietario": "Departamento TI",
            "tipo_servicio": "Aplicación Web",
            "app_critica": "Portal Corporativo",
            "descripcion": "Servidor web con Apache y aplicaciones PHP",
            "id_host": "ACT-EVA-001-001",
            "tipo_dependencia": "parcial"
        }
    ]
    return pd.DataFrame(datos)


def get_campos_info() -> Dict:
    """Retorna información sobre los campos para la UI"""
    return {
        "requeridos": [
            {"campo": "nombre_activo", "descripcion": "Nombre único del activo", "ejemplo": "Servidor BD Académica"},
            {"campo": "tipo_activo", "descripcion": "Tipo de servidor", "ejemplo": "Servidor Virtual o Servidor Físico"},
            {"campo": "ubicacion", "descripcion": "Ubicación física o lógica", "ejemplo": "DataCenter Principal"},
            {"campo": "propietario", "descripcion": "Área o persona responsable", "ejemplo": "Departamento TI"},
            {"campo": "tipo_servicio", "descripcion": "Función principal del servidor", "ejemplo": "Base de Datos, Web, Correo"}
        ],
        "opcionales": [
            {"campo": "app_critica", "descripcion": "Aplicación crítica que aloja", "ejemplo": "ERP, Banner, SAP"},
            {"campo": "descripcion", "descripcion": "Descripción adicional", "ejemplo": "Servidor principal de producción"},
            {"campo": "id_host", "descripcion": "ID del host físico (para VMs)", "ejemplo": "ACT-EVA-001-001"},
            {"campo": "tipo_dependencia", "descripcion": "Tipo de dependencia con el host", "ejemplo": "total, parcial, ninguna"}
        ],
        "tipos_validos": TIPOS_ACTIVO_VALIDOS,
        "tipos_dependencia_validos": TIPOS_DEPENDENCIA_VALIDOS
    }

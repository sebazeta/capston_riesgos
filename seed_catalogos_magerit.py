"""
SEED DE CATÁLOGOS MAGERIT v3 + ISO 27002:2022
==============================================
Catálogos oficiales completos:
- Criterios MAGERIT (D, I, C, Probabilidad, Niveles de riesgo)
- 52 Amenazas MAGERIT v3
- 93 Controles ISO/IEC 27002:2022

Uso: python seed_catalogos_magerit.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database_service import get_connection, init_database, read_table, DB_PATH
import sqlite3


def crear_tablas_catalogos():
    """Crea las tablas de catálogos en SQLite (elimina las existentes)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Eliminar tablas existentes para recrearlas con estructura correcta
        cursor.execute('DROP TABLE IF EXISTS CRITERIOS_DISPONIBILIDAD')
        cursor.execute('DROP TABLE IF EXISTS CRITERIOS_INTEGRIDAD')
        cursor.execute('DROP TABLE IF EXISTS CRITERIOS_CONFIDENCIALIDAD')
        cursor.execute('DROP TABLE IF EXISTS CRITERIOS_PROBABILIDAD')
        cursor.execute('DROP TABLE IF EXISTS CRITERIOS_NIVEL_RIESGO')
        cursor.execute('DROP TABLE IF EXISTS CATALOGO_AMENAZAS_MAGERIT')
        cursor.execute('DROP TABLE IF EXISTS CATALOGO_CONTROLES_ISO27002')
        
        # CRITERIOS_DISPONIBILIDAD
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CRITERIOS_DISPONIBILIDAD (
                valor INTEGER PRIMARY KEY,
                nivel TEXT NOT NULL,
                descripcion TEXT,
                ejemplo TEXT
            )
        ''')
        
        # CRITERIOS_INTEGRIDAD
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CRITERIOS_INTEGRIDAD (
                valor INTEGER PRIMARY KEY,
                nivel TEXT NOT NULL,
                descripcion TEXT,
                ejemplo TEXT
            )
        ''')
        
        # CRITERIOS_CONFIDENCIALIDAD
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CRITERIOS_CONFIDENCIALIDAD (
                valor INTEGER PRIMARY KEY,
                nivel TEXT NOT NULL,
                descripcion TEXT,
                ejemplo TEXT
            )
        ''')
        
        # CRITERIOS_PROBABILIDAD
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CRITERIOS_PROBABILIDAD (
                valor INTEGER PRIMARY KEY,
                nivel TEXT NOT NULL,
                descripcion TEXT,
                frecuencia TEXT
            )
        ''')
        
        # CRITERIOS_NIVEL_RIESGO
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CRITERIOS_NIVEL_RIESGO (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rango_min INTEGER,
                rango_max INTEGER,
                nivel TEXT NOT NULL,
                accion TEXT
            )
        ''')
        
        # CATALOGO_AMENAZAS_MAGERIT (52 amenazas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CATALOGO_AMENAZAS_MAGERIT (
                codigo TEXT PRIMARY KEY,
                tipo_amenaza TEXT NOT NULL,
                amenaza TEXT NOT NULL,
                descripcion TEXT,
                aplicable_a TEXT DEFAULT 'Todos los activos'
            )
        ''')
        
        # CATALOGO_CONTROLES_ISO27002 (93 controles)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CATALOGO_CONTROLES_ISO27002 (
                codigo TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descripcion TEXT
            )
        ''')
        
        # Crear índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_amenazas_tipo ON CATALOGO_AMENAZAS_MAGERIT(tipo_amenaza)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_controles_cat ON CATALOGO_CONTROLES_ISO27002(categoria)')


def get_criterios_disponibilidad():
    """Criterios MAGERIT para Disponibilidad"""
    return [
        (5, "Muy Alto", "Minutos de inactividad causan daño crítico", "Sistemas 24/7, transacciones en tiempo real"),
        (4, "Alto", "1 hora de inactividad causa daño grave", "Sistemas operacionales críticos"),
        (3, "Medio", "1 día de inactividad causa daño moderado", "Sistemas de gestión interna"),
        (2, "Bajo", "1 semana de inactividad causa daño menor", "Sistemas de soporte"),
        (1, "Muy Bajo", "Inactividad prolongada sin impacto crítico", "Sistemas de archivo"),
    ]


def get_criterios_integridad():
    """Criterios MAGERIT para Integridad"""
    return [
        (5, "Muy Alto", "Modificación irreparable, daño crítico", "Datos financieros, transacciones"),
        (4, "Alto", "Modificación difícil de reparar", "Bases de datos operacionales"),
        (3, "Medio", "Modificación reparable con esfuerzo", "Datos de configuración"),
        (2, "Bajo", "Modificación fácilmente reparable", "Documentos de trabajo"),
        (1, "Muy Bajo", "Modificación sin impacto relevante", "Datos temporales"),
    ]


def get_criterios_confidencialidad():
    """Criterios MAGERIT para Confidencialidad"""
    return [
        (5, "Muy Alto", "Información ultra secreta, divulgación crítica", "Secretos empresariales, datos personales sensibles"),
        (4, "Alto", "Información restringida, divulgación grave", "Información estratégica, contratos"),
        (3, "Medio", "Información interna, divulgación moderada", "Datos operacionales internos"),
        (2, "Bajo", "Información de uso general interno", "Políticas internas"),
        (1, "Muy Bajo", "Información pública", "Documentación publicada"),
    ]


def get_criterios_probabilidad():
    """Criterios MAGERIT para Probabilidad/Frecuencia"""
    return [
        (5, "Muy Alto", "Casi seguro que ocurra", "Diario / Semanal"),
        (4, "Alto", "Muy probable", "Mensual"),
        (3, "Medio", "Probable", "Trimestral / Semestral"),
        (2, "Bajo", "Poco probable", "Anual"),
        (1, "Muy Bajo", "Raro", "Cada varios años"),
    ]


def get_criterios_nivel_riesgo():
    """Niveles de riesgo según Probabilidad × Impacto"""
    return [
        (20, 25, "CRÍTICO", "Acción inmediata obligatoria"),
        (12, 19, "ALTO", "Acción prioritaria en corto plazo"),
        (6, 11, "MEDIO", "Planificar mitigación"),
        (3, 5, "BAJO", "Monitorear"),
        (1, 2, "MUY BAJO", "Aceptar"),
    ]


def get_amenazas_magerit():
    """52 Amenazas MAGERIT v3 oficiales"""
    return [
        # DESASTRES NATURALES (3)
        ("N.1", "Desastres Naturales", "Fuego", "Incendio natural o provocado", "Todos los activos"),
        ("N.2", "Desastres Naturales", "Daños por agua", "Inundación, humedad, filtración", "Todos los activos"),
        ("N.*", "Desastres Naturales", "Desastres naturales", "Terremoto, tornado, huracán, etc.", "Todos los activos"),
        
        # ORIGEN INDUSTRIAL (11)
        ("I.1", "Origen Industrial", "Fuego", "Incendio por causas industriales", "Todos los activos"),
        ("I.2", "Origen Industrial", "Daños por agua", "Daños por agua de origen industrial", "Todos los activos"),
        ("I.3", "Origen Industrial", "Contaminación mecánica", "Vibración, polvo, suciedad", "Todos los activos"),
        ("I.4", "Origen Industrial", "Contaminación electromagnética", "Radiación, pulsos electromagnéticos", "Todos los activos"),
        ("I.5", "Origen Industrial", "Avería de origen físico o lógico", "Fallo de equipamiento o software", "Todos los activos"),
        ("I.6", "Origen Industrial", "Corte del suministro eléctrico", "Interrupción del flujo eléctrico", "Todos los activos"),
        ("I.7", "Origen Industrial", "Condiciones inadecuadas de temperatura o humedad", "Ambiente no controlado", "Todos los activos"),
        ("I.8", "Origen Industrial", "Fallo de servicios de comunicaciones", "Interrupción de red/internet", "Todos los activos"),
        ("I.9", "Origen Industrial", "Interrupción de otros servicios", "Servicios esenciales no disponibles", "Todos los activos"),
        ("I.10", "Origen Industrial", "Degradación de los soportes de almacenamiento", "Deterioro de discos/medios", "Todos los activos"),
        ("I.11", "Origen Industrial", "Emanaciones electromagnéticas", "Fuga de información por radiación", "Todos los activos"),
        
        # ERRORES NO INTENCIONADOS (17)
        ("E.1", "Errores no Intencionados", "Errores de los usuarios", "Uso inadecuado, descuido", "Todos los activos"),
        ("E.2", "Errores no Intencionados", "Errores del administrador", "Configuración incorrecta", "Todos los activos"),
        ("E.3", "Errores no Intencionados", "Errores de monitorización (log)", "Fallos en auditoría/registro", "Todos los activos"),
        ("E.4", "Errores no Intencionados", "Errores de configuración", "Parámetros incorrectos", "Todos los activos"),
        ("E.7", "Errores no Intencionados", "Deficiencias en la organización", "Procesos inadecuados", "Todos los activos"),
        ("E.8", "Errores no Intencionados", "Difusión de software dañino", "Propagación de malware sin intención", "Todos los activos"),
        ("E.9", "Errores no Intencionados", "Errores de re-encaminamiento", "Rutas de red incorrectas", "Todos los activos"),
        ("E.10", "Errores no Intencionados", "Errores de secuencia", "Orden incorrecto de operaciones", "Todos los activos"),
        ("E.14", "Errores no Intencionados", "Escapes de información", "Fuga de datos no intencionada", "Todos los activos"),
        ("E.15", "Errores no Intencionados", "Alteración accidental de la información", "Modificación no intencional", "Todos los activos"),
        ("E.18", "Errores no Intencionados", "Destrucción de información", "Borrado accidental", "Todos los activos"),
        ("E.19", "Errores no Intencionados", "Fugas de información", "Divulgación no autorizada", "Todos los activos"),
        ("E.20", "Errores no Intencionados", "Vulnerabilidades de los programas", "Bugs, fallos de software", "Todos los activos"),
        ("E.21", "Errores no Intencionados", "Errores de mantenimiento / actualización", "Fallos en parches/updates", "Todos los activos"),
        ("E.23", "Errores no Intencionados", "Errores de uso", "Uso inadecuado de recursos", "Todos los activos"),
        ("E.25", "Errores no Intencionados", "Pérdida de equipos", "Extravío de hardware", "Todos los activos"),
        ("E.28", "Errores no Intencionados", "Indisponibilidad del personal", "Ausencia de personal clave", "Todos los activos"),
        
        # ATAQUES INTENCIONADOS (21)
        ("A.3", "Ataques Intencionados", "Manipulación de los registros de actividad (log)", "Alteración de auditoría", "Todos los activos"),
        ("A.4", "Ataques Intencionados", "Manipulación de la configuración", "Cambios maliciosos", "Todos los activos"),
        ("A.5", "Ataques Intencionados", "Suplantación de la identidad del usuario", "Robo de identidad", "Todos los activos"),
        ("A.6", "Ataques Intencionados", "Abuso de privilegios de acceso", "Uso indebido de permisos", "Todos los activos"),
        ("A.7", "Ataques Intencionados", "Uso no previsto", "Utilización fuera de especificación", "Todos los activos"),
        ("A.8", "Ataques Intencionados", "Difusión de software dañino", "Malware, virus, troyanos", "Todos los activos"),
        ("A.9", "Ataques Intencionados", "Re-encaminamiento de mensajes", "Redireccionamiento malicioso", "Todos los activos"),
        ("A.10", "Ataques Intencionados", "Alteración de secuencia", "Manipulación del orden", "Todos los activos"),
        ("A.11", "Ataques Intencionados", "Acceso no autorizado", "Intrusión, penetración", "Todos los activos"),
        ("A.15", "Ataques Intencionados", "Modificación deliberada de la información", "Alteración maliciosa", "Todos los activos"),
        ("A.18", "Ataques Intencionados", "Destrucción de información", "Borrado intencional", "Todos los activos"),
        ("A.19", "Ataques Intencionados", "Divulgación de información", "Fuga deliberada de datos", "Todos los activos"),
        ("A.22", "Ataques Intencionados", "Manipulación de programas", "Backdoors, lógica maliciosa", "Todos los activos"),
        ("A.23", "Ataques Intencionados", "Manipulación de los equipos", "Sabotaje físico", "Todos los activos"),
        ("A.24", "Ataques Intencionados", "Denegación de servicio", "DoS, DDoS", "Todos los activos"),
        ("A.25", "Ataques Intencionados", "Robo", "Sustracción de equipos/información", "Todos los activos"),
        ("A.26", "Ataques Intencionados", "Ataque destructivo", "Destrucción física/lógica", "Todos los activos"),
        ("A.27", "Ataques Intencionados", "Ocupación enemiga", "Toma de control hostil", "Todos los activos"),
        ("A.28", "Ataques Intencionados", "Indisponibilidad del personal", "Sabotaje de RRHH", "Todos los activos"),
        ("A.29", "Ataques Intencionados", "Extorsión", "Chantaje, ransomware", "Todos los activos"),
        ("A.30", "Ataques Intencionados", "Ingeniería social (piratería)", "Phishing, pretexting", "Todos los activos"),
    ]


def get_controles_iso27002():
    """93 Controles ISO/IEC 27002:2022 oficiales"""
    return [
        # ORGANIZACIONAL (5.1 - 5.37) = 37 controles
        ("5.1", "Políticas de seguridad de la información", "Organizacional", "Directrices de seguridad aprobadas y publicadas"),
        ("5.2", "Roles y responsabilidades de seguridad", "Organizacional", "Definición y asignación de responsabilidades"),
        ("5.3", "Segregación de funciones", "Organizacional", "Separación de tareas críticas"),
        ("5.4", "Responsabilidades de gestión", "Organizacional", "Obligaciones de los gestores"),
        ("5.5", "Contacto con autoridades", "Organizacional", "Relaciones con entidades gubernamentales"),
        ("5.6", "Contacto con grupos de interés especial", "Organizacional", "Foros de seguridad, comunidades"),
        ("5.7", "Inteligencia de amenazas", "Organizacional", "Información sobre amenazas actuales"),
        ("5.8", "Seguridad de la información en gestión de proyectos", "Organizacional", "Integración en proyectos"),
        ("5.9", "Inventario de información y otros activos asociados", "Organizacional", "Catálogo de activos"),
        ("5.10", "Uso aceptable de información y activos", "Organizacional", "Políticas de uso adecuado"),
        ("5.11", "Devolución de activos", "Organizacional", "Retorno al finalizar empleo/contrato"),
        ("5.12", "Clasificación de la información", "Organizacional", "Niveles de confidencialidad"),
        ("5.13", "Etiquetado de información", "Organizacional", "Marcado según clasificación"),
        ("5.14", "Transferencia de información", "Organizacional", "Intercambio seguro de datos"),
        ("5.15", "Control de acceso", "Organizacional", "Reglas de acceso a información"),
        ("5.16", "Gestión de identidad", "Organizacional", "Administración de identidades únicas"),
        ("5.17", "Información de autenticación", "Organizacional", "Gestión de credenciales"),
        ("5.18", "Derechos de acceso", "Organizacional", "Asignación y revisión de permisos"),
        ("5.19", "Seguridad de la información en relaciones con proveedores", "Organizacional", "Acuerdos con terceros"),
        ("5.20", "Abordar la seguridad de la información en acuerdos con proveedores", "Organizacional", "Cláusulas de seguridad"),
        ("5.21", "Gestión de seguridad de la información en la cadena de suministro TIC", "Organizacional", "Seguridad en supply chain"),
        ("5.22", "Monitoreo, revisión y gestión de cambios de servicios de proveedores", "Organizacional", "Supervisión de terceros"),
        ("5.23", "Seguridad de la información en servicios en la nube", "Organizacional", "Cloud security"),
        ("5.24", "Planificación y preparación de gestión de incidentes", "Organizacional", "Plan de respuesta"),
        ("5.25", "Evaluación y decisión sobre eventos de seguridad", "Organizacional", "Análisis de eventos"),
        ("5.26", "Respuesta a incidentes de seguridad", "Organizacional", "Procedimientos de respuesta"),
        ("5.27", "Aprender de incidentes de seguridad", "Organizacional", "Lecciones aprendidas"),
        ("5.28", "Recopilación de evidencia", "Organizacional", "Preservación de pruebas forenses"),
        ("5.29", "Seguridad de la información durante interrupciones", "Organizacional", "Continuidad del negocio"),
        ("5.30", "Preparación de TIC para continuidad del negocio", "Organizacional", "Planes de contingencia IT"),
        ("5.31", "Requisitos legales, estatutarios, regulatorios y contractuales", "Organizacional", "Cumplimiento legal"),
        ("5.32", "Derechos de propiedad intelectual", "Organizacional", "Protección de IP"),
        ("5.33", "Protección de registros", "Organizacional", "Salvaguarda de documentos"),
        ("5.34", "Privacidad y protección de PII", "Organizacional", "Datos personales, GDPR"),
        ("5.35", "Revisión independiente de seguridad de la información", "Organizacional", "Auditorías externas"),
        ("5.36", "Cumplimiento de políticas, reglas y estándares", "Organizacional", "Verificación de conformidad"),
        ("5.37", "Procedimientos operativos documentados", "Organizacional", "SOPs, documentación"),
        
        # PERSONAS (6.1 - 6.8) = 8 controles
        ("6.1", "Selección", "Personas", "Verificación de antecedentes en contratación"),
        ("6.2", "Términos y condiciones de empleo", "Personas", "Contratos con cláusulas de seguridad"),
        ("6.3", "Concienciación, educación y capacitación en seguridad", "Personas", "Programas de formación"),
        ("6.4", "Proceso disciplinario", "Personas", "Sanciones por incumplimiento"),
        ("6.5", "Responsabilidades tras la terminación o cambio de empleo", "Personas", "Fin de relación laboral"),
        ("6.6", "Acuerdos de confidencialidad o no divulgación", "Personas", "NDAs"),
        ("6.7", "Trabajo remoto", "Personas", "Teletrabajo seguro"),
        ("6.8", "Reportes de eventos de seguridad", "Personas", "Canales de reporte"),
        
        # FÍSICO (7.1 - 7.14) = 14 controles
        ("7.1", "Perímetros de seguridad física", "Físico", "Barreras, vallas, controles de acceso"),
        ("7.2", "Entrada física", "Físico", "Control de ingreso a instalaciones"),
        ("7.3", "Seguridad de oficinas, habitaciones e instalaciones", "Físico", "Protección de espacios"),
        ("7.4", "Monitoreo de seguridad física", "Físico", "CCTV, vigilancia"),
        ("7.5", "Protección contra amenazas físicas y ambientales", "Físico", "Desastres naturales, incendios"),
        ("7.6", "Trabajo en áreas seguras", "Físico", "Zonas restringidas"),
        ("7.7", "Escritorio y pantalla limpios", "Físico", "Clear desk policy"),
        ("7.8", "Ubicación y protección de equipos", "Físico", "Emplazamiento de hardware"),
        ("7.9", "Seguridad de activos fuera de las instalaciones", "Físico", "Equipos portátiles"),
        ("7.10", "Medios de almacenamiento", "Físico", "Gestión de discos, USBs"),
        ("7.11", "Servicios de apoyo", "Físico", "Energía, climatización"),
        ("7.12", "Seguridad del cableado", "Físico", "Protección de cables de red/energía"),
        ("7.13", "Mantenimiento de equipos", "Físico", "Servicio técnico autorizado"),
        ("7.14", "Disposición o reutilización segura de equipos", "Físico", "Borrado seguro, destrucción"),
        
        # TECNOLÓGICO (8.1 - 8.34) = 34 controles
        ("8.1", "Dispositivos de punto final de usuario", "Tecnológico", "Laptops, móviles, tablets"),
        ("8.2", "Derechos de acceso privilegiados", "Tecnológico", "Administradores, root, sudo"),
        ("8.3", "Restricción de acceso a la información", "Tecnológico", "Control basado en roles"),
        ("8.4", "Acceso al código fuente", "Tecnológico", "Protección de repositorios"),
        ("8.5", "Autenticación segura", "Tecnológico", "MFA, strong passwords"),
        ("8.6", "Gestión de capacidad", "Tecnológico", "Monitoreo de recursos"),
        ("8.7", "Protección contra malware", "Tecnológico", "Antivirus, antimalware"),
        ("8.8", "Gestión de vulnerabilidades técnicas", "Tecnológico", "Patching, actualizaciones"),
        ("8.9", "Gestión de configuración", "Tecnológico", "Baseline, hardening"),
        ("8.10", "Eliminación de información", "Tecnológico", "Borrado seguro de datos"),
        ("8.11", "Enmascaramiento de datos", "Tecnológico", "Data masking, anonimización"),
        ("8.12", "Prevención de fuga de datos", "Tecnológico", "DLP - Data Loss Prevention"),
        ("8.13", "Respaldo de información", "Tecnológico", "Backups, copias de seguridad"),
        ("8.14", "Redundancia de instalaciones de procesamiento de información", "Tecnológico", "HA, clustering"),
        ("8.15", "Registro (logging)", "Tecnológico", "Logs de eventos, auditoría"),
        ("8.16", "Actividades de monitoreo", "Tecnológico", "Supervisión de sistemas"),
        ("8.17", "Sincronización de reloj", "Tecnológico", "NTP, time sync"),
        ("8.18", "Uso de programas de utilidad privilegiados", "Tecnológico", "Herramientas administrativas"),
        ("8.19", "Instalación de software en sistemas operativos", "Tecnológico", "Control de instalaciones"),
        ("8.20", "Seguridad de redes", "Tecnológico", "Firewalls, IDS/IPS"),
        ("8.21", "Seguridad de servicios de red", "Tecnológico", "Protección de protocolos"),
        ("8.22", "Segregación de redes", "Tecnológico", "VLANs, segmentación"),
        ("8.23", "Filtrado web", "Tecnológico", "Proxy, content filtering"),
        ("8.24", "Uso de criptografía", "Tecnológico", "Cifrado, encriptación"),
        ("8.25", "Ciclo de vida de desarrollo seguro", "Tecnológico", "SDLC con seguridad"),
        ("8.26", "Requisitos de seguridad de aplicaciones", "Tecnológico", "Security by design"),
        ("8.27", "Arquitectura de sistemas seguros y principios de ingeniería", "Tecnológico", "Diseño seguro"),
        ("8.28", "Codificación segura", "Tecnológico", "Prácticas de desarrollo seguro"),
        ("8.29", "Pruebas de seguridad en desarrollo y aceptación", "Tecnológico", "Testing, pentesting"),
        ("8.30", "Desarrollo subcontratado", "Tecnológico", "Outsourcing de desarrollo"),
        ("8.31", "Separación de entornos de desarrollo, prueba y producción", "Tecnológico", "Dev, QA, Prod"),
        ("8.32", "Gestión de cambios", "Tecnológico", "Change management"),
        ("8.33", "Información de prueba", "Tecnológico", "Datos de testing seguros"),
        ("8.34", "Protección de sistemas de información durante pruebas de auditoría", "Tecnológico", "Auditorías no invasivas"),
    ]


def limpiar_catalogos():
    """Elimina datos existentes de catálogos para reinsertar"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM CRITERIOS_DISPONIBILIDAD')
        cursor.execute('DELETE FROM CRITERIOS_INTEGRIDAD')
        cursor.execute('DELETE FROM CRITERIOS_CONFIDENCIALIDAD')
        cursor.execute('DELETE FROM CRITERIOS_PROBABILIDAD')
        cursor.execute('DELETE FROM CRITERIOS_NIVEL_RIESGO')
        cursor.execute('DELETE FROM CATALOGO_AMENAZAS_MAGERIT')
        cursor.execute('DELETE FROM CATALOGO_CONTROLES_ISO27002')


def insertar_criterios():
    """Inserta todos los criterios MAGERIT"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Disponibilidad
        cursor.executemany(
            'INSERT INTO CRITERIOS_DISPONIBILIDAD (valor, nivel, descripcion, ejemplo) VALUES (?, ?, ?, ?)',
            get_criterios_disponibilidad()
        )
        
        # Integridad
        cursor.executemany(
            'INSERT INTO CRITERIOS_INTEGRIDAD (valor, nivel, descripcion, ejemplo) VALUES (?, ?, ?, ?)',
            get_criterios_integridad()
        )
        
        # Confidencialidad
        cursor.executemany(
            'INSERT INTO CRITERIOS_CONFIDENCIALIDAD (valor, nivel, descripcion, ejemplo) VALUES (?, ?, ?, ?)',
            get_criterios_confidencialidad()
        )
        
        # Probabilidad
        cursor.executemany(
            'INSERT INTO CRITERIOS_PROBABILIDAD (valor, nivel, descripcion, frecuencia) VALUES (?, ?, ?, ?)',
            get_criterios_probabilidad()
        )
        
        # Niveles de riesgo
        cursor.executemany(
            'INSERT INTO CRITERIOS_NIVEL_RIESGO (rango_min, rango_max, nivel, accion) VALUES (?, ?, ?, ?)',
            get_criterios_nivel_riesgo()
        )


def insertar_amenazas():
    """Inserta las 52 amenazas MAGERIT v3"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            'INSERT INTO CATALOGO_AMENAZAS_MAGERIT (codigo, tipo_amenaza, amenaza, descripcion, aplicable_a) VALUES (?, ?, ?, ?, ?)',
            get_amenazas_magerit()
        )


def insertar_controles():
    """Inserta los 93 controles ISO 27002:2022"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            'INSERT INTO CATALOGO_CONTROLES_ISO27002 (codigo, nombre, categoria, descripcion) VALUES (?, ?, ?, ?)',
            get_controles_iso27002()
        )


def validar_conteos():
    """Valida que los conteos sean correctos"""
    amenazas = read_table("CATALOGO_AMENAZAS_MAGERIT")
    controles = read_table("CATALOGO_CONTROLES_ISO27002")
    
    n_amenazas = len(amenazas)
    n_controles = len(controles)
    
    print(f"\n📊 VALIDACIÓN DE CONTEOS:")
    print(f"   Amenazas MAGERIT: {n_amenazas} (esperado: 52) {'✅' if n_amenazas == 52 else '❌'}")
    print(f"   Controles ISO 27002: {n_controles} (esperado: 93) {'✅' if n_controles == 93 else '❌'}")
    
    # Desglose por categoría
    if not amenazas.empty:
        print(f"\n   📋 Amenazas por tipo:")
        for tipo, count in amenazas['tipo_amenaza'].value_counts().items():
            print(f"      - {tipo}: {count}")
    
    if not controles.empty:
        print(f"\n   📋 Controles por categoría:")
        for cat, count in controles['categoria'].value_counts().items():
            print(f"      - {cat}: {count}")
    
    return n_amenazas == 52 and n_controles == 93


def main():
    """Ejecuta el seed completo de catálogos MAGERIT + ISO 27002"""
    print("=" * 70)
    print("🔐 SEED DE CATÁLOGOS MAGERIT v3 + ISO 27002:2022")
    print("=" * 70)
    
    # Asegurar que la BD existe
    if not os.path.exists(DB_PATH):
        print("⚠️ Base de datos no existe. Ejecuta primero init_sqlite.py")
        init_database()
    
    # Crear tablas de catálogos
    print("\n📦 Creando tablas de catálogos...")
    crear_tablas_catalogos()
    print("   ✅ Tablas creadas")
    
    # Limpiar datos existentes
    print("\n🧹 Limpiando catálogos existentes...")
    limpiar_catalogos()
    print("   ✅ Catálogos limpiados")
    
    # Insertar criterios
    print("\n📏 Insertando criterios MAGERIT...")
    insertar_criterios()
    print("   ✅ Criterios D/I/C/Probabilidad/Riesgo insertados")
    
    # Insertar amenazas
    print("\n⚠️ Insertando 52 amenazas MAGERIT v3...")
    insertar_amenazas()
    print("   ✅ Amenazas insertadas")
    
    # Insertar controles
    print("\n🛡️ Insertando 93 controles ISO 27002:2022...")
    insertar_controles()
    print("   ✅ Controles insertados")
    
    # Validar
    exito = validar_conteos()
    
    if exito:
        print("\n" + "=" * 70)
        print("🎉 CATÁLOGOS CARGADOS CORRECTAMENTE")
        print("=" * 70)
    else:
        print("\n❌ ERROR: Los conteos no coinciden con los esperados")
        sys.exit(1)


if __name__ == "__main__":
    main()

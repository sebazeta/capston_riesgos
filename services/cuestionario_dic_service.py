"""
SERVICIO DE CUESTIONARIO D/I/C + RTO/RPO/BIA
=============================================
Cuestionarios específicos por tipo de activo para calcular:
- D: Disponibilidad
- I: Integridad  
- C: Confidencialidad
- RTO: Recovery Time Objective (Tiempo máximo de recuperación)
- RPO: Recovery Point Objective (Pérdida máxima de datos tolerable)
- BIA: Business Impact Analysis (Impacto al negocio)

Cada tipo de activo tiene aproximadamente 21 preguntas:
- 4 preguntas de Disponibilidad
- 3 preguntas de Integridad
- 3 preguntas de Confidencialidad
- 4 preguntas de RTO
- 3 preguntas de RPO
- 4 preguntas de BIA
"""
import datetime as dt
import pandas as pd
from typing import Dict, List, Optional, Tuple
from services.database_service import read_table, insert_rows, get_connection


# ==================== BANCOS DE PREGUNTAS POR TIPO ====================

BANCO_PREGUNTAS_DIC = {
    # ========== SERVIDOR FÍSICO ==========
    "Servidor Físico": {
        "D": [
            {
                "id": "SF-D1",
                "pregunta": "¿Cuánto tiempo puede estar inoperativo este servidor sin afectar operaciones críticas?",
                "opciones": [
                    {"texto": "Menos de 1 hora - Operaciones se detienen inmediatamente", "valor": 3},
                    {"texto": "Entre 1 hora y 4 horas - Afecta operaciones importantes", "valor": 2},
                    {"texto": "Entre 4 horas y 1 día - Afecta operaciones menores", "valor": 1},
                    {"texto": "Más de 1 día - No afecta operaciones críticas", "valor": 0}
                ]
            },
            {
                "id": "SF-D2",
                "pregunta": "¿Cuántos usuarios/sistemas dependen directamente de este servidor?",
                "opciones": [
                    {"texto": "Más de 100 usuarios o sistemas críticos de toda la organización", "valor": 3},
                    {"texto": "Entre 50-100 usuarios o sistemas de un departamento clave", "valor": 2},
                    {"texto": "Entre 10-50 usuarios o sistemas de un área específica", "valor": 1},
                    {"texto": "Menos de 10 usuarios o sistemas no críticos", "valor": 0}
                ]
            },
            {
                "id": "SF-D3",
                "pregunta": "¿Existe redundancia o respaldo para este servidor físico?",
                "opciones": [
                    {"texto": "No existe redundancia - Es único punto de falla", "valor": 3},
                    {"texto": "Redundancia parcial - Respaldo manual con tiempo de recuperación largo", "valor": 2},
                    {"texto": "Redundancia activa - Failover automático en minutos", "valor": 1},
                    {"texto": "Alta disponibilidad - Cluster activo-activo sin interrupción", "valor": 0}
                ]
            },
            {
                "id": "SF-D4",
                "pregunta": "¿Cuál es el horario de operación crítico del servidor?",
                "opciones": [
                    {"texto": "24x7x365 - Operación continua sin ventanas de mantenimiento", "valor": 3},
                    {"texto": "24x7 con ventanas de mantenimiento programadas", "valor": 2},
                    {"texto": "Horario extendido (6am-10pm) días laborables", "valor": 1},
                    {"texto": "Horario de oficina (8am-6pm) días laborables", "valor": 0}
                ]
            }
        ],
        "I": [
            {
                "id": "SF-I1",
                "pregunta": "¿Qué tan crítica es la integridad de los datos que procesa este servidor?",
                "opciones": [
                    {"texto": "Datos financieros/legales - Modificación causa pérdidas irreparables", "valor": 3},
                    {"texto": "Datos operacionales - Modificación causa problemas significativos", "valor": 2},
                    {"texto": "Datos de soporte - Modificación causa inconvenientes menores", "valor": 1},
                    {"texto": "Datos de prueba/desarrollo - Modificación no tiene impacto", "valor": 0}
                ]
            },
            {
                "id": "SF-I2",
                "pregunta": "¿Existen controles de integridad implementados (checksums, logs, auditoría)?",
                "opciones": [
                    {"texto": "Sin controles - No hay forma de detectar modificaciones", "valor": 3},
                    {"texto": "Controles básicos - Solo logs manuales esporádicos", "valor": 2},
                    {"texto": "Controles moderados - Logs automáticos y checksums periódicos", "valor": 1},
                    {"texto": "Controles avanzados - Monitoreo en tiempo real con alertas", "valor": 0}
                ]
            },
            {
                "id": "SF-I3",
                "pregunta": "¿Cuánto tiempo tomaría detectar y reparar una alteración no autorizada?",
                "opciones": [
                    {"texto": "Días o semanas - No hay mecanismo de detección", "valor": 3},
                    {"texto": "Horas - Detección manual durante revisiones", "valor": 2},
                    {"texto": "Minutos - Alertas automáticas con procedimiento de respuesta", "valor": 1},
                    {"texto": "Inmediato - Prevención activa que bloquea alteraciones", "valor": 0}
                ]
            }
        ],
        "C": [
            {
                "id": "SF-C1",
                "pregunta": "¿Qué tipo de información maneja este servidor?",
                "opciones": [
                    {"texto": "Información altamente confidencial (datos personales sensibles, financieros, secretos)", "valor": 3},
                    {"texto": "Información confidencial de uso interno restringido", "valor": 2},
                    {"texto": "Información interna de uso general por empleados", "valor": 1},
                    {"texto": "Información pública o sin restricciones", "valor": 0}
                ]
            },
            {
                "id": "SF-C2",
                "pregunta": "¿Quién tiene acceso físico y lógico a este servidor?",
                "opciones": [
                    {"texto": "Solo 1-2 administradores con acceso muy restringido y MFA", "valor": 0},
                    {"texto": "Equipo de TI (5-10 personas) con roles definidos", "valor": 1},
                    {"texto": "Múltiples departamentos con acceso controlado", "valor": 2},
                    {"texto": "Acceso amplio sin restricciones significativas", "valor": 3}
                ]
            },
            {
                "id": "SF-C3",
                "pregunta": "¿Cuál sería el impacto de una filtración de datos de este servidor?",
                "opciones": [
                    {"texto": "Catastrófico - Multas regulatorias, demandas, daño reputacional severo", "valor": 3},
                    {"texto": "Significativo - Pérdida de clientes, investigaciones internas", "valor": 2},
                    {"texto": "Menor - Inconvenientes internos, correcciones necesarias", "valor": 1},
                    {"texto": "Mínimo - Sin impacto significativo", "valor": 0}
                ]
            }
        ],
        "RTO": [
            {
                "id": "SF-RTO1",
                "pregunta": "¿Cuál es el tiempo máximo aceptable para restaurar este servidor después de una falla total?",
                "opciones": [
                    {"texto": "Menos de 1 hora - Crítico para operaciones continuas", "valor": 3},
                    {"texto": "Entre 1 y 4 horas - Importante para el negocio", "valor": 2},
                    {"texto": "Entre 4 y 24 horas - Puede esperar hasta el siguiente día", "valor": 1},
                    {"texto": "Más de 24 horas - No es urgente", "valor": 0}
                ]
            },
            {
                "id": "SF-RTO2",
                "pregunta": "¿Existen procedimientos documentados de recuperación para este servidor?",
                "opciones": [
                    {"texto": "No hay documentación - Dependemos del conocimiento de personas específicas", "valor": 3},
                    {"texto": "Documentación básica - Pasos generales sin detalles", "valor": 2},
                    {"texto": "Documentación completa - Runbooks detallados y actualizados", "valor": 1},
                    {"texto": "Automatizado - Scripts de recuperación probados regularmente", "valor": 0}
                ]
            },
            {
                "id": "SF-RTO3",
                "pregunta": "¿Con qué frecuencia se prueban los procedimientos de recuperación?",
                "opciones": [
                    {"texto": "Nunca se han probado", "valor": 3},
                    {"texto": "Se probaron hace más de 1 año", "valor": 2},
                    {"texto": "Se prueban anualmente", "valor": 1},
                    {"texto": "Se prueban trimestralmente o con mayor frecuencia", "valor": 0}
                ]
            },
            {
                "id": "SF-RTO4",
                "pregunta": "¿Qué recursos se requieren para la recuperación (personal, hardware, licencias)?",
                "opciones": [
                    {"texto": "Recursos especializados escasos - Difícil conseguir en emergencia", "valor": 3},
                    {"texto": "Recursos disponibles pero requieren coordinación", "valor": 2},
                    {"texto": "Recursos identificados y preposicionados", "valor": 1},
                    {"texto": "Recursos automáticos (cloud, DR site activo)", "valor": 0}
                ]
            }
        ],
        "RPO": [
            {
                "id": "SF-RPO1",
                "pregunta": "¿Cuánta pérdida de datos es aceptable en caso de falla?",
                "opciones": [
                    {"texto": "Cero - No se puede perder ninguna transacción", "valor": 3},
                    {"texto": "Hasta 1 hora de datos", "valor": 2},
                    {"texto": "Hasta 4 horas de datos", "valor": 1},
                    {"texto": "Hasta 24 horas de datos", "valor": 0}
                ]
            },
            {
                "id": "SF-RPO2",
                "pregunta": "¿Cuál es la frecuencia actual de respaldos de este servidor?",
                "opciones": [
                    {"texto": "No hay respaldos configurados", "valor": 3},
                    {"texto": "Respaldo diario", "valor": 2},
                    {"texto": "Respaldo cada hora", "valor": 1},
                    {"texto": "Replicación continua o en tiempo real", "valor": 0}
                ]
            },
            {
                "id": "SF-RPO3",
                "pregunta": "¿Los respaldos se almacenan en ubicación separada (offsite/cloud)?",
                "opciones": [
                    {"texto": "No - Solo respaldos locales en el mismo sitio", "valor": 3},
                    {"texto": "Parcial - Algunos respaldos van a otro sitio", "valor": 2},
                    {"texto": "Sí - Respaldos completos en sitio remoto", "valor": 1},
                    {"texto": "Sí - Múltiples copias en diferentes geografías", "valor": 0}
                ]
            }
        ],
        "BIA": [
            {
                "id": "SF-BIA1",
                "pregunta": "¿Qué procesos de negocio dependen directamente de este servidor?",
                "opciones": [
                    {"texto": "Procesos core del negocio (ventas, producción, facturación)", "valor": 3},
                    {"texto": "Procesos importantes (logística, RRHH, finanzas)", "valor": 2},
                    {"texto": "Procesos de soporte (email, intranet)", "valor": 1},
                    {"texto": "Procesos no críticos (desarrollo, pruebas)", "valor": 0}
                ]
            },
            {
                "id": "SF-BIA2",
                "pregunta": "¿Cuál es el impacto financiero estimado por hora de inactividad?",
                "opciones": [
                    {"texto": "Más de $10,000/hora - Pérdidas directas significativas", "valor": 3},
                    {"texto": "Entre $1,000 y $10,000/hora - Pérdidas moderadas", "valor": 2},
                    {"texto": "Entre $100 y $1,000/hora - Pérdidas menores", "valor": 1},
                    {"texto": "Menos de $100/hora - Impacto mínimo", "valor": 0}
                ]
            },
            {
                "id": "SF-BIA3",
                "pregunta": "¿Existen obligaciones contractuales o SLAs que dependan de este servidor?",
                "opciones": [
                    {"texto": "SLAs críticos con penalidades financieras significativas", "valor": 3},
                    {"texto": "SLAs importantes con clientes clave", "valor": 2},
                    {"texto": "Compromisos internos de nivel de servicio", "valor": 1},
                    {"texto": "Sin SLAs o compromisos formales", "valor": 0}
                ]
            },
            {
                "id": "SF-BIA4",
                "pregunta": "¿Cuál es el impacto reputacional si este servidor falla?",
                "opciones": [
                    {"texto": "Alto - Afecta directamente a clientes externos, medios podrían reportar", "valor": 3},
                    {"texto": "Medio - Afecta a partners o clientes importantes", "valor": 2},
                    {"texto": "Bajo - Solo afecta operaciones internas", "valor": 1},
                    {"texto": "Mínimo - Sin visibilidad externa", "valor": 0}
                ]
            }
        ]
    },
    
    # ========== SERVIDOR VIRTUAL ==========
    "Servidor Virtual": {
        "D": [
            {"id": "SV-D1", "pregunta": "¿Cuánto tiempo puede estar inoperativa esta VM sin afectar operaciones críticas?",
             "opciones": [{"texto": "Menos de 1 hora - Operaciones se detienen inmediatamente", "valor": 3},
                         {"texto": "Entre 1-4 horas - Afecta operaciones importantes", "valor": 2},
                         {"texto": "Entre 4 horas y 1 día - Afecta operaciones menores", "valor": 1},
                         {"texto": "Más de 1 día - No afecta operaciones críticas", "valor": 0}]},
            {"id": "SV-D2", "pregunta": "¿Cuántos usuarios/sistemas dependen directamente de esta VM?",
             "opciones": [{"texto": "Más de 100 usuarios o sistemas críticos", "valor": 3},
                         {"texto": "Entre 50-100 usuarios o sistemas importantes", "valor": 2},
                         {"texto": "Entre 10-50 usuarios o sistemas", "valor": 1},
                         {"texto": "Menos de 10 usuarios o sistemas no críticos", "valor": 0}]},
            {"id": "SV-D3", "pregunta": "¿La VM tiene configuración de alta disponibilidad (HA/vMotion)?",
             "opciones": [{"texto": "No - Sin HA, falla del host = caída de la VM", "valor": 3},
                         {"texto": "HA básico - Reinicio automático en otro host (minutos)", "valor": 2},
                         {"texto": "HA con DRS - Balanceo y migración automática", "valor": 1},
                         {"texto": "Fault Tolerance - Cero interrupción ante falla de host", "valor": 0}]},
            {"id": "SV-D4", "pregunta": "¿Cuál es el horario de operación crítico de esta VM?",
             "opciones": [{"texto": "24x7x365 - Operación continua sin ventanas", "valor": 3},
                         {"texto": "24x7 con ventanas de mantenimiento", "valor": 2},
                         {"texto": "Horario extendido (6am-10pm)", "valor": 1},
                         {"texto": "Horario de oficina (8am-6pm)", "valor": 0}]}
        ],
        "I": [
            {"id": "SV-I1", "pregunta": "¿Qué tan crítica es la integridad de los datos en esta VM?",
             "opciones": [{"texto": "Datos financieros/legales - Modificación causa pérdidas irreparables", "valor": 3},
                         {"texto": "Datos operacionales - Modificación causa problemas significativos", "valor": 2},
                         {"texto": "Datos de soporte - Modificación causa inconvenientes menores", "valor": 1},
                         {"texto": "Datos de prueba/desarrollo - Sin impacto", "valor": 0}]},
            {"id": "SV-I2", "pregunta": "¿La VM tiene snapshots y control de cambios implementado?",
             "opciones": [{"texto": "Sin snapshots ni control de cambios", "valor": 3},
                         {"texto": "Snapshots manuales ocasionales", "valor": 2},
                         {"texto": "Snapshots automáticos antes de cambios", "valor": 1},
                         {"texto": "Gestión completa con versionamiento y rollback", "valor": 0}]},
            {"id": "SV-I3", "pregunta": "¿Existen controles de acceso y auditoría en el hipervisor?",
             "opciones": [{"texto": "Acceso compartido sin auditoría", "valor": 3},
                         {"texto": "Acceso con roles básicos", "valor": 2},
                         {"texto": "RBAC completo con logs", "valor": 1},
                         {"texto": "RBAC + MFA + SIEM integrado", "valor": 0}]}
        ],
        "C": [
            {"id": "SV-C1", "pregunta": "¿Qué tipo de información maneja esta VM?",
             "opciones": [{"texto": "Información altamente confidencial (PII, financiera)", "valor": 3},
                         {"texto": "Información confidencial de uso interno restringido", "valor": 2},
                         {"texto": "Información interna de uso general", "valor": 1},
                         {"texto": "Información pública o sin restricciones", "valor": 0}]},
            {"id": "SV-C2", "pregunta": "¿Los discos virtuales están encriptados?",
             "opciones": [{"texto": "No - Sin encriptación de discos", "valor": 3},
                         {"texto": "Parcial - Solo algunos discos críticos", "valor": 2},
                         {"texto": "Sí - Encriptación a nivel de storage", "valor": 1},
                         {"texto": "Sí - Encriptación a nivel de VM + gestión de llaves", "valor": 0}]},
            {"id": "SV-C3", "pregunta": "¿La red virtual de esta VM está segmentada/aislada?",
             "opciones": [{"texto": "Red plana - Sin segmentación", "valor": 3},
                         {"texto": "VLANs básicas", "valor": 2},
                         {"texto": "Microsegmentación (NSX/similar)", "valor": 1},
                         {"texto": "Zero Trust con inspección de tráfico E-W", "valor": 0}]}
        ],
        "RTO": [
            {"id": "SV-RTO1", "pregunta": "¿Cuál es el tiempo máximo aceptable para restaurar esta VM?",
             "opciones": [{"texto": "Menos de 1 hora", "valor": 3}, {"texto": "Entre 1 y 4 horas", "valor": 2},
                         {"texto": "Entre 4 y 24 horas", "valor": 1}, {"texto": "Más de 24 horas", "valor": 0}]},
            {"id": "SV-RTO2", "pregunta": "¿Existe una réplica de esta VM en otro sitio (DR)?",
             "opciones": [{"texto": "No hay réplica en DR", "valor": 3},
                         {"texto": "Réplica manual periódica", "valor": 2},
                         {"texto": "Réplica automatizada (Zerto, SRM, ASR)", "valor": 1},
                         {"texto": "Active-Active en múltiples sitios", "valor": 0}]},
            {"id": "SV-RTO3", "pregunta": "¿La VM puede ser reconstruida desde código (IaC)?",
             "opciones": [{"texto": "No - Configuración manual única", "valor": 3},
                         {"texto": "Documentación de instalación existe", "valor": 2},
                         {"texto": "Templates/Golden images disponibles", "valor": 1},
                         {"texto": "100% Infrastructure as Code (Terraform, Ansible)", "valor": 0}]},
            {"id": "SV-RTO4", "pregunta": "¿Con qué frecuencia se prueban los procedimientos de recovery?",
             "opciones": [{"texto": "Nunca se han probado", "valor": 3},
                         {"texto": "Se probaron hace más de 1 año", "valor": 2},
                         {"texto": "Se prueban anualmente", "valor": 1},
                         {"texto": "Se prueban trimestralmente o más frecuente", "valor": 0}]}
        ],
        "RPO": [
            {"id": "SV-RPO1", "pregunta": "¿Cuánta pérdida de datos es aceptable para esta VM?",
             "opciones": [{"texto": "Cero - Replicación síncrona requerida", "valor": 3},
                         {"texto": "Hasta 1 hora de datos", "valor": 2},
                         {"texto": "Hasta 4 horas de datos", "valor": 1},
                         {"texto": "Hasta 24 horas de datos", "valor": 0}]},
            {"id": "SV-RPO2", "pregunta": "¿Cuál es la frecuencia de respaldos/snapshots de esta VM?",
             "opciones": [{"texto": "Sin respaldos automáticos", "valor": 3},
                         {"texto": "Respaldo diario", "valor": 2},
                         {"texto": "Respaldo cada hora", "valor": 1},
                         {"texto": "Replicación continua (CDP)", "valor": 0}]},
            {"id": "SV-RPO3", "pregunta": "¿Los respaldos de esta VM se verifican regularmente?",
             "opciones": [{"texto": "Nunca se ha verificado una restauración", "valor": 3},
                         {"texto": "Verificación anual", "valor": 2},
                         {"texto": "Verificación trimestral", "valor": 1},
                         {"texto": "Verificación automática continua", "valor": 0}]}
        ],
        "BIA": [
            {"id": "SV-BIA1", "pregunta": "¿Qué procesos de negocio dependen de esta VM?",
             "opciones": [{"texto": "Procesos core del negocio", "valor": 3},
                         {"texto": "Procesos importantes", "valor": 2},
                         {"texto": "Procesos de soporte", "valor": 1},
                         {"texto": "Procesos no críticos", "valor": 0}]},
            {"id": "SV-BIA2", "pregunta": "¿Cuál es el impacto financiero estimado por hora de inactividad?",
             "opciones": [{"texto": "Más de $10,000/hora", "valor": 3},
                         {"texto": "Entre $1,000 y $10,000/hora", "valor": 2},
                         {"texto": "Entre $100 y $1,000/hora", "valor": 1},
                         {"texto": "Menos de $100/hora", "valor": 0}]},
            {"id": "SV-BIA3", "pregunta": "¿Esta VM soporta servicios externos a clientes?",
             "opciones": [{"texto": "Sí - Servicios críticos para clientes externos", "valor": 3},
                         {"texto": "Sí - Servicios secundarios para clientes", "valor": 2},
                         {"texto": "No - Solo servicios internos importantes", "valor": 1},
                         {"texto": "No - Solo servicios internos no críticos", "valor": 0}]},
            {"id": "SV-BIA4", "pregunta": "¿Cuál es el impacto regulatorio si esta VM falla?",
             "opciones": [{"texto": "Alto - Incumplimiento regulatorio con multas", "valor": 3},
                         {"texto": "Medio - Posibles observaciones en auditorías", "valor": 2},
                         {"texto": "Bajo - Afecta métricas internas", "valor": 1},
                         {"texto": "Ninguno - Sin impacto regulatorio", "valor": 0}]}
        ]
    },
    
    # ========== BASE DE DATOS ==========
    "Base de Datos": {
        "D": [
            {"id": "BD-D1", "pregunta": "¿Cuánto tiempo puede estar inoperativa esta base de datos sin afectar operaciones?",
             "opciones": [{"texto": "Menos de 15 minutos - Sistema transaccional crítico", "valor": 3},
                         {"texto": "Entre 15 min y 1 hora - Base de datos operacional", "valor": 2},
                         {"texto": "Entre 1 y 4 horas - Base de datos de reporting", "valor": 1},
                         {"texto": "Más de 4 horas - Base de datos de desarrollo/archivo", "valor": 0}]},
            {"id": "BD-D2", "pregunta": "¿Cuántas aplicaciones/sistemas consultan esta base de datos?",
             "opciones": [{"texto": "Más de 10 aplicaciones críticas", "valor": 3},
                         {"texto": "Entre 5-10 aplicaciones importantes", "valor": 2},
                         {"texto": "Entre 1-5 aplicaciones", "valor": 1},
                         {"texto": "Solo 1 aplicación no crítica", "valor": 0}]},
            {"id": "BD-D3", "pregunta": "¿La base de datos tiene configuración de alta disponibilidad?",
             "opciones": [{"texto": "Sin HA - Instancia única", "valor": 3},
                         {"texto": "Log shipping o respaldo en standby manual", "valor": 2},
                         {"texto": "Always On / RAC / Replica con failover automático", "valor": 1},
                         {"texto": "Multi-región con failover automático", "valor": 0}]},
            {"id": "BD-D4", "pregunta": "¿Cuál es el volumen de transacciones por segundo (TPS)?",
             "opciones": [{"texto": "Más de 1000 TPS - Alta carga transaccional", "valor": 3},
                         {"texto": "Entre 100-1000 TPS - Carga moderada-alta", "valor": 2},
                         {"texto": "Entre 10-100 TPS - Carga moderada", "valor": 1},
                         {"texto": "Menos de 10 TPS - Baja carga", "valor": 0}]}
        ],
        "I": [
            {"id": "BD-I1", "pregunta": "¿Qué tipo de datos almacena esta base de datos?",
             "opciones": [{"texto": "Datos financieros, contables o transaccionales regulados", "valor": 3},
                         {"texto": "Datos de clientes y operacionales críticos", "valor": 2},
                         {"texto": "Datos de soporte y configuración", "valor": 1},
                         {"texto": "Datos de prueba, logs o temporales", "valor": 0}]},
            {"id": "BD-I2", "pregunta": "¿Existen constraints, triggers y validaciones de integridad referencial?",
             "opciones": [{"texto": "Sin constraints - Integridad manejada solo por aplicación", "valor": 3},
                         {"texto": "Constraints básicos (PK, FK principales)", "valor": 2},
                         {"texto": "Modelo completo con validaciones", "valor": 1},
                         {"texto": "Modelo robusto + auditoría de cambios", "valor": 0}]},
            {"id": "BD-I3", "pregunta": "¿Se auditan los cambios a datos críticos (INSERT/UPDATE/DELETE)?",
             "opciones": [{"texto": "Sin auditoría de cambios", "valor": 3},
                         {"texto": "Auditoría básica en algunas tablas", "valor": 2},
                         {"texto": "Auditoría completa con timestamps y usuarios", "valor": 1},
                         {"texto": "CDC (Change Data Capture) con historial completo", "valor": 0}]}
        ],
        "C": [
            {"id": "BD-C1", "pregunta": "¿Qué nivel de sensibilidad tiene la información en esta base de datos?",
             "opciones": [{"texto": "PII sensible, datos financieros, información regulada (GDPR, PCI)", "valor": 3},
                         {"texto": "Información confidencial de negocio", "valor": 2},
                         {"texto": "Información interna no sensible", "valor": 1},
                         {"texto": "Información pública o de prueba", "valor": 0}]},
            {"id": "BD-C2", "pregunta": "¿Los datos están encriptados (at-rest y in-transit)?",
             "opciones": [{"texto": "Sin encriptación", "valor": 3},
                         {"texto": "Solo encriptación in-transit (TLS)", "valor": 2},
                         {"texto": "Encriptación at-rest (TDE) + TLS", "valor": 1},
                         {"texto": "Encriptación completa + column-level para datos sensibles", "valor": 0}]},
            {"id": "BD-C3", "pregunta": "¿Cómo se gestionan los accesos y privilegios a la base de datos?",
             "opciones": [{"texto": "Usuarios compartidos o acceso con SA/root", "valor": 3},
                         {"texto": "Usuarios individuales con privilegios amplios", "valor": 2},
                         {"texto": "Principio de menor privilegio con roles", "valor": 1},
                         {"texto": "PAM + Just-in-time access + revisión periódica", "valor": 0}]}
        ],
        "RTO": [
            {"id": "BD-RTO1", "pregunta": "¿Cuál es el tiempo máximo aceptable para restaurar esta BD?",
             "opciones": [{"texto": "Menos de 15 minutos - Failover automático requerido", "valor": 3},
                         {"texto": "Entre 15 minutos y 1 hora", "valor": 2},
                         {"texto": "Entre 1 y 4 horas", "valor": 1},
                         {"texto": "Más de 4 horas", "valor": 0}]},
            {"id": "BD-RTO2", "pregunta": "¿Cuál es el tamaño de la BD y tiempo estimado de restore?",
             "opciones": [{"texto": "Más de 1 TB - Restore toma varias horas", "valor": 3},
                         {"texto": "Entre 100 GB y 1 TB - Restore toma 1-2 horas", "valor": 2},
                         {"texto": "Entre 10-100 GB - Restore toma menos de 1 hora", "valor": 1},
                         {"texto": "Menos de 10 GB - Restore rápido", "valor": 0}]},
            {"id": "BD-RTO3", "pregunta": "¿Existen réplicas de lectura que podrían promover a primario?",
             "opciones": [{"texto": "Sin réplicas", "valor": 3},
                         {"texto": "Réplica manual que requiere configuración", "valor": 2},
                         {"texto": "Réplica con promoción semi-automática", "valor": 1},
                         {"texto": "Réplicas sincrónicas con failover automático", "valor": 0}]},
            {"id": "BD-RTO4", "pregunta": "¿Las aplicaciones pueden reconectarse automáticamente tras un failover?",
             "opciones": [{"texto": "No - Requieren reinicio manual", "valor": 3},
                         {"texto": "Parcial - Algunas apps se reconectan", "valor": 2},
                         {"texto": "Sí - Connection strings apuntan a listener/cluster", "valor": 1},
                         {"texto": "Sí - Con retry logic y circuit breakers", "valor": 0}]}
        ],
        "RPO": [
            {"id": "BD-RPO1", "pregunta": "¿Cuánta pérdida de datos es aceptable para esta BD?",
             "opciones": [{"texto": "Cero - Cada transacción debe persistirse", "valor": 3},
                         {"texto": "Hasta 5 minutos de transacciones", "valor": 2},
                         {"texto": "Hasta 1 hora de datos", "valor": 1},
                         {"texto": "Hasta 24 horas de datos", "valor": 0}]},
            {"id": "BD-RPO2", "pregunta": "¿Cuál es el modo de respaldo de transaction logs?",
             "opciones": [{"texto": "Sin respaldo de logs - Solo full backups", "valor": 3},
                         {"texto": "Log backup cada hora", "valor": 2},
                         {"texto": "Log backup cada 15 minutos", "valor": 1},
                         {"texto": "Log shipping continuo o replicación síncrona", "valor": 0}]},
            {"id": "BD-RPO3", "pregunta": "¿Se realizan verificaciones DBCC/CHECKSUM de respaldos?",
             "opciones": [{"texto": "Nunca se verifican respaldos", "valor": 3},
                         {"texto": "Verificación anual", "valor": 2},
                         {"texto": "Verificación mensual", "valor": 1},
                         {"texto": "Verificación automática en cada respaldo", "valor": 0}]}
        ],
        "BIA": [
            {"id": "BD-BIA1", "pregunta": "¿Esta BD soporta aplicaciones de cara al cliente?",
             "opciones": [{"texto": "Sí - E-commerce, banca, servicios críticos", "valor": 3},
                         {"texto": "Sí - Portal de clientes, CRM", "valor": 2},
                         {"texto": "No - Solo aplicaciones internas importantes", "valor": 1},
                         {"texto": "No - Solo aplicaciones internas no críticas", "valor": 0}]},
            {"id": "BD-BIA2", "pregunta": "¿Cuál es el impacto financiero por hora de inactividad?",
             "opciones": [{"texto": "Más de $50,000/hora - BD transaccional core", "valor": 3},
                         {"texto": "Entre $5,000 y $50,000/hora", "valor": 2},
                         {"texto": "Entre $500 y $5,000/hora", "valor": 1},
                         {"texto": "Menos de $500/hora", "valor": 0}]},
            {"id": "BD-BIA3", "pregunta": "¿Esta BD está sujeta a requisitos regulatorios?",
             "opciones": [{"texto": "Sí - PCI-DSS, HIPAA, SOX u otras regulaciones estrictas", "valor": 3},
                         {"texto": "Sí - GDPR u otras regulaciones de privacidad", "valor": 2},
                         {"texto": "Sí - Políticas internas de retención", "valor": 1},
                         {"texto": "No - Sin requisitos regulatorios específicos", "valor": 0}]},
            {"id": "BD-BIA4", "pregunta": "¿Cuántos reportes/procesos batch dependen de esta BD?",
             "opciones": [{"texto": "Reportes financieros, regulatorios o ejecutivos críticos", "valor": 3},
                         {"texto": "Reportes operacionales importantes", "valor": 2},
                         {"texto": "Reportes de gestión", "valor": 1},
                         {"texto": "Sin reportes o procesos batch", "valor": 0}]}
        ]
    },
    
    # ========== SERVIDOR WEB ==========
    "Servidor Web": {
        "D": [
            {"id": "SW-D1", "pregunta": "¿Cuánto tiempo puede estar inoperativo este servidor web?",
             "opciones": [{"texto": "Menos de 5 minutos - E-commerce o servicio crítico 24x7", "valor": 3},
                         {"texto": "Entre 5 y 30 minutos - Portal importante para clientes", "valor": 2},
                         {"texto": "Entre 30 min y 4 horas - Aplicación interna", "valor": 1},
                         {"texto": "Más de 4 horas - Sitio informativo no crítico", "valor": 0}]},
            {"id": "SW-D2", "pregunta": "¿Cuántas visitas/requests por día recibe este servidor web?",
             "opciones": [{"texto": "Más de 100,000 requests/día", "valor": 3},
                         {"texto": "Entre 10,000 y 100,000 requests/día", "valor": 2},
                         {"texto": "Entre 1,000 y 10,000 requests/día", "valor": 1},
                         {"texto": "Menos de 1,000 requests/día", "valor": 0}]},
            {"id": "SW-D3", "pregunta": "¿Existe balanceo de carga y múltiples instancias?",
             "opciones": [{"texto": "Servidor único sin balanceo", "valor": 3},
                         {"texto": "2 servidores con balanceo básico", "valor": 2},
                         {"texto": "Múltiples servidores con LB y auto-scaling", "valor": 1},
                         {"texto": "CDN + múltiples regiones + auto-scaling", "valor": 0}]},
            {"id": "SW-D4", "pregunta": "¿Hay monitoreo de disponibilidad y alertas configuradas?",
             "opciones": [{"texto": "Sin monitoreo - Los usuarios reportan caídas", "valor": 3},
                         {"texto": "Monitoreo básico de uptime", "valor": 2},
                         {"texto": "APM completo con alertas", "valor": 1},
                         {"texto": "Synthetic monitoring + APM + auto-remediation", "valor": 0}]}
        ],
        "I": [
            {"id": "SW-I1", "pregunta": "¿El servidor web procesa transacciones o solo sirve contenido estático?",
             "opciones": [{"texto": "Transacciones financieras o de pago", "valor": 3},
                         {"texto": "Transacciones de negocio (pedidos, registros)", "valor": 2},
                         {"texto": "Formularios y datos de usuarios", "valor": 1},
                         {"texto": "Solo contenido estático", "valor": 0}]},
            {"id": "SW-I2", "pregunta": "¿Hay protección contra modificación de contenido (WAF, IDS)?",
             "opciones": [{"texto": "Sin protección - Servidor expuesto directamente", "valor": 3},
                         {"texto": "Firewall de red básico", "valor": 2},
                         {"texto": "WAF con reglas estándar", "valor": 1},
                         {"texto": "WAF + RASP + monitoreo de integridad", "valor": 0}]},
            {"id": "SW-I3", "pregunta": "¿Cómo se gestiona el deployment de código?",
             "opciones": [{"texto": "Deployment manual por FTP/SSH sin control", "valor": 3},
                         {"texto": "Deployment manual con proceso documentado", "valor": 2},
                         {"texto": "CI/CD con aprobaciones y rollback", "valor": 1},
                         {"texto": "CI/CD + blue-green + feature flags", "valor": 0}]}
        ],
        "C": [
            {"id": "SW-C1", "pregunta": "¿Qué datos manejan los usuarios en este sitio web?",
             "opciones": [{"texto": "Datos de pago (tarjetas, cuentas bancarias)", "valor": 3},
                         {"texto": "PII sensible (documentos, historial médico)", "valor": 2},
                         {"texto": "Credenciales y datos de perfil básicos", "valor": 1},
                         {"texto": "Sin datos de usuarios", "valor": 0}]},
            {"id": "SW-C2", "pregunta": "¿El tráfico está encriptado con TLS/HTTPS?",
             "opciones": [{"texto": "HTTP sin encriptación", "valor": 3},
                         {"texto": "HTTPS opcional, HTTP disponible", "valor": 2},
                         {"texto": "HTTPS forzado con TLS 1.2+", "valor": 1},
                         {"texto": "HTTPS + HSTS + TLS 1.3 + Certificate pinning", "valor": 0}]},
            {"id": "SW-C3", "pregunta": "¿Cómo se protegen las sesiones y autenticación?",
             "opciones": [{"texto": "Sesiones básicas sin protección adicional", "valor": 3},
                         {"texto": "Cookies seguras + timeout", "valor": 2},
                         {"texto": "JWT + HttpOnly + Secure cookies", "valor": 1},
                         {"texto": "OAuth2/OIDC + MFA + rate limiting", "valor": 0}]}
        ],
        "RTO": [
            {"id": "SW-RTO1", "pregunta": "¿Cuál es el tiempo máximo aceptable de restauración del sitio web?",
             "opciones": [{"texto": "Menos de 5 minutos", "valor": 3},
                         {"texto": "Entre 5 y 30 minutos", "valor": 2},
                         {"texto": "Entre 30 minutos y 2 horas", "valor": 1},
                         {"texto": "Más de 2 horas", "valor": 0}]},
            {"id": "SW-RTO2", "pregunta": "¿Existe un sitio de DR o capacidad de failover geográfico?",
             "opciones": [{"texto": "Sin DR - Solo infraestructura primaria", "valor": 3},
                         {"texto": "DR cold - Requiere activación manual", "valor": 2},
                         {"texto": "DR warm - Réplica lista para activar", "valor": 1},
                         {"texto": "DR active-active multi-región", "valor": 0}]},
            {"id": "SW-RTO3", "pregunta": "¿El código y configuración están versionados para reconstrucción?",
             "opciones": [{"texto": "Sin control de versiones", "valor": 3},
                         {"texto": "Código en Git, configuración manual", "valor": 2},
                         {"texto": "Todo en Git + documentación", "valor": 1},
                         {"texto": "GitOps completo + IaC + containers", "valor": 0}]},
            {"id": "SW-RTO4", "pregunta": "¿Hay página de mantenimiento/status page para comunicar incidentes?",
             "opciones": [{"texto": "Sin página de status", "valor": 3},
                         {"texto": "Página estática que se activa manualmente", "valor": 2},
                         {"texto": "Status page automatizada", "valor": 1},
                         {"texto": "Status page + comunicación proactiva a clientes", "valor": 0}]}
        ],
        "RPO": [
            {"id": "SW-RPO1", "pregunta": "¿Cuánta pérdida de datos/transacciones es aceptable?",
             "opciones": [{"texto": "Cero - Cada transacción debe guardarse", "valor": 3},
                         {"texto": "Hasta 5 minutos", "valor": 2},
                         {"texto": "Hasta 1 hora", "valor": 1},
                         {"texto": "El contenido es estático, RPO no aplica", "valor": 0}]},
            {"id": "SW-RPO2", "pregunta": "¿Con qué frecuencia se respalda el contenido y configuración?",
             "opciones": [{"texto": "Sin respaldos automáticos", "valor": 3},
                         {"texto": "Respaldo diario", "valor": 2},
                         {"texto": "Respaldo cada hora + replicación de BD", "valor": 1},
                         {"texto": "Todo en Git + BD replicada síncronamente", "valor": 0}]},
            {"id": "SW-RPO3", "pregunta": "¿Los uploads de usuarios están respaldados?",
             "opciones": [{"texto": "Sin respaldo de archivos de usuarios", "valor": 3},
                         {"texto": "Respaldo diario de archivos", "valor": 2},
                         {"texto": "Almacenamiento en Object Storage con replicación", "valor": 1},
                         {"texto": "CDN + Object Storage multi-región", "valor": 0}]}
        ],
        "BIA": [
            {"id": "SW-BIA1", "pregunta": "¿Cuál es el propósito principal de este sitio web?",
             "opciones": [{"texto": "E-commerce / Ventas directas", "valor": 3},
                         {"texto": "Portal de clientes / Servicios", "valor": 2},
                         {"texto": "Marketing / Lead generation", "valor": 1},
                         {"texto": "Informativo / Documentación", "valor": 0}]},
            {"id": "SW-BIA2", "pregunta": "¿Cuál es el impacto financiero estimado por hora de caída?",
             "opciones": [{"texto": "Más de $10,000/hora - Ventas directas", "valor": 3},
                         {"texto": "Entre $1,000 y $10,000/hora", "valor": 2},
                         {"texto": "Entre $100 y $1,000/hora", "valor": 1},
                         {"texto": "Menos de $100/hora", "valor": 0}]},
            {"id": "SW-BIA3", "pregunta": "¿Cuál es el impacto reputacional de una caída prolongada?",
             "opciones": [{"texto": "Alto - Cobertura mediática, redes sociales", "valor": 3},
                         {"texto": "Medio - Quejas de clientes visibles", "valor": 2},
                         {"texto": "Bajo - Inconveniente para usuarios", "valor": 1},
                         {"texto": "Mínimo - Poco tráfico, sin visibilidad", "valor": 0}]},
            {"id": "SW-BIA4", "pregunta": "¿Hay obligaciones SLA con clientes que dependen de este sitio?",
             "opciones": [{"texto": "SLAs de 99.9%+ con penalidades", "valor": 3},
                         {"texto": "SLAs de 99.5% con compromisos", "valor": 2},
                         {"texto": "Compromisos internos de disponibilidad", "valor": 1},
                         {"texto": "Sin SLAs formales", "valor": 0}]}
        ]
    },
    
    # ========== EQUIPO DE RED ==========
    "Equipo de Red": {
        "D": [
            {"id": "ER-D1", "pregunta": "¿Cuánto tiempo puede estar fuera de servicio este equipo de red?",
             "opciones": [{"texto": "Menos de 5 minutos - Core/backbone crítico", "valor": 3},
                         {"texto": "Entre 5 y 30 minutos - Distribución importante", "valor": 2},
                         {"texto": "Entre 30 min y 2 horas - Acceso de usuarios", "valor": 1},
                         {"texto": "Más de 2 horas - Segmento no crítico", "valor": 0}]},
            {"id": "ER-D2", "pregunta": "¿Cuántos usuarios/dispositivos dependen de este equipo?",
             "opciones": [{"texto": "Más de 500 usuarios o toda la organización", "valor": 3},
                         {"texto": "Entre 100 y 500 usuarios o un edificio", "valor": 2},
                         {"texto": "Entre 20 y 100 usuarios o un piso", "valor": 1},
                         {"texto": "Menos de 20 usuarios", "valor": 0}]},
            {"id": "ER-D3", "pregunta": "¿Existe redundancia para este equipo (stack, HSRP/VRRP)?",
             "opciones": [{"texto": "Sin redundancia - Único punto de falla", "valor": 3},
                         {"texto": "Equipo de respaldo cold spare", "valor": 2},
                         {"texto": "Stack o par redundante con failover", "valor": 1},
                         {"texto": "Topología full mesh con múltiples paths", "valor": 0}]},
            {"id": "ER-D4", "pregunta": "¿Hay monitoreo SNMP/NetFlow y alertas configuradas?",
             "opciones": [{"texto": "Sin monitoreo", "valor": 3},
                         {"texto": "Ping básico", "valor": 2},
                         {"texto": "SNMP con alertas de disponibilidad", "valor": 1},
                         {"texto": "NMS completo + NetFlow + anomaly detection", "valor": 0}]}
        ],
        "I": [
            {"id": "ER-I1", "pregunta": "¿Las configuraciones están versionadas y respaldadas?",
             "opciones": [{"texto": "Sin respaldo de configuración", "valor": 3},
                         {"texto": "Respaldo manual ocasional", "valor": 2},
                         {"texto": "Respaldo automático diario (RANCID, Oxidized)", "valor": 1},
                         {"texto": "IaC completo + drift detection", "valor": 0}]},
            {"id": "ER-I2", "pregunta": "¿Cómo se controlan los cambios de configuración?",
             "opciones": [{"texto": "Cualquiera puede hacer cambios sin registro", "valor": 3},
                         {"texto": "Cambios documentados manualmente", "valor": 2},
                         {"texto": "Proceso de cambios con aprobación", "valor": 1},
                         {"texto": "Cambios solo via automatización + peer review", "valor": 0}]},
            {"id": "ER-I3", "pregunta": "¿Hay protección contra configuraciones no autorizadas?",
             "opciones": [{"texto": "Sin protección - Acceso admin compartido", "valor": 3},
                         {"texto": "Cuentas individuales sin MFA", "valor": 2},
                         {"texto": "AAA con TACACS+/RADIUS", "valor": 1},
                         {"texto": "AAA + MFA + logging centralizado + alertas", "valor": 0}]}
        ],
        "C": [
            {"id": "ER-C1", "pregunta": "¿Qué tipo de tráfico pasa por este equipo de red?",
             "opciones": [{"texto": "Tráfico de todos los segmentos incluyendo DMZ y producción", "valor": 3},
                         {"texto": "Tráfico de red corporativa sensible", "valor": 2},
                         {"texto": "Tráfico de usuarios internos", "valor": 1},
                         {"texto": "Tráfico de red de invitados o desarrollo", "valor": 0}]},
            {"id": "ER-C2", "pregunta": "¿Las comunicaciones de gestión están encriptadas?",
             "opciones": [{"texto": "Telnet y SNMPv1/v2 sin encriptación", "valor": 3},
                         {"texto": "SSH pero SNMP sin encriptación", "valor": 2},
                         {"texto": "SSH + SNMPv3 para todo", "valor": 1},
                         {"texto": "SSH + SNMPv3 + gestión via red OOB dedicada", "valor": 0}]},
            {"id": "ER-C3", "pregunta": "¿Hay ACLs y segmentación implementada en este equipo?",
             "opciones": [{"texto": "Sin ACLs - Todo el tráfico permitido", "valor": 3},
                         {"texto": "ACLs básicas entre VLANs principales", "valor": 2},
                         {"texto": "Segmentación completa con ACLs", "valor": 1},
                         {"texto": "Zero Trust con microsegmentación", "valor": 0}]}
        ],
        "RTO": [
            {"id": "ER-RTO1", "pregunta": "¿Cuál es el tiempo máximo aceptable para restaurar este equipo?",
             "opciones": [{"texto": "Menos de 5 minutos - Failover automático requerido", "valor": 3},
                         {"texto": "Entre 5 y 30 minutos - Swap de equipo rápido", "valor": 2},
                         {"texto": "Entre 30 minutos y 2 horas", "valor": 1},
                         {"texto": "Más de 2 horas", "valor": 0}]},
            {"id": "ER-RTO2", "pregunta": "¿Hay equipos spare disponibles para reemplazo?",
             "opciones": [{"texto": "Sin spare - Hay que comprar en emergencia", "valor": 3},
                         {"texto": "Spare disponible pero diferente modelo", "valor": 2},
                         {"texto": "Spare idéntico disponible on-site", "valor": 1},
                         {"texto": "Hot spare listo para activar", "valor": 0}]},
            {"id": "ER-RTO3", "pregunta": "¿Cuánto tiempo toma reconfigurar un equipo de reemplazo?",
             "opciones": [{"texto": "Horas - Configuración manual desde cero", "valor": 3},
                         {"texto": "30-60 minutos - Restore de config backup", "valor": 2},
                         {"texto": "5-15 minutos - ZTP/autoconfig", "valor": 1},
                         {"texto": "Inmediato - Stack/cluster asume automáticamente", "valor": 0}]},
            {"id": "ER-RTO4", "pregunta": "¿Hay contrato de soporte con RMA para este equipo?",
             "opciones": [{"texto": "Sin contrato de soporte", "valor": 3},
                         {"texto": "Soporte NBD (Next Business Day)", "valor": 2},
                         {"texto": "Soporte 4 horas", "valor": 1},
                         {"texto": "Soporte 24x7 con 2 horas de respuesta", "valor": 0}]}
        ],
        "RPO": [
            {"id": "ER-RPO1", "pregunta": "¿Con qué frecuencia se respalda la configuración?",
             "opciones": [{"texto": "Sin respaldos automáticos", "valor": 3},
                         {"texto": "Respaldo semanal", "valor": 2},
                         {"texto": "Respaldo diario", "valor": 1},
                         {"texto": "Respaldo en cada cambio (event-driven)", "valor": 0}]},
            {"id": "ER-RPO2", "pregunta": "¿Los logs se almacenan en servidor externo (Syslog)?",
             "opciones": [{"texto": "Solo logs locales que se pierden con el equipo", "valor": 3},
                         {"texto": "Syslog configurado pero no monitoreado", "valor": 2},
                         {"texto": "Syslog + retención definida", "valor": 1},
                         {"texto": "Syslog + SIEM + retención regulatoria", "valor": 0}]},
            {"id": "ER-RPO3", "pregunta": "¿La documentación de red está actualizada?",
             "opciones": [{"texto": "Sin documentación o muy desactualizada", "valor": 3},
                         {"texto": "Diagramas básicos pero incompletos", "valor": 2},
                         {"texto": "Documentación completa actualizada periódicamente", "valor": 1},
                         {"texto": "Auto-discovery + documentación automatizada", "valor": 0}]}
        ],
        "BIA": [
            {"id": "ER-BIA1", "pregunta": "¿Este equipo es parte de la ruta crítica de servicios al cliente?",
             "opciones": [{"texto": "Sí - Core/backbone para servicios externos", "valor": 3},
                         {"texto": "Sí - Ruta a datacenter principal", "valor": 2},
                         {"texto": "Parcial - Una de varias rutas", "valor": 1},
                         {"texto": "No - Solo red de oficinas", "valor": 0}]},
            {"id": "ER-BIA2", "pregunta": "¿Cuál es el impacto financiero por hora de caída?",
             "opciones": [{"texto": "Más de $10,000/hora - Afecta operaciones críticas", "valor": 3},
                         {"texto": "Entre $1,000 y $10,000/hora", "valor": 2},
                         {"texto": "Entre $100 y $1,000/hora", "valor": 1},
                         {"texto": "Menos de $100/hora", "valor": 0}]},
            {"id": "ER-BIA3", "pregunta": "¿Cuántos servicios/aplicaciones se verían afectados?",
             "opciones": [{"texto": "Todos los servicios de la organización", "valor": 3},
                         {"texto": "Servicios de un sitio o departamento crítico", "valor": 2},
                         {"texto": "Varios servicios de un área", "valor": 1},
                         {"texto": "Servicios limitados no críticos", "valor": 0}]},
            {"id": "ER-BIA4", "pregunta": "¿Hay workarounds si este equipo falla?",
             "opciones": [{"texto": "No hay alternativa - Dependencia total", "valor": 3},
                         {"texto": "Workaround parcial con degradación severa", "valor": 2},
                         {"texto": "Ruta alternativa con menor capacidad", "valor": 1},
                         {"texto": "Múltiples rutas - Redundancia completa", "valor": 0}]}
        ]
    },
    
    # ========== ALMACENAMIENTO ==========
    "Almacenamiento": {
        "D": [
            {"id": "AL-D1", "pregunta": "¿Cuánto tiempo puede estar inoperativo este storage?",
             "opciones": [{"texto": "Menos de 5 minutos - Storage de producción crítico", "valor": 3},
                         {"texto": "Entre 5 y 30 minutos - Storage de aplicaciones importantes", "valor": 2},
                         {"texto": "Entre 30 min y 4 horas - Storage secundario", "valor": 1},
                         {"texto": "Más de 4 horas - Storage de archivo/backup", "valor": 0}]},
            {"id": "AL-D2", "pregunta": "¿Cuántos servidores/aplicaciones dependen de este storage?",
             "opciones": [{"texto": "Más de 50 servidores o aplicaciones críticas", "valor": 3},
                         {"texto": "Entre 20 y 50 servidores", "valor": 2},
                         {"texto": "Entre 5 y 20 servidores", "valor": 1},
                         {"texto": "Menos de 5 servidores", "valor": 0}]},
            {"id": "AL-D3", "pregunta": "¿El storage tiene controladoras y paths redundantes?",
             "opciones": [{"texto": "Controladora única - Single point of failure", "valor": 3},
                         {"texto": "Dual controller pero single path", "valor": 2},
                         {"texto": "Dual controller + multipath activo-pasivo", "valor": 1},
                         {"texto": "Dual controller + multipath activo-activo + DR", "valor": 0}]},
            {"id": "AL-D4", "pregunta": "¿Cuál es el nivel de RAID y hot spare configurado?",
             "opciones": [{"texto": "RAID 0 o sin RAID", "valor": 3},
                         {"texto": "RAID 5 sin hot spare", "valor": 2},
                         {"texto": "RAID 6/10 con hot spare", "valor": 1},
                         {"texto": "RAID 6/10 + hot spare + erasure coding + DR", "valor": 0}]}
        ],
        "I": [
            {"id": "AL-I1", "pregunta": "¿Qué tipo de datos almacena este storage?",
             "opciones": [{"texto": "Bases de datos transaccionales y sistemas core", "valor": 3},
                         {"texto": "Archivos de producción y aplicaciones", "valor": 2},
                         {"texto": "Datos de usuarios y file shares", "valor": 1},
                         {"texto": "Backups, archivos o datos de desarrollo", "valor": 0}]},
            {"id": "AL-I2", "pregunta": "¿Hay verificación de integridad de datos (checksums, scrubbing)?",
             "opciones": [{"texto": "Sin verificación de integridad", "valor": 3},
                         {"texto": "Verificación manual ocasional", "valor": 2},
                         {"texto": "Scrubbing automático programado", "valor": 1},
                         {"texto": "Checksums en tiempo real + scrubbing + alertas", "valor": 0}]},
            {"id": "AL-I3", "pregunta": "¿Hay protección contra ransomware (snapshots inmutables)?",
             "opciones": [{"texto": "Sin protección contra ransomware", "valor": 3},
                         {"texto": "Snapshots regulares pero no inmutables", "valor": 2},
                         {"texto": "Snapshots inmutables configurados", "valor": 1},
                         {"texto": "Snapshots inmutables + air-gapped copy + anomaly detection", "valor": 0}]}
        ],
        "C": [
            {"id": "AL-C1", "pregunta": "¿Qué nivel de sensibilidad tienen los datos en este storage?",
             "opciones": [{"texto": "Datos altamente confidenciales (financieros, PII, secretos)", "valor": 3},
                         {"texto": "Datos confidenciales de negocio", "valor": 2},
                         {"texto": "Datos internos generales", "valor": 1},
                         {"texto": "Datos públicos o de prueba", "valor": 0}]},
            {"id": "AL-C2", "pregunta": "¿Los datos están encriptados at-rest?",
             "opciones": [{"texto": "Sin encriptación", "valor": 3},
                         {"texto": "Encriptación a nivel de controlador", "valor": 2},
                         {"texto": "Encriptación AES-256 con gestión de llaves", "valor": 1},
                         {"texto": "Encriptación + HSM + key rotation automático", "valor": 0}]},
            {"id": "AL-C3", "pregunta": "¿Cómo se controla el acceso a los datos en este storage?",
             "opciones": [{"texto": "Acceso abierto sin restricciones", "valor": 3},
                         {"texto": "ACLs básicas a nivel de share", "valor": 2},
                         {"texto": "RBAC completo + logging", "valor": 1},
                         {"texto": "RBAC + DLP + clasificación de datos + auditoría", "valor": 0}]}
        ],
        "RTO": [
            {"id": "AL-RTO1", "pregunta": "¿Cuál es el tiempo máximo aceptable para restaurar este storage?",
             "opciones": [{"texto": "Menos de 15 minutos - Requiere failover automático", "valor": 3},
                         {"texto": "Entre 15 minutos y 2 horas", "valor": 2},
                         {"texto": "Entre 2 y 8 horas", "valor": 1},
                         {"texto": "Más de 8 horas", "valor": 0}]},
            {"id": "AL-RTO2", "pregunta": "¿Existe réplica en sitio DR?",
             "opciones": [{"texto": "Sin réplica en DR", "valor": 3},
                         {"texto": "Réplica manual/tape a DR", "valor": 2},
                         {"texto": "Réplica asíncrona automática a DR", "valor": 1},
                         {"texto": "Réplica síncrona con failover automático", "valor": 0}]},
            {"id": "AL-RTO3", "pregunta": "¿Cuál es la capacidad del storage y tiempo estimado de rebuild?",
             "opciones": [{"texto": "Más de 100 TB - Rebuild toma días", "valor": 3},
                         {"texto": "Entre 20 y 100 TB - Rebuild toma horas", "valor": 2},
                         {"texto": "Entre 5 y 20 TB - Rebuild manejable", "valor": 1},
                         {"texto": "Menos de 5 TB - Rebuild rápido", "valor": 0}]},
            {"id": "AL-RTO4", "pregunta": "¿Hay contrato de soporte con reemplazo de partes?",
             "opciones": [{"texto": "Sin contrato de soporte", "valor": 3},
                         {"texto": "Soporte NBD", "valor": 2},
                         {"texto": "Soporte 4 horas para partes críticas", "valor": 1},
                         {"texto": "Soporte 24x7 con 2 horas + spare on-site", "valor": 0}]}
        ],
        "RPO": [
            {"id": "AL-RPO1", "pregunta": "¿Cuánta pérdida de datos es aceptable?",
             "opciones": [{"texto": "Cero - Réplica síncrona requerida", "valor": 3},
                         {"texto": "Hasta 15 minutos de datos", "valor": 2},
                         {"texto": "Hasta 1 hora de datos", "valor": 1},
                         {"texto": "Hasta 24 horas de datos", "valor": 0}]},
            {"id": "AL-RPO2", "pregunta": "¿Con qué frecuencia se toman snapshots?",
             "opciones": [{"texto": "Sin snapshots automáticos", "valor": 3},
                         {"texto": "Snapshots diarios", "valor": 2},
                         {"texto": "Snapshots cada hora", "valor": 1},
                         {"texto": "Snapshots cada 15 minutos o CDP", "valor": 0}]},
            {"id": "AL-RPO3", "pregunta": "¿Los snapshots se copian a ubicación externa?",
             "opciones": [{"texto": "Snapshots solo locales", "valor": 3},
                         {"texto": "Algunos snapshots van a otro sitio", "valor": 2},
                         {"texto": "Replicación completa a DR", "valor": 1},
                         {"texto": "Replicación a DR + copia a cloud/tape", "valor": 0}]}
        ],
        "BIA": [
            {"id": "AL-BIA1", "pregunta": "¿Este storage soporta sistemas de producción críticos?",
             "opciones": [{"texto": "Sí - Todas las BD y VMs de producción", "valor": 3},
                         {"texto": "Sí - Sistemas importantes de producción", "valor": 2},
                         {"texto": "Parcial - Mix de producción y desarrollo", "valor": 1},
                         {"texto": "No - Solo desarrollo, test o archivo", "valor": 0}]},
            {"id": "AL-BIA2", "pregunta": "¿Cuál es el impacto financiero por hora de inactividad?",
             "opciones": [{"texto": "Más de $50,000/hora - Storage de core business", "valor": 3},
                         {"texto": "Entre $5,000 y $50,000/hora", "valor": 2},
                         {"texto": "Entre $500 y $5,000/hora", "valor": 1},
                         {"texto": "Menos de $500/hora", "valor": 0}]},
            {"id": "AL-BIA3", "pregunta": "¿Hay datos únicos que solo existen en este storage?",
             "opciones": [{"texto": "Sí - Datos únicos sin copia en otro lugar", "valor": 3},
                         {"texto": "Parcial - Algunos datos únicos", "valor": 2},
                         {"texto": "Mayoría tiene copia/respaldo", "valor": 1},
                         {"texto": "Todo tiene copia en múltiples ubicaciones", "valor": 0}]},
            {"id": "AL-BIA4", "pregunta": "¿Cuánto tiempo tomaría recrear los datos si se pierden?",
             "opciones": [{"texto": "Imposible - Datos irrecuperables", "valor": 3},
                         {"texto": "Semanas o meses de trabajo", "valor": 2},
                         {"texto": "Días de trabajo", "valor": 1},
                         {"texto": "Horas - Datos fácilmente reproducibles", "valor": 0}]}
        ]
    },
    
    # ========== UPS ==========
    "UPS": {
        "D": [
            {"id": "UPS-D1", "pregunta": "¿Qué equipos críticos dependen de este UPS?",
             "opciones": [{"texto": "Datacenter completo o sala de servidores principal", "valor": 3},
                         {"texto": "Racks de servidores críticos", "valor": 2},
                         {"texto": "Equipos de red y comunicaciones", "valor": 1},
                         {"texto": "Equipos no críticos o desarrollo", "valor": 0}]},
            {"id": "UPS-D2", "pregunta": "¿Cuánta autonomía tiene este UPS con carga actual?",
             "opciones": [{"texto": "Menos de 5 minutos - Solo para transferencia a generador", "valor": 3},
                         {"texto": "Entre 5 y 15 minutos", "valor": 2},
                         {"texto": "Entre 15 y 30 minutos", "valor": 1},
                         {"texto": "Más de 30 minutos o hay generador con ATS", "valor": 0}]},
            {"id": "UPS-D3", "pregunta": "¿Existe UPS redundante (N+1 o 2N)?",
             "opciones": [{"texto": "UPS único sin redundancia", "valor": 3},
                         {"texto": "N+1 pero con bypass manual", "valor": 2},
                         {"texto": "N+1 con bypass automático", "valor": 1},
                         {"texto": "2N con alimentación dual a equipos", "valor": 0}]},
            {"id": "UPS-D4", "pregunta": "¿Hay monitoreo del UPS con alertas?",
             "opciones": [{"texto": "Sin monitoreo remoto", "valor": 3},
                         {"texto": "Panel local con alarmas audibles", "valor": 2},
                         {"texto": "Monitoreo SNMP con alertas básicas", "valor": 1},
                         {"texto": "Monitoreo completo + predictive maintenance", "valor": 0}]}
        ],
        "I": [
            {"id": "UPS-I1", "pregunta": "¿Qué calidad de energía proporciona este UPS?",
             "opciones": [{"texto": "Offline/Standby - Tiempo de transferencia largo", "valor": 3},
                         {"texto": "Line-interactive - Protección básica", "valor": 2},
                         {"texto": "Online doble conversión", "valor": 1},
                         {"texto": "Online + regulación + filtrado + aislamiento", "valor": 0}]},
            {"id": "UPS-I2", "pregunta": "¿Se realizan pruebas periódicas de baterías?",
             "opciones": [{"texto": "Nunca se prueban las baterías", "valor": 3},
                         {"texto": "Test anual", "valor": 2},
                         {"texto": "Test trimestral", "valor": 1},
                         {"texto": "Monitoreo continuo con predictive analytics", "valor": 0}]},
            {"id": "UPS-I3", "pregunta": "¿Las baterías están dentro de su vida útil recomendada?",
             "opciones": [{"texto": "Baterías vencidas o con más de 5 años", "valor": 3},
                         {"texto": "Entre 3 y 5 años de uso", "valor": 2},
                         {"texto": "Menos de 3 años", "valor": 1},
                         {"texto": "Baterías nuevas con mantenimiento preventivo", "valor": 0}]}
        ],
        "C": [
            {"id": "UPS-C1", "pregunta": "¿El UPS tiene interfaz de gestión segura?",
             "opciones": [{"texto": "Aislado en red de gestión OOB", "valor": 0},
                         {"texto": "Interfaz segura con autenticación", "valor": 1},
                         {"texto": "Interfaz de red con acceso básico", "valor": 2},
                         {"texto": "Sin interfaz de red o interfaz insegura", "valor": 3}]},
            {"id": "UPS-C2", "pregunta": "¿Quién tiene acceso físico al UPS?",
             "opciones": [{"texto": "Solo personal de facilities autorizado", "valor": 0},
                         {"texto": "Personal de TI con acceso controlado", "valor": 1},
                         {"texto": "Varios departamentos con acceso", "valor": 2},
                         {"texto": "Acceso no restringido", "valor": 3}]},
            {"id": "UPS-C3", "pregunta": "¿Los eventos del UPS se registran y auditan?",
             "opciones": [{"texto": "Sin registro de eventos", "valor": 3},
                         {"texto": "Log local en el UPS", "valor": 2},
                         {"texto": "Logs enviados a sistema centralizado", "valor": 1},
                         {"texto": "Logs + SIEM + retención regulatoria", "valor": 0}]}
        ],
        "RTO": [
            {"id": "UPS-RTO1", "pregunta": "¿Cuál es el tiempo máximo aceptable para reparar/reemplazar este UPS?",
             "opciones": [{"texto": "Menos de 4 horas - Crítico para operaciones", "valor": 3},
                         {"texto": "Entre 4 y 24 horas", "valor": 2},
                         {"texto": "Entre 1 y 3 días", "valor": 1},
                         {"texto": "Más de 3 días - Hay redundancia suficiente", "valor": 0}]},
            {"id": "UPS-RTO2", "pregunta": "¿Hay contrato de mantenimiento con SLA de respuesta?",
             "opciones": [{"texto": "Sin contrato de mantenimiento", "valor": 3},
                         {"texto": "Contrato con respuesta NBD", "valor": 2},
                         {"texto": "Contrato con respuesta 4-8 horas", "valor": 1},
                         {"texto": "Contrato 24x7 con 2 horas de respuesta", "valor": 0}]},
            {"id": "UPS-RTO3", "pregunta": "¿Hay baterías y módulos de repuesto disponibles?",
             "opciones": [{"texto": "Sin repuestos - Hay que ordenar", "valor": 3},
                         {"texto": "Repuestos disponibles en proveedor local", "valor": 2},
                         {"texto": "Repuestos críticos on-site", "valor": 1},
                         {"texto": "Módulos hot-swappable disponibles", "valor": 0}]},
            {"id": "UPS-RTO4", "pregunta": "¿Existe bypass manual/automático para mantenimiento?",
             "opciones": [{"texto": "Sin bypass - Requiere apagado", "valor": 3},
                         {"texto": "Bypass externo manual", "valor": 2},
                         {"texto": "Bypass interno con transferencia", "valor": 1},
                         {"texto": "Hot-swap sin interrupción", "valor": 0}]}
        ],
        "RPO": [
            {"id": "UPS-RPO1", "pregunta": "¿Hay procedimiento de shutdown ordenado configurado?",
             "opciones": [{"texto": "Sin procedimiento - Apagado abrupto", "valor": 3},
                         {"texto": "Shutdown manual documentado", "valor": 2},
                         {"texto": "Shutdown automático configurado", "valor": 1},
                         {"texto": "Orquestación completa de shutdown con prioridades", "valor": 0}]},
            {"id": "UPS-RPO2", "pregunta": "¿Los sistemas críticos tienen tiempo para guardar datos antes del apagado?",
             "opciones": [{"texto": "No - Autonomía insuficiente para shutdown", "valor": 3},
                         {"texto": "Apenas suficiente - Depende de la carga", "valor": 2},
                         {"texto": "Sí - Tiempo suficiente para shutdown ordenado", "valor": 1},
                         {"texto": "Sí - Más generador que toma la carga", "valor": 0}]},
            {"id": "UPS-RPO3", "pregunta": "¿Hay scripts/agentes de shutdown en los servidores conectados?",
             "opciones": [{"texto": "Sin integración con servidores", "valor": 3},
                         {"texto": "Algunos servidores tienen agentes", "valor": 2},
                         {"texto": "Todos los servidores críticos tienen agentes", "valor": 1},
                         {"texto": "Orquestación completa + verificación post-shutdown", "valor": 0}]}
        ],
        "BIA": [
            {"id": "UPS-BIA1", "pregunta": "¿Cuál es el impacto si este UPS falla completamente?",
             "opciones": [{"texto": "Apagón total del datacenter/site", "valor": 3},
                         {"texto": "Caída de sistemas críticos de producción", "valor": 2},
                         {"texto": "Caída de algunos sistemas importantes", "valor": 1},
                         {"texto": "Impacto limitado - Sistemas no críticos", "valor": 0}]},
            {"id": "UPS-BIA2", "pregunta": "¿Cuál es el impacto financiero por hora sin este UPS?",
             "opciones": [{"texto": "Más de $50,000/hora - Soporta core business", "valor": 3},
                         {"texto": "Entre $5,000 y $50,000/hora", "valor": 2},
                         {"texto": "Entre $500 y $5,000/hora", "valor": 1},
                         {"texto": "Menos de $500/hora", "valor": 0}]},
            {"id": "UPS-BIA3", "pregunta": "¿Cuántos equipos/servicios se verían afectados por falla del UPS?",
             "opciones": [{"texto": "Más de 50 servidores o equipos críticos", "valor": 3},
                         {"texto": "Entre 20 y 50 equipos", "valor": 2},
                         {"texto": "Entre 5 y 20 equipos", "valor": 1},
                         {"texto": "Menos de 5 equipos", "valor": 0}]},
            {"id": "UPS-BIA4", "pregunta": "¿El UPS soporta sistemas con requisitos regulatorios?",
             "opciones": [{"texto": "Sí - Sistemas sujetos a regulaciones estrictas", "valor": 3},
                         {"texto": "Sí - Sistemas con requisitos de compliance", "valor": 2},
                         {"texto": "Parcial - Algunos sistemas regulados", "valor": 1},
                         {"texto": "No - Sin requisitos regulatorios", "valor": 0}]}
        ]
    }
}


# ==================== FUNCIONES DE CÁLCULO ====================

def get_banco_preguntas_tipo(tipo_activo: str) -> Optional[Dict]:
    """Obtiene el banco de preguntas para un tipo de activo específico."""
    banco = BANCO_PREGUNTAS_DIC.get(tipo_activo)
    if not banco:
        for tipo, preguntas in BANCO_PREGUNTAS_DIC.items():
            if tipo.lower() in tipo_activo.lower() or tipo_activo.lower() in tipo.lower():
                return preguntas
        return BANCO_PREGUNTAS_DIC.get("Servidor Físico")
    return banco


def calcular_valor_dimension(respuestas: List[int]) -> Tuple[int, str]:
    """Calcula el valor de una dimensión basado en las respuestas."""
    if not respuestas:
        return 0, "N"
    max_val = max(respuestas)
    avg_val = sum(respuestas) / len(respuestas)
    if max_val == 3 and avg_val < 1.5:
        valor = 2
    elif max_val == 2 and avg_val < 1.0:
        valor = 1
    else:
        valor = max_val
    nivel_map = {0: "N", 1: "B", 2: "M", 3: "A"}
    return valor, nivel_map.get(valor, "N")


def calcular_criticidad(valor_d: int, valor_i: int, valor_c: int) -> Tuple[int, str]:
    """Calcula la criticidad como el máximo de D, I, C."""
    criticidad = max(valor_d, valor_i, valor_c)
    nivel_map = {0: "Nula", 1: "Baja", 2: "Media", 3: "Alta"}
    return criticidad, nivel_map.get(criticidad, "Nula")


def calcular_rto_rpo(respuestas_rto: List[int], respuestas_rpo: List[int]) -> Dict:
    """Calcula los valores de RTO y RPO basados en las respuestas."""
    if respuestas_rto:
        rto_max = max(respuestas_rto)
        rto_map = {3: ("< 1 hora", "Alto"), 2: ("1-4 horas", "Medio"),
                   1: ("4-24 horas", "Bajo"), 0: ("> 24 horas", "Nulo")}
        rto_tiempo, rto_nivel = rto_map.get(rto_max, ("> 24 horas", "Nulo"))
    else:
        rto_max, rto_tiempo, rto_nivel = 0, "No definido", "Nulo"
    if respuestas_rpo:
        rpo_max = max(respuestas_rpo)
        rpo_map = {3: ("0 (cero pérdida)", "Alto"), 2: ("< 1 hora", "Medio"),
                   1: ("1-4 horas", "Bajo"), 0: ("> 24 horas", "Nulo")}
        rpo_tiempo, rpo_nivel = rpo_map.get(rpo_max, ("> 24 horas", "Nulo"))
    else:
        rpo_max, rpo_tiempo, rpo_nivel = 0, "No definido", "Nulo"
    return {"RTO_Valor": rto_max, "RTO_Tiempo": rto_tiempo, "RTO_Nivel": rto_nivel,
            "RPO_Valor": rpo_max, "RPO_Tiempo": rpo_tiempo, "RPO_Nivel": rpo_nivel}


def calcular_bia(respuestas_bia: List[int]) -> Dict:
    """Calcula el impacto BIA basado en las respuestas."""
    if not respuestas_bia:
        return {"BIA_Valor": 0, "BIA_Nivel": "Nulo"}
    bia_max = max(respuestas_bia)
    bia_avg = sum(respuestas_bia) / len(respuestas_bia)
    if bia_max == 3 and bia_avg >= 2.0:
        bia_valor, bia_nivel = 3, "Alto"
    elif bia_max >= 2 and bia_avg >= 1.5:
        bia_valor, bia_nivel = 2, "Medio"
    elif bia_max >= 1 and bia_avg >= 1.0:
        bia_valor, bia_nivel = 1, "Bajo"
    else:
        bia_valor, bia_nivel = 0, "Nulo"
    return {"BIA_Valor": bia_valor, "BIA_Nivel": bia_nivel}


def procesar_cuestionario_dic(tipo_activo: str, respuestas: Dict[str, int]) -> Dict:
    """Procesa todas las respuestas del cuestionario y calcula D/I/C/RTO/RPO/BIA."""
    resp_d, resp_i, resp_c = [], [], []
    resp_rto, resp_rpo, resp_bia = [], [], []
    for pregunta_id, valor in respuestas.items():
        if "-D" in pregunta_id:
            resp_d.append(valor)
        elif "-I" in pregunta_id:
            resp_i.append(valor)
        elif "-C" in pregunta_id:
            resp_c.append(valor)
        elif "-RTO" in pregunta_id:
            resp_rto.append(valor)
        elif "-RPO" in pregunta_id:
            resp_rpo.append(valor)
        elif "-BIA" in pregunta_id:
            resp_bia.append(valor)
    valor_d, nivel_d = calcular_valor_dimension(resp_d)
    valor_i, nivel_i = calcular_valor_dimension(resp_i)
    valor_c, nivel_c = calcular_valor_dimension(resp_c)
    criticidad, criticidad_nivel = calcular_criticidad(valor_d, valor_i, valor_c)
    rto_rpo = calcular_rto_rpo(resp_rto, resp_rpo)
    bia = calcular_bia(resp_bia)
    return {
        "D": nivel_d, "Valor_D": valor_d, "I": nivel_i, "Valor_I": valor_i,
        "C": nivel_c, "Valor_C": valor_c, "Criticidad": criticidad, "Criticidad_Nivel": criticidad_nivel,
        "RTO_Valor": rto_rpo["RTO_Valor"], "RTO_Tiempo": rto_rpo["RTO_Tiempo"], "RTO_Nivel": rto_rpo["RTO_Nivel"],
        "RPO_Valor": rto_rpo["RPO_Valor"], "RPO_Tiempo": rto_rpo["RPO_Tiempo"], "RPO_Nivel": rto_rpo["RPO_Nivel"],
        "BIA_Valor": bia["BIA_Valor"], "BIA_Nivel": bia["BIA_Nivel"],
        "Respuestas_Detalle": respuestas, "Tipo_Activo_Evaluado": tipo_activo,
        "Total_Preguntas": len(respuestas), "Fecha_Calculo": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def guardar_respuestas_dic(id_evaluacion: str, id_activo: str, tipo_activo: str, respuestas: Dict[str, int]) -> Dict:
    """Guarda las respuestas del cuestionario DIC y calcula los valores."""
    import json
    resultado = procesar_cuestionario_dic(tipo_activo, respuestas)
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            columnas_nuevas = ["Respuestas_JSON TEXT", "RTO_Valor INTEGER", "RTO_Tiempo TEXT", "RTO_Nivel TEXT",
                              "RPO_Valor INTEGER", "RPO_Tiempo TEXT", "RPO_Nivel TEXT", "BIA_Valor INTEGER", "BIA_Nivel TEXT"]
            for col in columnas_nuevas:
                try:
                    cursor.execute(f"ALTER TABLE IDENTIFICACION_VALORACION ADD COLUMN {col}")
                    conn.commit()
                except:
                    pass
            cursor.execute("SELECT id FROM IDENTIFICACION_VALORACION WHERE ID_Evaluacion = ? AND ID_Activo = ?",
                          (id_evaluacion, id_activo))
            existente = cursor.fetchone()
            if existente:
                cursor.execute("""UPDATE IDENTIFICACION_VALORACION SET D = ?, Valor_D = ?, I = ?, Valor_I = ?,
                    C = ?, Valor_C = ?, Criticidad = ?, Criticidad_Nivel = ?, RTO_Valor = ?, RTO_Tiempo = ?, RTO_Nivel = ?,
                    RPO_Valor = ?, RPO_Tiempo = ?, RPO_Nivel = ?, BIA_Valor = ?, BIA_Nivel = ?, Respuestas_JSON = ?,
                    Fecha_Valoracion = ? WHERE ID_Evaluacion = ? AND ID_Activo = ?""",
                    (resultado["D"], resultado["Valor_D"], resultado["I"], resultado["Valor_I"],
                     resultado["C"], resultado["Valor_C"], resultado["Criticidad"], resultado["Criticidad_Nivel"],
                     resultado["RTO_Valor"], resultado["RTO_Tiempo"], resultado["RTO_Nivel"],
                     resultado["RPO_Valor"], resultado["RPO_Tiempo"], resultado["RPO_Nivel"],
                     resultado["BIA_Valor"], resultado["BIA_Nivel"], json.dumps(respuestas),
                     resultado["Fecha_Calculo"], id_evaluacion, id_activo))
            else:
                cursor.execute("""INSERT INTO IDENTIFICACION_VALORACION (ID_Evaluacion, ID_Activo, Nombre_Activo,
                    D, Valor_D, I, Valor_I, C, Valor_C, Criticidad, Criticidad_Nivel, RTO_Valor, RTO_Tiempo, RTO_Nivel,
                    RPO_Valor, RPO_Tiempo, RPO_Nivel, BIA_Valor, BIA_Nivel, Respuestas_JSON, Fecha_Valoracion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (id_evaluacion, id_activo, "", resultado["D"], resultado["Valor_D"], resultado["I"], resultado["Valor_I"],
                     resultado["C"], resultado["Valor_C"], resultado["Criticidad"], resultado["Criticidad_Nivel"],
                     resultado["RTO_Valor"], resultado["RTO_Tiempo"], resultado["RTO_Nivel"],
                     resultado["RPO_Valor"], resultado["RPO_Tiempo"], resultado["RPO_Nivel"],
                     resultado["BIA_Valor"], resultado["BIA_Nivel"], json.dumps(respuestas), resultado["Fecha_Calculo"]))
        except Exception as e:
            raise e
    return resultado


def get_respuestas_previas(id_evaluacion: str, id_activo: str) -> Optional[Dict[str, int]]:
    """Obtiene las respuestas previas del cuestionario DIC para un activo."""
    import json
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT Respuestas_JSON FROM IDENTIFICACION_VALORACION WHERE ID_Evaluacion = ? AND ID_Activo = ?",
                          (id_evaluacion, id_activo))
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return None
        except:
            return None


def get_estadisticas_banco() -> Dict:
    """Retorna estadísticas del banco de preguntas"""
    stats = {}
    for tipo, banco in BANCO_PREGUNTAS_DIC.items():
        total = sum(len(banco.get(dim, [])) for dim in ["D", "I", "C", "RTO", "RPO", "BIA"])
        stats[tipo] = {"total": total, "D": len(banco.get("D", [])), "I": len(banco.get("I", [])),
                       "C": len(banco.get("C", [])), "RTO": len(banco.get("RTO", [])),
                       "RPO": len(banco.get("RPO", [])), "BIA": len(banco.get("BIA", []))}
    return stats


# ==================== CÁLCULO DE FRECUENCIA DESDE RESPUESTAS ====================

def calcular_frecuencia_desde_cuestionario(id_evaluacion: str, id_activo: str) -> Tuple[float, str, Dict]:
    """
    Calcula la FRECUENCIA de amenazas basándose en las respuestas del cuestionario.
    
    LÓGICA MAGERIT:
    La frecuencia se determina inversamente al nivel de controles y protección.
    - Activo con buenos controles (respuestas altas) = Frecuencia BAJA
    - Activo con malos controles (respuestas bajas) = Frecuencia ALTA
    
    Factores considerados:
    1. Criticidad del activo (D/I/C) - Mayor criticidad = más exposición
    2. RTO bajo = activo más crítico = potencialmente más atacado
    3. BIA alto = más impacto = más atractivo para amenazas
    
    Escala de frecuencia MAGERIT:
    - 0.1: Nula (cada varios años)
    - 1.0: Baja (1 vez al año)
    - 2.0: Media (mensualmente)
    - 3.0: Alta (a diario)
    
    Returns:
        (frecuencia: float, nivel: str, detalles: Dict)
    """
    # Obtener valoración del activo
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Primero verificar qué columnas existen
        cursor.execute("PRAGMA table_info(IDENTIFICACION_VALORACION)")
        columnas_existentes = {row[1] for row in cursor.fetchall()}
        
        # Consulta base solo con columnas que seguro existen
        cursor.execute("""
            SELECT D, Valor_D, I, Valor_I, C, Valor_C, Criticidad, Criticidad_Nivel
            FROM IDENTIFICACION_VALORACION 
            WHERE ID_Evaluacion = ? AND ID_Activo = ?
        """, (id_evaluacion, id_activo))
        
        row = cursor.fetchone()
        
        if not row:
            # Sin valoración, frecuencia media por defecto
            return 2.0, "Media", {"mensaje": "Sin valoración D/I/C - usando frecuencia media por defecto"}
        
        # Extraer valores básicos
        valor_d = row[1] or 0
        valor_i = row[3] or 0
        valor_c = row[5] or 0
        criticidad = row[6] or 0
        criticidad_nivel = row[7] or "Sin valorar"
        
        # Valores opcionales (pueden no existir en la tabla)
        rto_nivel = "N/A"
        bia_nivel = "N/A"
        
        # Calcular frecuencia base según criticidad
        # Activos más críticos tienen mayor exposición y son más atacados
        if criticidad >= 3:  # Alta criticidad
            freq_base = 2.5  # Tendencia a frecuencia alta
        elif criticidad == 2:  # Media criticidad
            freq_base = 1.5  # Tendencia a frecuencia media
        elif criticidad == 1:  # Baja criticidad
            freq_base = 0.5  # Tendencia a frecuencia baja
        else:  # Sin valorar
            freq_base = 1.0  # Frecuencia media-baja
        
        # Ajustar por RTO (activos con RTO bajo son más críticos → más atacados)
        if rto_nivel == "Crítico":
            freq_base += 0.5
        elif rto_nivel == "Alto":
            freq_base += 0.3
        elif rto_nivel == "Medio":
            freq_base += 0.1
        
        # Ajustar por BIA (activos con alto impacto al negocio son más atractivos)
        if bia_nivel == "Crítico":
            freq_base += 0.5
        elif bia_nivel == "Alto":
            freq_base += 0.3
        elif bia_nivel == "Medio":
            freq_base += 0.1
        
        # Limitar al rango válido [0.1, 3.0]
        frecuencia = max(0.1, min(3.0, freq_base))
        
        # Mapear a valores discretos de MAGERIT
        if frecuencia >= 2.5:
            frecuencia_final = 3.0
            nivel = "Alta"
        elif frecuencia >= 1.5:
            frecuencia_final = 2.0
            nivel = "Media"
        elif frecuencia >= 0.5:
            frecuencia_final = 1.0
            nivel = "Baja"
        else:
            frecuencia_final = 0.1
            nivel = "Nula"
        
        detalles = {
            "criticidad": criticidad,
            "criticidad_nivel": criticidad_nivel,
            "rto_nivel": rto_nivel,
            "bia_nivel": bia_nivel,
            "freq_base": freq_base,
            "frecuencia_calculada": frecuencia_final,
            "factores": {
                "criticidad_aporte": "Alto" if criticidad >= 3 else "Medio" if criticidad >= 2 else "Bajo",
                "rto_aporte": rto_nivel,
                "bia_aporte": bia_nivel
            }
        }
        
        return frecuencia_final, nivel, detalles


def calcular_frecuencia_todas_amenazas(id_evaluacion: str, id_activo: str) -> List[Dict]:
    """
    Calcula la frecuencia para todas las amenazas de un activo.
    Usa la frecuencia base del cuestionario pero puede ajustar por tipo de amenaza.
    
    Returns:
        Lista de dicts con: id_va, amenaza, frecuencia, nivel, impacto, riesgo
    """
    # Obtener frecuencia base del activo
    freq_base, nivel_base, detalles = calcular_frecuencia_desde_cuestionario(id_evaluacion, id_activo)
    
    # Obtener amenazas del activo
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT va.id, va.Cod_Amenaza, va.Amenaza, va.Vulnerabilidad,
                   va.Degradacion_D, va.Degradacion_I, va.Degradacion_C, va.Impacto
            FROM VULNERABILIDADES_AMENAZAS va
            WHERE va.ID_Evaluacion = ? AND va.ID_Activo = ?
        """, (id_evaluacion, id_activo))
        
        amenazas = cursor.fetchall()
        
        resultados = []
        for am in amenazas:
            id_va = am[0]
            cod_amenaza = am[1] or ""
            nombre_amenaza = am[2]
            vulnerabilidad = am[3]
            impacto = am[7] or 0
            
            # Ajustar frecuencia según tipo de amenaza
            freq_ajustada = freq_base
            
            # Amenazas de tipo "Ataques Intencionados" (A.xx) tienden a ser más frecuentes
            if cod_amenaza.startswith("A."):
                freq_ajustada = min(3.0, freq_base + 0.5)
            # Errores no intencionados (E.xx) tienen frecuencia similar
            elif cod_amenaza.startswith("E."):
                freq_ajustada = freq_base
            # Desastres naturales (N.xx) son menos frecuentes
            elif cod_amenaza.startswith("N."):
                freq_ajustada = max(0.1, freq_base - 0.5)
            # Origen industrial (I.xx) frecuencia media
            elif cod_amenaza.startswith("I."):
                freq_ajustada = max(0.1, freq_base - 0.2)
            
            # Mapear a valores discretos
            if freq_ajustada >= 2.5:
                freq_final = 3.0
                nivel = "Alta"
            elif freq_ajustada >= 1.5:
                freq_final = 2.0
                nivel = "Media"
            elif freq_ajustada >= 0.5:
                freq_final = 1.0
                nivel = "Baja"
            else:
                freq_final = 0.1
                nivel = "Nula"
            
            # Calcular riesgo
            riesgo = freq_final * impacto
            
            resultados.append({
                "id_va": id_va,
                "cod_amenaza": cod_amenaza,
                "amenaza": nombre_amenaza,
                "vulnerabilidad": vulnerabilidad,
                "frecuencia": freq_final,
                "frecuencia_nivel": nivel,
                "impacto": impacto,
                "riesgo": riesgo
            })
        
        return resultados

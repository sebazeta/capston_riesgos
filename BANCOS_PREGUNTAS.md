# 📋 Bancos de Preguntas - Sistema de Evaluación de Riesgos

Este documento contiene los dos bancos de preguntas para servidores físicos y virtuales.
**Edita este archivo y envíamelo con tus correcciones.**

---

## 📖 Guía de Formato

| Campo | Descripción |
|-------|-------------|
| **ID_Pregunta** | Identificador único (PF = Físico, PV = Virtual) |
| **Dimensión** | D = Disponibilidad, I = Integridad, C = Confidencialidad |
| **Tipo_Respuesta** | `0/1` = Sí/No (radio buttons), `1-5` = Escala (slider) |
| **Peso** | Importancia de 1 a 5 (5 = más importante) |

---

## 🖥️ BANCO DE PREGUNTAS - SERVIDORES FÍSICOS

### 📌 Preguntas BIA/RTO/RPO (Obligatorias)

| ID | Dimensión | Pregunta | Tipo | Peso |
|----|-----------|----------|------|------|
| PF-BIA-001 | D | ¿Cuál es el nivel de impacto al negocio (BIA) si este activo falla? (1=Mínimo, 5=Crítico) | 1-5 | 5 |
| PF-RTO-001 | D | ¿Cuál es el RTO objetivo en horas? (Tiempo máximo aceptable de inactividad) | 1-5 | 5 |
| PF-RPO-001 | I | ¿Cuál es el RPO objetivo en horas? (Pérdida máxima aceptable de datos) | 1-5 | 5 |

### 🔵 Disponibilidad (D)

| ID | Pregunta | Tipo | Peso |
|----|----------|------|------|
| PF-D-001 | ¿El servidor físico cuenta con fuente de alimentación redundante? | 0/1 | 5 |
| PF-D-002 | ¿Existe un sistema UPS (backup eléctrico) dedicado al servidor? | 0/1 | 5 |
| PF-D-003 | ¿El servidor está en un rack con refrigeración adecuada? | 0/1 | 4 |
| PF-D-004 | ¿Se realizan mantenimientos preventivos periódicos del hardware? | 1-5 | 4 |
| PF-D-005 | ¿Existen piezas de repuesto disponibles para componentes críticos? | 0/1 | 3 |
| PF-D-006 | ¿El servidor tiene conexiones de red redundantes? | 0/1 | 4 |
| PF-D-007 | ¿Existe un servidor físico de respaldo (standby)? | 0/1 | 5 |
| PF-D-008 | ¿El servidor cuenta con sistemas de detección de incendios? | 0/1 | 4 |
| PF-D-009 | ¿Existe plan de recuperación ante desastres documentado? | 1-5 | 5 |

### 🟢 Integridad (I)

| ID | Pregunta | Tipo | Peso |
|----|----------|------|------|
| PF-I-001 | ¿Los discos físicos tienen tecnología RAID implementada? | 0/1 | 5 |
| PF-I-002 | ¿Se realizan backups físicos periódicos de los datos? | 1-5 | 5 |
| PF-I-003 | ¿Los backups físicos se almacenan en ubicación separada? | 0/1 | 4 |
| PF-I-004 | ¿Se verifica la integridad de los backups regularmente? | 1-5 | 4 |
| PF-I-005 | ¿Existe monitoreo de salud de discos (SMART)? | 0/1 | 3 |
| PF-I-006 | ¿Se realizan pruebas de restauración de backups? | 1-5 | 5 |

### 🔴 Confidencialidad (C)

| ID | Pregunta | Tipo | Peso |
|----|----------|------|------|
| PF-C-001 | ¿El servidor está en un área con acceso físico restringido? | 1-5 | 5 |
| PF-C-002 | ¿Existe videovigilancia en el área del servidor? | 0/1 | 3 |
| PF-C-003 | ¿Los discos físicos están cifrados (encryption at rest)? | 0/1 | 5 |
| PF-C-004 | ¿Se registran los accesos físicos al área del servidor? | 1-5 | 4 |
| PF-C-005 | ¿El proceso de disposal de discos físicos es seguro? | 1-5 | 4 |

**Total preguntas físicas: 25**

---

## ☁️ BANCO DE PREGUNTAS - SERVIDORES VIRTUALES

### 📌 Preguntas BIA/RTO/RPO (Obligatorias)

| ID | Dimensión | Pregunta | Tipo | Peso |
|----|-----------|----------|------|------|
| PV-BIA-001 | D | ¿Cuál es el nivel de impacto al negocio (BIA) si este activo falla? (1=Mínimo, 5=Crítico) | 1-5 | 5 |
| PV-RTO-001 | D | ¿Cuál es el RTO objetivo en horas? (Tiempo máximo aceptable de inactividad) | 1-5 | 5 |
| PV-RPO-001 | I | ¿Cuál es el RPO objetivo en horas? (Pérdida máxima aceptable de datos) | 1-5 | 5 |

### 🔵 Disponibilidad (D)

| ID | Pregunta | Tipo | Peso |
|----|----------|------|------|
| PV-D-001 | ¿La VM tiene snapshots automatizados configurados? | 0/1 | 4 |
| PV-D-002 | ¿El hipervisor tiene alta disponibilidad (HA) habilitada? | 0/1 | 5 |
| PV-D-003 | ¿Existe migración automática en caso de fallo del host? | 0/1 | 5 |
| PV-D-004 | ¿La VM tiene recursos garantizados (no compartidos)? | 1-5 | 4 |
| PV-D-005 | ¿Se monitorea el rendimiento de la VM en tiempo real? | 1-5 | 3 |
| PV-D-006 | ¿Existen réplicas de la VM en otro datacenter/host? | 0/1 | 5 |
| PV-D-007 | ¿El almacenamiento compartido es redundante? | 0/1 | 5 |
| PV-D-008 | ¿Existen políticas de DRS (Distributed Resource Scheduler)? | 1-5 | 4 |

### 🟢 Integridad (I)

| ID | Pregunta | Tipo | Peso |
|----|----------|------|------|
| PV-I-001 | ¿Los backups de la VM se realizan de forma automatizada? | 1-5 | 5 |
| PV-I-002 | ¿Los backups incluyen tanto la VM como los datos? | 0/1 | 5 |
| PV-I-003 | ¿Los snapshots se almacenan en storage diferente del principal? | 0/1 | 4 |
| PV-I-004 | ¿Se prueban las restauraciones de backups periódicamente? | 1-5 | 5 |
| PV-I-005 | ¿Existe versionado de configuración de la VM? | 0/1 | 3 |
| PV-I-006 | ¿Los discos virtuales tienen protección contra corrupción? | 1-5 | 4 |

### 🔴 Confidencialidad (C)

| ID | Pregunta | Tipo | Peso |
|----|----------|------|------|
| PV-C-001 | ¿Los discos virtuales están cifrados? | 0/1 | 5 |
| PV-C-002 | ¿El acceso al hipervisor está restringido y auditado? | 1-5 | 5 |
| PV-C-003 | ¿La red virtual está segmentada (VLANs)? | 1-5 | 4 |
| PV-C-004 | ¿Existen controles de aislamiento entre VMs? | 1-5 | 4 |
| PV-C-005 | ¿Se auditan los accesos administrativos a la VM? | 1-5 | 5 |
| PV-C-006 | ¿El proceso de eliminación de VMs incluye borrado seguro? | 1-5 | 4 |

**Total preguntas virtuales: 25**

---

## ✏️ Instrucciones para Modificar

1. **Agregar pregunta**: Añade una fila nueva en la sección correspondiente
2. **Eliminar pregunta**: Borra la fila completa
3. **Cambiar tipo de respuesta**: Modifica `0/1` ↔ `1-5`
4. **Ajustar peso**: Cambia el valor de 1 a 5

### Límites:
- **Máximo 25 preguntas por banco** (incluyendo BIA/RTO/RPO)
- Las 3 primeras preguntas (BIA, RTO, RPO) son obligatorias

---

*Edita este documento y envíamelo cuando termines. Actualizaré el sistema automáticamente.*

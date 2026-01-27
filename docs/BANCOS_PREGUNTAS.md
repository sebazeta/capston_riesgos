# 📋 BANCOS DE PREGUNTAS TITA - BIA/MAGERIT

## Estructura General

Cada banco tiene **21 preguntas** organizadas en 5 bloques:
- **Bloque A**: Impacto (5 preguntas) - Dimensión D, I, C
- **Bloque B**: Continuidad (4 preguntas) - Dimensión D
- **Bloque C**: Controles (5 preguntas) - Dimensión D, I, C
- **Bloque D**: Ciberseguridad (4 preguntas) - Dimensión I, C, D
- **Bloque E**: Exposición (3 preguntas) - Dimensión C, D

### Escala de Respuestas
- **Opción 1**: Nivel más bajo / Sin control / Mayor riesgo
- **Opción 2**: Nivel básico
- **Opción 3**: Nivel intermedio
- **Opción 4**: Nivel óptimo / Control completo / Menor riesgo

### Pesos
- **5**: Pregunta crítica (mayor impacto en el cálculo)
- **4**: Pregunta importante
- **3**: Pregunta estándar

---

# 🖥️ BANCO 1: SERVIDOR FÍSICO (21 preguntas)

## Bloque A: Impacto (5 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PF-A01 | D | ¿Cuál es el tiempo máximo tolerable de interrupción (RTO) del servidor? | Más de 72 horas | 24-72 horas | 4-24 horas | Menos de 4 horas | 5 |
| PF-A02 | D | ¿Cuántos usuarios o procesos críticos dependen directamente de este servidor? | Menos de 10 | 10-50 | 50-200 | Más de 200 | 4 |
| PF-A03 | I | ¿Qué nivel de pérdida de datos es tolerable (RPO)? | Hasta 1 semana | Hasta 24 horas | Hasta 4 horas | Cero pérdida | 5 |
| PF-A04 | C | ¿Qué tipo de información procesa este servidor? | Pública | Interna | Confidencial | Altamente sensible | 5 |
| PF-A05 | D | ¿Cuál sería el impacto financiero estimado por hora de inactividad? | Menor a $100 | $100-$1,000 | $1,000-$10,000 | Mayor a $10,000 | 4 |

## Bloque B: Continuidad (4 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PF-B01 | D | ¿Existe un servidor de respaldo o failover configurado? | No existe | Existe sin probar | Probado anualmente | Activo-Activo probado | 5 |
| PF-B02 | D | ¿Con qué frecuencia se realizan copias de seguridad? | Mensual o nunca | Semanal | Diario | Continuo/Tiempo real | 5 |
| PF-B03 | D | ¿Se prueban regularmente las restauraciones de backup? | Nunca | Anualmente | Trimestralmente | Mensualmente | 4 |
| PF-B04 | D | ¿El servidor tiene fuente de alimentación redundante (UPS)? | Sin UPS | UPS básico | UPS + generador | Redundancia completa | 3 |

## Bloque C: Controles (5 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PF-C01 | C | ¿Cómo se gestiona el control de acceso al servidor? | Sin control | Usuario/contraseña básico | Roles y permisos | MFA + roles + auditoría | 5 |
| PF-C02 | I | ¿Con qué frecuencia se aplican parches de seguridad? | Nunca/Raramente | Anualmente | Trimestralmente | Mensual o automático | 5 |
| PF-C03 | D | ¿Existe monitoreo de rendimiento y alertas? | Sin monitoreo | Monitoreo manual | Alertas básicas | Monitoreo 24/7 con escalamiento | 4 |
| PF-C04 | C | ¿Se registran y revisan los logs de acceso? | Sin logs | Logs sin revisión | Revisión mensual | SIEM con alertas | 4 |
| PF-C05 | C | ¿Existe segmentación de red para este servidor? | Red plana | VLAN básica | Firewall dedicado | Microsegmentación | 4 |

## Bloque D: Ciberseguridad (4 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PF-D01 | I | ¿El servidor tiene antivirus/antimalware actualizado? | Sin protección | Antivirus básico | EDR | EDR + XDR integrado | 4 |
| PF-D02 | C | ¿Los datos en reposo están cifrados? | Sin cifrado | Cifrado parcial | Cifrado completo | Cifrado + gestión de claves | 4 |
| PF-D03 | I | ¿Se realizan análisis de vulnerabilidades? | Nunca | Anualmente | Trimestralmente | Continuo automatizado | 4 |
| PF-D04 | D | ¿Existe protección contra ransomware específica? | Sin protección | Backups offline | Backups + detección | Protección multicapa | 5 |

## Bloque E: Exposición (3 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PF-E01 | C | ¿El servidor tiene servicios expuestos a Internet? | Totalmente expuesto | Parcialmente expuesto | Solo VPN | Solo red interna | 5 |
| PF-E02 | C | ¿Cuál es el nivel de acceso físico al servidor? | Acceso libre | Sala cerrada | Datacenter con control | Datacenter Tier III+ | 3 |
| PF-E03 | D | ¿Cuántas dependencias externas tiene el servidor? | Más de 10 | 5-10 | 2-4 | 0-1 | 3 |

---

# 💻 BANCO 2: SERVIDOR VIRTUAL (21 preguntas)

## Bloque A: Impacto (5 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PV-A01 | D | ¿Cuál es el tiempo máximo tolerable de interrupción (RTO) de la VM? | Más de 72 horas | 24-72 horas | 4-24 horas | Menos de 4 horas | 5 |
| PV-A02 | D | ¿Cuántos servicios o aplicaciones dependen de esta VM? | 1-2 servicios | 3-5 servicios | 6-10 servicios | Más de 10 servicios | 4 |
| PV-A03 | I | ¿Qué nivel de pérdida de datos es tolerable (RPO)? | Hasta 1 semana | Hasta 24 horas | Hasta 4 horas | Cero pérdida | 5 |
| PV-A04 | C | ¿Qué tipo de información procesa esta VM? | Pública | Interna | Confidencial | Altamente sensible | 5 |
| PV-A05 | D | ¿Esta VM forma parte de un cluster o granja de servidores? | VM aislada crítica | VM aislada no crítica | Parte de cluster | Cluster con auto-scaling | 4 |

## Bloque B: Continuidad (4 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PV-B01 | D | ¿Existe capacidad de migración en vivo (vMotion/Live Migration)? | No disponible | Disponible sin probar | Probado anualmente | Automatizado DRS/HA | 5 |
| PV-B02 | D | ¿Con qué frecuencia se realizan snapshots/backups de la VM? | Mensual o nunca | Semanal | Diario | Múltiples veces al día | 5 |
| PV-B03 | D | ¿Existe réplica de la VM en otro sitio/datacenter? | Sin réplica | Réplica manual | Réplica asíncrona | Réplica síncrona multi-sitio | 4 |
| PV-B04 | D | ¿El hypervisor tiene recursos reservados para esta VM? | Sin reservas | Reserva parcial | Reserva completa | Host dedicado | 3 |

## Bloque C: Controles (5 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PV-C01 | C | ¿Cómo se gestiona el acceso a la consola de la VM? | Sin control | Usuario/contraseña | Roles + auditoría | PAM + MFA + grabación | 5 |
| PV-C02 | I | ¿La imagen/template de la VM está hardened? | Instalación default | Configuración básica | CIS Benchmark parcial | CIS Benchmark completo | 4 |
| PV-C03 | D | ¿Existe monitoreo de recursos de la VM (CPU, RAM, disco)? | Sin monitoreo | Monitoreo básico | Alertas automáticas | AIOps con predicción | 4 |
| PV-C04 | I | ¿Con qué frecuencia se actualiza el SO de la VM? | Nunca/Raramente | Anualmente | Trimestralmente | Mensual automatizado | 5 |
| PV-C05 | C | ¿Se utilizan políticas de grupo o configuración centralizada? | Configuración manual | Scripts básicos | GPO/Ansible parcial | IaC completo (Terraform/Ansible) | 3 |

## Bloque D: Ciberseguridad (4 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PV-D01 | I | ¿La VM tiene agente de seguridad endpoint (EDR/XDR)? | Sin protección | Antivirus básico | EDR | XDR integrado con SOAR | 4 |
| PV-D02 | C | ¿Los discos virtuales están cifrados? | Sin cifrado | Cifrado storage | Cifrado VM individual | Cifrado + vTPM + SecureBoot | 4 |
| PV-D03 | C | ¿Existe segmentación de red virtual (NSX/micro-segmentación)? | Sin segmentación | VLANs básicas | Firewall distribuido | Zero Trust NSX-T | 4 |
| PV-D04 | I | ¿Se monitorea la integridad de archivos del sistema? | Sin monitoreo | Verificación manual | FIM básico | FIM + respuesta automática | 3 |

## Bloque E: Exposición (3 preguntas)

| ID | Dimensión | Pregunta | Opción 1 | Opción 2 | Opción 3 | Opción 4 | Peso |
|----|-----------|----------|----------|----------|----------|----------|------|
| PV-E01 | C | ¿La VM está en nube pública, privada o híbrida? | Nube pública sin controles | Nube pública con controles | Nube privada | On-premise aislado | 4 |
| PV-E02 | C | ¿La VM tiene interfaces de red expuestas a Internet? | IP pública directa | NAT con puertos abiertos | Solo a través de LB/WAF | Solo red privada | 5 |
| PV-E03 | D | ¿Cuántas VMs comparten el mismo host físico? | Más de 50 | 20-50 | 5-20 | Host dedicado | 3 |

---

# 🧮 Lógica de Cálculo de Riesgo

## Clasificación de Preguntas para Impacto

### Preguntas de IMPACTO DIRECTO (valor alto = impacto alto)
```
Bloque A completo: PF-A01 a PF-A05, PV-A01 a PV-A05
Bloque B (RTO/RPO): PF-B01, PF-B02, PV-B01, PV-B02
Bloque E (Exposición): PF-E01 a PF-E03, PV-E01 a PV-E03
```

### Preguntas de CONTROL (valor bajo = sin control = impacto alto)
Se INVIERTE la escala: Opción 1 (No) → Impacto 4
```
Bloque B (Procedimientos): PF-B03, PF-B04, PV-B03, PV-B04
Bloque C completo: PF-C01 a PF-C05, PV-C01 a PV-C05
Bloque D completo: PF-D01 a PF-D04, PV-D01 a PV-D04
```

## Fórmula MAGERIT v3

```
Riesgo Inherente = Probabilidad × Impacto

Donde:
- Probabilidad: 1-5 (calculada desde exposición e historial)
- Impacto: 1-5 (máximo de D, I, C)
- Riesgo: 1-25
```

## Umbrales de Clasificación

| Nivel | Rango | Color | Acción |
|-------|-------|-------|--------|
| CRÍTICO | ≥ 20 | 🔴 Rojo | Acción inmediata |
| ALTO | 12-19 | 🟠 Naranja | Plan urgente |
| MEDIO | 6-11 | 🟡 Amarillo | Monitoreo |
| BAJO | 3-5 | 🟢 Verde | Aceptable |
| MUY BAJO | 1-2 | 🔵 Azul | Mínimo |

---

# ✏️ Notas para Modificaciones

## Para agregar una pregunta:
1. Usar ID secuencial: `PF-X##` o `PV-X##`
2. Asignar Dimensión: D (Disponibilidad), I (Integridad), C (Confidencialidad)
3. Definir 4 opciones de menor a mayor madurez
4. Asignar Peso: 3-5

## Para cambiar comportamiento:
- Si la pregunta mide **impacto directo**: Opción 4 = mayor impacto
- Si la pregunta mide **controles**: Opción 1 (sin control) = mayor impacto

## Archivos a modificar:
- `init_proyecto.py` - Funciones `get_banco_preguntas_fisicas()` y `get_banco_preguntas_virtuales()`
- `services/magerit_engine.py` - Sets `PREGUNTAS_IMPACTO_DIRECTO` y `PREGUNTAS_CONTROL_INVERTIDO`

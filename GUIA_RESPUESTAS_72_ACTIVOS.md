# 📋 GUÍA DE RESPUESTAS PARA 72 ACTIVOS

## 🎯 ESTRATEGIA GENERAL

Tus 72 activos:
- 50 Servidores Virtuales
- 22 Servidores Físicos

Distribución objetivo:
- 45 activos CRÍTICOS (Criticidad ALTA)
- 12 activos IMPORTANTES (Criticidad MEDIA)
- 10 activos SECUNDARIOS (Criticidad BAJA)
- 5 activos NO CRÍTICOS (Criticidad NULA)

---

## 🔴 SERVIDORES CRÍTICOS (45 activos)

### Objetivo: Nivel de Impacto Alto → RTO bajo, RPO bajo, respuestas pesimistas

### 📌 Preguntas Obligatorias BIA/RTO/RPO

**Para TODOS los 45 activos críticos:**

```
BIA (Impacto al negocio): 5/5
RTO (Tiempo máximo inactividad): 1/5  (pocas horas tolerables)
RPO (Pérdida máxima de datos): 1/5  (pérdida mínima tolerada)
```

### 🔵 Disponibilidad - SERVIDORES VIRTUALES CRÍTICOS (30 activos)

```
PV-D-001: ¿Snapshots automatizados? → NO (0)
PV-D-002: ¿Alta disponibilidad HA? → NO (0)
PV-D-003: ¿Migración automática? → NO (0)
PV-D-004: ¿Recursos garantizados? → 1/5
PV-D-005: ¿Monitoreo tiempo real? → 1/5
PV-D-006: ¿Réplicas en otro datacenter? → NO (0)
PV-D-007: ¿Almacenamiento redundante? → NO (0)
PV-D-008: ¿Políticas DRS? → 1/5
```

### 🟢 Integridad - SERVIDORES VIRTUALES CRÍTICOS

```
PV-I-001: ¿Backups automatizados? → 1/5 (mínimo)
PV-I-002: ¿Backups completos (VM+datos)? → NO (0)
PV-I-003: ¿Snapshots en storage diferente? → NO (0)
PV-I-004: ¿Pruebas de restauración? → 1/5
PV-I-005: ¿Versionado de configuración? → NO (0)
PV-I-006: ¿Protección contra corrupción? → 1/5
```

### 🔴 Confidencialidad - SERVIDORES VIRTUALES CRÍTICOS

```
PV-C-001: ¿Discos cifrados? → NO (0)
PV-C-002: ¿Acceso hipervisor restringido? → 1/5
PV-C-003: ¿Red segmentada (VLANs)? → 1/5
PV-C-004: ¿Aislamiento entre VMs? → 1/5
PV-C-005: ¿Auditoría de accesos admin? → 1/5
PV-C-006: ¿Borrado seguro al eliminar? → 1/5
```

---

### 🔵 Disponibilidad - SERVIDORES FÍSICOS CRÍTICOS (15 activos)

```
PF-D-001: ¿Fuente redundante? → NO (0)
PF-D-002: ¿Sistema UPS? → NO (0)
PF-D-003: ¿Rack con refrigeración? → NO (0)
PF-D-004: ¿Mantenimiento preventivo? → 1/5
PF-D-005: ¿Piezas de repuesto? → NO (0)
PF-D-006: ¿Red redundante? → NO (0)
PF-D-007: ¿Servidor standby? → NO (0)
PF-D-008: ¿Detección de incendios? → NO (0)
PF-D-009: ¿Plan recuperación desastres? → 1/5
```

### 🟢 Integridad - SERVIDORES FÍSICOS CRÍTICOS

```
PF-I-001: ¿RAID implementado? → NO (0)
PF-I-002: ¿Backups periódicos? → 1/5
PF-I-003: ¿Backups en ubicación separada? → NO (0)
PF-I-004: ¿Verificación de backups? → 1/5
PF-I-005: ¿Monitoreo SMART? → NO (0)
PF-I-006: ¿Pruebas de restauración? → 1/5
```

### 🔴 Confidencialidad - SERVIDORES FÍSICOS CRÍTICOS

```
PF-C-001: ¿Acceso físico restringido? → 1/5
PF-C-002: ¿Videovigilancia? → NO (0)
PF-C-003: ¿Discos cifrados? → NO (0)
PF-C-004: ¿Registro de accesos físicos? → 1/5
PF-C-005: ¿Disposal seguro? → 1/5
```

---

## 🟡 SERVIDORES IMPORTANTES (12 activos - 8 Virtual + 4 Físico)

### 📌 BIA/RTO/RPO

```
BIA: 3/5 (impacto medio)
RTO: 3/5 (puede tolerar medio día)
RPO: 3/5 (pérdida moderada aceptable)
```

### Disponibilidad, Integridad, Confidencialidad

**Para todos (Virtual y Físico):**
- Respuestas 0/1: → Mezcla 50/50 (mitad SÍ, mitad NO)
- Respuestas 1-5: → 3/5 (medio)

**Ejemplo Virtual:**
```
PV-D-001: 0, PV-D-002: 1, PV-D-003: 0, PV-D-004: 3/5
PV-D-005: 3/5, PV-D-006: 1, PV-D-007: 0, PV-D-008: 3/5
```

---

## 🟢 SERVIDORES SECUNDARIOS (10 activos - 7 Virtual + 3 Físico)

### 📌 BIA/RTO/RPO

```
BIA: 2/5 (impacto bajo)
RTO: 4/5 (puede estar caído días)
RPO: 4/5 (pérdida de varios días tolerable)
```

### Disponibilidad, Integridad, Confidencialidad

**Para todos:**
- Respuestas 0/1: → Mayoría SÍ (1)
- Respuestas 1-5: → 4/5

**Ejemplo Virtual:**
```
PV-D-001: 1, PV-D-002: 1, PV-D-003: 1, PV-D-004: 4/5
PV-D-005: 4/5, PV-D-006: 1, PV-D-007: 1, PV-D-008: 4/5
```

---

## ⚪ SERVIDORES NO CRÍTICOS (5 activos - Todos Virtual)

### 📌 BIA/RTO/RPO

```
BIA: 1/5 (impacto nulo/mínimo)
RTO: 5/5 (puede estar caído semanas)
RPO: 5/5 (pérdida total tolerable)
```

### Disponibilidad, Integridad, Confidencialidad

**Para todos:**
- Respuestas 0/1: → Todos SÍ (1)
- Respuestas 1-5: → 5/5

**Ejemplo Virtual:**
```
PV-D-001: 1, PV-D-002: 1, PV-D-003: 1, PV-D-004: 5/5
PV-D-005: 5/5, PV-D-006: 1, PV-D-007: 1, PV-D-008: 5/5
PV-I-001 a PV-I-006: 5/5 o 1 (todos óptimos)
PV-C-001 a PV-C-006: 5/5 o 1 (todos protegidos)
```

---

## 📊 RESUMEN DE ASIGNACIÓN

### Servidores Virtuales (50 total)

| Criticidad | Cantidad | Patrón Respuestas |
|------------|----------|-------------------|
| 🔴 ALTA | 30 | BIA=5, RTO=1, RPO=1, resto 0 o 1/5 |
| 🟡 MEDIA | 8 | BIA=3, RTO=3, RPO=3, resto 3/5 o mix |
| 🟢 BAJA | 7 | BIA=2, RTO=4, RPO=4, resto 4/5 o 1 |
| ⚪ NULA | 5 | BIA=1, RTO=5, RPO=5, resto 5/5 o 1 |

### Servidores Físicos (22 total)

| Criticidad | Cantidad | Patrón Respuestas |
|------------|----------|-------------------|
| 🔴 ALTA | 15 | BIA=5, RTO=1, RPO=1, resto 0 o 1/5 |
| 🟡 MEDIA | 4 | BIA=3, RTO=3, RPO=3, resto 3/5 o mix |
| 🟢 BAJA | 3 | BIA=2, RTO=4, RPO=4, resto 4/5 o 1 |
| ⚪ NULA | 0 | N/A |

---

## 🎯 RESULTADO ESPERADO

Con estas respuestas:
- **45 activos** tendrán **alta criticidad** (BIA=5, controles débiles)
- **12 activos** tendrán **criticidad media**
- **10 activos** tendrán **criticidad baja**
- **5 activos** tendrán **criticidad nula**

En **Tab 9 (Madurez Inherente)**:
- Nivel esperado: **1 - Inicial** (5-10 puntos)
- Mayoría de activos en zona de riesgo alto

---

## 💡 TIPS DE INGRESO RÁPIDO

1. Ordena tus activos por nombre o ID
2. Los primeros 30 Virtual + 15 Físico: **Patrón Crítico**
3. Siguientes 8 Virtual + 4 Físico: **Patrón Medio**
4. Siguientes 7 Virtual + 3 Físico: **Patrón Bajo**
5. Últimos 5 Virtual: **Patrón Nulo**

Responde sistemáticamente:
- **Primero** las 3 preguntas BIA/RTO/RPO
- **Luego** las preguntas D (Disponibilidad)
- **Después** las preguntas I (Integridad)
- **Finalmente** las preguntas C (Confidencialidad)

# ANÁLISIS DE RIESGO POR CONCENTRACIÓN - PROYECTO TITA

## Documento de Decisión Arquitectónica (ADR)

**Fecha**: 25 Enero 2026  
**Autor**: Arquitecto de Ciberseguridad  
**Estado**: APROBADO

---

## 1. CONTEXTO

### 1.1 Situación Actual
- El proyecto TITA evalúa riesgos de activos TI usando MAGERIT v3
- Existen dos tipos de activos: `Servidor Físico` y `Servidor Virtual`
- **Actualmente NO existe relación de dependencia** entre activos virtuales y hosts físicos
- Si un host físico falla, todos los activos virtuales que dependen de él fallan (blast radius)

### 1.2 Problema
El sistema no refleja el **riesgo por concentración**:
- Un host con 10 VMs críticas tiene mayor impacto que uno con 1 VM
- La falla del host es un **punto único de falla (SPOF)**
- El riesgo individual de cada VM no considera su dependencia del host

### 1.3 Objetivo
Implementar cálculo de riesgo por concentración que:
- Sea coherente con MAGERIT v3
- Refleje correctamente el impacto cascada
- Sea defendible académicamente
- Sea visualizable en dashboards

---

## 2. ANÁLISIS DE VARIANTES

### 2.1 Variante 1 — Ajuste solo en Disponibilidad

**Descripción**: El riesgo por concentración incrementa únicamente el impacto en Disponibilidad.

**Fórmula**:
```
Impacto_D_Ajustado = min(5, Impacto_D + Factor_Concentración)
Factor_Concentración = floor(num_vms_dependientes / 3)
```

**Ventajas**:
- ✅ Conservador y alineado con MAGERIT (la concentración afecta principalmente D)
- ✅ Simple de implementar
- ✅ Fácil de explicar

**Desventajas**:
- ❌ Ignora que la concentración también afecta I/C (datos en VMs)
- ❌ No considera criticidad individual de cada VM
- ❌ Limitado para análisis avanzados

**Puntuación**: ⭐⭐⭐ (3/5)

---

### 2.2 Variante 2 — Ajuste mixto Impacto + Probabilidad

**Descripción**: Incrementa Impacto (efecto cascada) y Probabilidad (complejidad operativa).

**Fórmula**:
```
Impacto_Ajustado = min(5, Impacto_Base × (1 + 0.1 × num_vms))
Probabilidad_Ajustada = min(5, Probabilidad_Base + floor(num_vms / 5))
```

**Ventajas**:
- ✅ Reconoce que más VMs = más complejidad operativa = más probabilidad de falla
- ✅ Equilibrio entre teoría y práctica

**Desventajas**:
- ❌ Mezcla conceptos (la probabilidad del host no cambia por tener más VMs)
- ❌ Difícil de justificar en MAGERIT puro
- ❌ Puede inflar artificialmente la probabilidad

**Puntuación**: ⭐⭐ (2/5)

---

### 2.3 Variante 3 — Blast Radius ponderado por criticidad

**Descripción**: Cada VM aporta peso según su criticidad; el impacto del host depende de la suma.

**Fórmula**:
```
Blast_Radius = Σ(Criticidad_VM × Peso_VM)
Criticidad_VM = max(Impacto_D, Impacto_I, Impacto_C) de cada VM
Factor_Concentración = min(5, ceil(Blast_Radius / Umbral))
Impacto_Host_Ajustado = max(Impacto_Base, Factor_Concentración)
```

**Ventajas**:
- ✅ Prioriza hosts con VMs críticas
- ✅ Permite comparar hosts objetivamente
- ✅ Alineado con enfoque basado en impacto de MAGERIT

**Desventajas**:
- ❌ Requiere que todas las VMs estén evaluadas primero
- ❌ Más complejo de implementar
- ❌ Depende de umbral configurable

**Puntuación**: ⭐⭐⭐⭐ (4/5)

---

### 2.4 Variante 4 — Herencia de riesgo MAGERIT

**Descripción**: El riesgo del host se propaga a las VMs (herencia hacia abajo).

**Fórmula**:
```
Riesgo_VM_Final = max(Riesgo_VM_Propio, Riesgo_Host × Factor_Herencia)
Factor_Herencia = 0.8 (el host transfiere 80% de su riesgo)
```

**Ventajas**:
- ✅ Modelo jerárquico formal de MAGERIT
- ✅ Las VMs reflejan el riesgo de su infraestructura base
- ✅ Justificable académicamente

**Desventajas**:
- ❌ Una VM segura puede tener riesgo alto solo por su host
- ❌ Puede ser contra-intuitivo para usuarios
- ❌ No refleja el impacto hacia arriba (VM crítica → host crítico)

**Puntuación**: ⭐⭐⭐ (3/5)

---

## 3. DECISIÓN: MODELO HÍBRIDO (V3 + V4)

### 3.1 Modelo Seleccionado

Combinación de **Variante 3 (Blast Radius) + Variante 4 (Herencia)** con flujo bidireccional:

1. **Hacia arriba (VM → Host)**: El host hereda impacto de sus VMs (blast radius)
2. **Hacia abajo (Host → VM)**: Las VMs heredan riesgo del host (dependencia)

### 3.2 Justificación

| Criterio | Modelo Híbrido |
|----------|----------------|
| Alineación MAGERIT | ✅ Propagación de impacto (Libro II, Cap 4) |
| Facilidad de implementación | ✅ Moderada (dos fases) |
| Claridad en dashboards | ✅ Muestra SPOF y dependencias |
| Justificación académica | ✅ Modelo de herencia + agregación |
| Comparabilidad temporal | ✅ Métricas consistentes |

### 3.3 Fórmulas Finales

#### Fase 1: Cálculo de Blast Radius del Host
```
Para cada Host H con VMs dependientes {VM1, VM2, ..., VMn}:

Blast_Radius_H = Σ(Criticidad_VMi × Peso_Dependencia_VMi)

Donde:
- Criticidad_VMi = max(D, I, C) del activo virtual i
- Peso_Dependencia = 1.0 (total) | 0.5 (parcial) | 0.0 (ninguna)

Factor_Concentración = min(4, floor(Blast_Radius / 5))

Impacto_D_Host_Ajustado = min(5, Impacto_D_Host + Factor_Concentración)
```

#### Fase 2: Herencia de Riesgo (Host → VM)
```
Para cada VM que depende del Host H:

Riesgo_Heredado = Riesgo_Host × 0.7  (70% de herencia)

Riesgo_VM_Final = max(Riesgo_VM_Propio, Riesgo_Heredado)

Nivel_Riesgo_VM = clasificar(Riesgo_VM_Final)
```

#### Fase 3: Riesgo Residual con Concentración
```
Efectividad_Mitigación = Efectividad_Controles × (1 - 0.1 × Factor_Concentración)
Riesgo_Residual = Riesgo_Inherente × (1 - Efectividad_Mitigación × 0.8)
```

### 3.4 Atributos Involucrados

**Del Host (Servidor Físico)**:
- Impacto DIC propio (del cuestionario)
- Probabilidad propia
- Lista de VMs dependientes
- Factor de concentración calculado

**Del Activo Virtual**:
- Impacto DIC propio
- Probabilidad propia
- Host del que depende (ID_Host)
- Tipo de dependencia (total/parcial)
- Riesgo heredado del host

### 3.5 Nuevos Campos en Base de Datos

```sql
-- Agregar a INVENTARIO_ACTIVOS
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN ID_Host TEXT;
ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Tipo_Dependencia TEXT DEFAULT 'total';

-- Nueva tabla para resultados de concentración
CREATE TABLE RESULTADOS_CONCENTRACION (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Evaluacion TEXT,
    ID_Host TEXT,
    Nombre_Host TEXT,
    Num_VMs_Dependientes INTEGER,
    Blast_Radius REAL,
    Factor_Concentracion INTEGER,
    Impacto_D_Original INTEGER,
    Impacto_D_Ajustado INTEGER,
    Riesgo_Original REAL,
    Riesgo_Ajustado REAL,
    VMs_Criticas TEXT,  -- JSON con lista de VMs críticas
    Fecha_Calculo TEXT,
    UNIQUE(ID_Evaluacion, ID_Host)
);
```

---

## 4. IMPLEMENTACIÓN

### 4.1 Servicios a Crear
- `concentration_risk_service.py`: Cálculo de riesgo por concentración

### 4.2 Modificaciones
- `magerit_engine.py`: Integrar herencia de riesgo
- `database_service.py`: Nuevas tablas
- `app_final.py`: UI para asignar host a VM
- `dashboard_magerit.py`: Visualización de SPOF

### 4.3 Dashboard
- Ranking de hosts por blast radius
- Mapa de dependencias
- Alerta de puntos únicos de falla

---

## 5. CRITERIOS DE ACEPTACIÓN

- [ ] El sistema identifica hosts como SPOF cuando tienen >3 VMs críticas
- [ ] El riesgo de VMs refleja dependencia del host
- [ ] El modelo es coherente con MAGERIT v3
- [ ] Los resultados son visibles en dashboard
- [ ] Se puede comparar entre evaluaciones

---

*Documento aprobado para implementación*

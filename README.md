# Comparativa de Planificadores PDDL

Comparativa de planificadores automaticos sobre dominios clasicos PDDL: **Blocksworld** (IPC 2000) y **Gripper** (IPC 1998).

Actividad 3 — Razonamiento y Planificacion Automatica, UNIR.

## Planificadores evaluados

| Configuracion | Planificador | Algoritmo | Heuristica | Resueltos |
|--------------|-------------|-----------|------------|-----------|
| FD-LAMA | Fast Downward (Docker) | LAMA multi-cola | Landmarks + FF | **10/10** |
| FD-GBFS-FF | Fast Downward (Docker) | GBFS | FF | **10/10** |
| PP-GBF-FF | pyperplan (Python) | GBF | h_FF | **10/10** |
| FD-ASTAR-LM | Fast Downward (Docker) | A* | LM-Cut | 6/10 |
| PP-ASTAR-ADD | pyperplan (Python) | A* | h_add | 6/10 |
| PP-ASTAR-FF | pyperplan (Python) | A* | h_FF | 5/10 |

## Estructura del proyecto

```
actividad3/
├── articulo.md          # Articulo completo en formato markdown
├── domains/
│   ├── blocksworld/     # Dominio + 5 instancias (5-17 bloques)
│   └── gripper/         # Dominio + 5 instancias (4-30 pelotas)
├── src/
│   ├── run_pyperplan.py       # Ejecucion paralela de pyperplan
│   ├── run_fast_downward.py   # Ejecucion paralela de Fast Downward (Docker)
│   └── analyze_results.py     # Generacion de tablas y figuras
├── results/             # Resultados JSON/CSV de 60 experimentos
└── figures/             # 6 graficas generadas con matplotlib
```

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes)
- Docker Desktop (para Fast Downward)

## Configuracion de Docker

Fast Downward se ejecuta dentro de un contenedor Docker basado en Ubuntu. Es necesario instalar Docker Desktop antes de ejecutar los experimentos de Fast Downward.

### 1. Instalar Docker Desktop

- **macOS**: Descargar desde https://www.docker.com/products/docker-desktop/ e instalar. En Apple Silicon (M1/M2/M3/M4) la imagen se ejecuta con emulacion x86 automaticamente via Rosetta.
- **Windows**: Descargar Docker Desktop desde la misma URL. Requiere WSL2 habilitado.
- **Linux**: Instalar Docker Engine siguiendo https://docs.docker.com/engine/install/

### 2. Verificar instalacion

```bash
docker --version
# Docker version 28.x.x

docker run --rm hello-world
# Deberia mostrar "Hello from Docker!"
```

### 3. Descargar imagen de Fast Downward

```bash
docker pull aibasel/downward:latest
```

La imagen ocupa aproximadamente 500 MB. Contiene el planificador Fast Downward precompilado sobre Ubuntu.

### 4. Verificar que funciona

```bash
# Prueba rapida con un problema simple
docker run --rm -v "$(pwd)/domains:/data:ro" aibasel/downward \
  --alias lama-first \
  /data/blocksworld/domain.pddl \
  /data/blocksworld/instances/instance-4.pddl
```

Deberia mostrar `Solution found!` con un plan de 12 pasos.

> **Nota:** Cada ejecucion de Docker tiene un overhead de ~2 segundos por la inicializacion del contenedor. Los tiempos reportados en el articulo incluyen este overhead. El script `run_fast_downward.py` limita cada contenedor a 4 GB de memoria (`--memory=4g`).

## Ejecucion

```bash
# 1. Instalar dependencias Python (pyperplan, matplotlib, pandas, etc.)
uv sync

# 2. Ejecutar pyperplan (no requiere Docker)
uv run python src/run_pyperplan.py

# 3. Ejecutar Fast Downward (requiere Docker corriendo)
uv run python src/run_fast_downward.py

# 4. Generar tablas y figuras
uv run python src/analyze_results.py
```

Los scripts ejecutan los planificadores en paralelo (6 workers para pyperplan, 4 para Fast Downward) con timeouts de 60s y 120s respectivamente.

## Resultados principales

- **FD-LAMA** es la configuracion mas robusta: resuelve todos los problemas en ~3.3s de media.
- Las configuraciones optimas (A*) no escalan mas alla de 12 bloques / 10 pelotas.
- pyperplan es competitivo en problemas pequenos pero se degrada rapidamente.
- La heuristica tiene mas impacto en el rendimiento que la implementacion del planificador.

## Referencias

- Helmert, M. (2006). The Fast Downward planning system. *JAIR*, 26, 191-246.
- Richter, S. y Westphal, M. (2010). The LAMA planner. *JAIR*, 39, 127-177.
- Alkhazraji, Y. et al. (2016). pyperplan. https://github.com/aibasel/pyperplan
- Potassco. (2020). PDDL Instances. https://github.com/potassco/pddl-instances

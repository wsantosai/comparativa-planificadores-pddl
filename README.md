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
- Docker (para Fast Downward)

## Ejecucion

```bash
# Instalar dependencias
uv sync

# Descargar imagen de Fast Downward
docker pull aibasel/downward:latest

# Ejecutar planificadores
uv run python src/run_pyperplan.py
uv run python src/run_fast_downward.py

# Generar tablas y figuras
uv run python src/analyze_results.py
```

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

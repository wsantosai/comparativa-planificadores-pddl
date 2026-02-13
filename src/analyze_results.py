"""
Script para analizar resultados y generar tablas y figuras para el articulo.
Lee los JSON de resultados de pyperplan y Fast Downward, genera:
- Tablas en formato markdown
- Figuras con matplotlib (tiempo, nodos, longitud de plan)
"""

import json
import os

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")


def load_results():
    """Cargar todos los resultados de ambos planificadores."""
    all_results = []

    pp_file = os.path.join(RESULTS_DIR, "pyperplan_results.json")
    if os.path.exists(pp_file):
        with open(pp_file) as f:
            all_results.extend(json.load(f))

    fd_file = os.path.join(RESULTS_DIR, "fast_downward_results.json")
    if os.path.exists(fd_file):
        with open(fd_file) as f:
            all_results.extend(json.load(f))

    return pd.DataFrame(all_results)


def generate_tables(df):
    """Generar tablas en formato markdown."""
    tables = {}

    for domain in df["domain"].unique():
        domain_df = df[df["domain"] == domain]

        # Tabla de tiempo y longitud
        pivot_time = domain_df.pivot_table(
            index=["problem", "complexity"],
            columns="planner",
            values="time",
            aggfunc="first",
        )
        pivot_length = domain_df.pivot_table(
            index=["problem", "complexity"],
            columns="planner",
            values="plan_length",
            aggfunc="first",
        )
        pivot_nodes = domain_df.pivot_table(
            index=["problem", "complexity"],
            columns="planner",
            values="nodes_expanded",
            aggfunc="first",
        )

        tables[f"{domain}_time"] = pivot_time
        tables[f"{domain}_length"] = pivot_length
        tables[f"{domain}_nodes"] = pivot_nodes

    return tables


def plot_time_comparison(df, domain, output_path):
    """Grafica de tiempo vs complejidad para un dominio."""
    domain_df = df[df["domain"] == domain]

    fig, ax = plt.subplots(figsize=(10, 6))

    markers = ["o", "s", "^", "D", "v", "p"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    for i, planner in enumerate(sorted(domain_df["planner"].unique())):
        planner_df = domain_df[domain_df["planner"] == planner].sort_values("complexity")
        ax.plot(
            planner_df["complexity"],
            planner_df["time"],
            marker=markers[i % len(markers)],
            color=colors[i % len(colors)],
            label=planner,
            linewidth=2,
            markersize=8,
        )

    domain_label = "Bloques" if domain == "blocksworld" else "Pelotas"
    ax.set_xlabel(f"Numero de {domain_label}", fontsize=12)
    ax.set_ylabel("Tiempo de ejecucion (s)", fontsize=12)
    ax.set_title(f"Tiempo de ejecucion vs. complejidad — {domain.capitalize()}", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Figura guardada: {output_path}")


def plot_nodes_comparison(df, domain, output_path):
    """Grafica de nodos expandidos vs complejidad."""
    domain_df = df[df["domain"] == domain].dropna(subset=["nodes_expanded"])

    fig, ax = plt.subplots(figsize=(10, 6))

    markers = ["o", "s", "^", "D", "v", "p"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    for i, planner in enumerate(sorted(domain_df["planner"].unique())):
        planner_df = domain_df[domain_df["planner"] == planner].sort_values("complexity")
        ax.plot(
            planner_df["complexity"],
            planner_df["nodes_expanded"],
            marker=markers[i % len(markers)],
            color=colors[i % len(colors)],
            label=planner,
            linewidth=2,
            markersize=8,
        )

    domain_label = "Bloques" if domain == "blocksworld" else "Pelotas"
    ax.set_xlabel(f"Numero de {domain_label}", fontsize=12)
    ax.set_ylabel("Nodos expandidos", fontsize=12)
    ax.set_title(f"Nodos expandidos vs. complejidad — {domain.capitalize()}", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_yscale("log")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Figura guardada: {output_path}")


def plot_plan_length_comparison(df, domain, output_path):
    """Grafica de longitud del plan vs complejidad."""
    domain_df = df[df["domain"] == domain].dropna(subset=["plan_length"])

    fig, ax = plt.subplots(figsize=(10, 6))

    markers = ["o", "s", "^", "D", "v", "p"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    for i, planner in enumerate(sorted(domain_df["planner"].unique())):
        planner_df = domain_df[domain_df["planner"] == planner].sort_values("complexity")
        ax.plot(
            planner_df["complexity"],
            planner_df["plan_length"],
            marker=markers[i % len(markers)],
            color=colors[i % len(colors)],
            label=planner,
            linewidth=2,
            markersize=8,
        )

    # Para Gripper, mostrar la solucion optima teorica
    if domain == "gripper":
        complexities = sorted(domain_df["complexity"].unique())
        optimal = [3 * n + 1 for n in complexities]
        ax.plot(
            complexities, optimal,
            "k--", label="Optimo teorico (3n+1)",
            linewidth=2, alpha=0.7,
        )

    domain_label = "Bloques" if domain == "blocksworld" else "Pelotas"
    ax.set_xlabel(f"Numero de {domain_label}", fontsize=12)
    ax.set_ylabel("Longitud del plan (acciones)", fontsize=12)
    ax.set_title(f"Longitud del plan vs. complejidad — {domain.capitalize()}", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Figura guardada: {output_path}")


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)

    df = load_results()
    if df.empty:
        print("No hay resultados. Ejecuta primero run_pyperplan.py y/o run_fast_downward.py")
        return

    print(f"Cargados {len(df)} resultados")
    print(f"Planificadores: {df['planner'].unique().tolist()}")
    print(f"Dominios: {df['domain'].unique().tolist()}")
    print()

    # Generar tablas
    tables = generate_tables(df)
    for name, table in tables.items():
        print(f"\n=== {name.upper()} ===")
        print(table.to_markdown())

    # Generar figuras
    for domain in df["domain"].unique():
        plot_time_comparison(
            df, domain,
            os.path.join(FIGURES_DIR, f"tiempo_{domain}.png"),
        )
        plot_nodes_comparison(
            df, domain,
            os.path.join(FIGURES_DIR, f"nodos_{domain}.png"),
        )
        plot_plan_length_comparison(
            df, domain,
            os.path.join(FIGURES_DIR, f"plan_length_{domain}.png"),
        )

    # Resumen general
    print("\n\n=== RESUMEN GENERAL ===")
    summary = df.groupby("planner").agg(
        problemas_resueltos=("solved", "sum"),
        tiempo_medio=("time", "mean"),
        plan_medio=("plan_length", "mean"),
    ).round(4)
    print(summary.to_markdown())

    # Guardar resumen como CSV
    df.to_csv(os.path.join(RESULTS_DIR, "all_results.csv"), index=False)
    print(f"\nCSV completo guardado en {os.path.join(RESULTS_DIR, 'all_results.csv')}")


if __name__ == "__main__":
    main()

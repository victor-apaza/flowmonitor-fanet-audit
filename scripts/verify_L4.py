#!/usr/bin/env python3
"""
Verificación L4: PDR Overestimates Application-Level Reliability
Reconstruido a partir del Anexo D del documento de limitaciones.

Compara pdr_layer3 (flowmonitor_pdr_weighted) con pdr_application (slam_pdr).
"""
import json
import sys
import glob
import os
import csv

def analyze_run(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    pdr_layer3 = data.get('flowmonitor_pdr_weighted', 0) * 100  # a %
    pdr_app = data.get('slam_pdr', 0) * 100  # a %
    gap = pdr_layer3 - pdr_app  # en pp

    return {
        'pdr_layer3': pdr_layer3,
        'pdr_app': pdr_app,
        'gap_pp': gap,
    }

def save_results(results, output_file):
    """Guarda los resultados en un archivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'pdr_layer3', 'pdr_app', 'gap_pp'])
        writer.writeheader()
        writer.writerows(results)

def main():
    base_dir = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    json_files = sorted(glob.glob(os.path.join(base_dir, '*', 'metrics_*.json')))
    if not json_files:
        print(f"No se encontraron JSON en {base_dir}")
        sys.exit(1)
    print(f"{'Corrida':<40} {'PDR layer3':>12} {'PDR app':>10} {'Gap pp':>10}")
    print("-" * 75)
    results = []
    for json_file in json_files:
        run_name = os.path.basename(os.path.dirname(json_file))
        r = analyze_run(json_file)
        r['run_name'] = run_name
        results.append(r)
        print(f"{run_name:<40} {r['pdr_layer3']:>11.2f}% {r['pdr_app']:>9.2f}% "
              f"{r['gap_pp']:>+10.2f}")
    print("-" * 75)
    # Resumen por N
    print("\nResumen por N (media de las 5 seeds):")
    print(f"{'N':>3} {'PDR layer3':>12} {'PDR app':>10} {'Gap pp':>10}")
    print("-" * 40)
    for n in [9, 12, 18, 24, 30]:
        runs_n = [r for r in results if f'_N{n}_' in r['run_name']]
        if runs_n:
            l3 = sum(r['pdr_layer3'] for r in runs_n) / len(runs_n)
            app = sum(r['pdr_app'] for r in runs_n) / len(runs_n)
            gap = sum(r['gap_pp'] for r in runs_n) / len(runs_n)
            print(f"{n:>3} {l3:>11.2f}% {app:>9.2f}% {gap:>+10.2f}")
    # Media global
    mean_gap = sum(r['gap_pp'] for r in results) / len(results)
    print("-" * 40)
    print(f"{'Global':>3} {'':>12} {'':>10} {mean_gap:>+10.2f}")
    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L4/L4_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

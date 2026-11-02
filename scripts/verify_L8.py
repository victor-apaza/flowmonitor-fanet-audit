#!/usr/bin/env python3
"""
Verificación L8: lostPackets is uint32_t (Overflow Risk)
Reconstruido a partir del reporte L8.

lostPackets no está directamente en el JSON. Se aproxima como tx - rx
(cota superior). Se compara con el límite de uint32_t.
"""
import json
import sys
import glob
import os
import csv

UINT32_MAX = 4294967295  # 2^32 - 1

def analyze_run(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    tx = data.get('flowmonitor_txPackets', 0)
    rx = data.get('flowmonitor_rxPackets', 0)
    lost = tx - rx  # Aproximación (cota superior)
    pct_limit = (lost / UINT32_MAX) * 100 if UINT32_MAX > 0 else 0
    margin = UINT32_MAX / lost if lost > 0 else float('inf')

    return {
        'tx': int(tx),
        'rx': int(rx),
        'lost_approx': int(lost),
        'pct_limit': pct_limit,
        'margin': margin,
    }

def save_results(results, output_file):
    """Guarda los resultados en un archivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'tx', 'rx', 'lost_approx',
                                                'pct_limit', 'margin'])
        writer.writeheader()
        writer.writerows(results)

def main():
    base_dir = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    json_files = sorted(glob.glob(os.path.join(base_dir, '*', 'metrics_*.json')))
    if not json_files:
        print(f"No se encontraron JSON en {base_dir}")
        sys.exit(1)
    print(f"{'Corrida':<40} {'TX packets':>12} {'RX packets':>12} {'Lost approx':>12} {'% límite':>10} {'Margen':>10}")
    print("-" * 100)
    results = []
    for json_file in json_files:
        run_name = os.path.basename(os.path.dirname(json_file))
        r = analyze_run(json_file)
        r['run_name'] = run_name
        results.append(r)
        margin_str = f"{r['margin']:.0f}x" if r['margin'] != float('inf') else "inf"
        print(f"{run_name:<40} {r['tx']:>12,} {r['rx']:>12,} {r['lost_approx']:>12,} "
              f"{r['pct_limit']:>9.4f}% {margin_str:>10}")
    print("-" * 100)
    # Resumen por N
    print("\nResumen por N (media de las 5 seeds):")
    print(f"{'N':>3} {'Lost approx':>12} {'% límite':>10} {'Margen':>10}")
    print("-" * 40)
    for n in [9, 12, 18, 24, 30]:
        runs_n = [r for r in results if f'_N{n}_' in r['run_name']]
        if runs_n:
            lost = sum(r['lost_approx'] for r in runs_n) / len(runs_n)
            pct = sum(r['pct_limit'] for r in runs_n) / len(runs_n)
            margin = sum(r['margin'] for r in runs_n if r['margin'] != float('inf')) / len(runs_n)
            print(f"{n:>3} {lost:>12,.0f} {pct:>9.4f}% {margin:>9.0f}x")
    # Máximo absoluto
    max_run = max(results, key=lambda x: x['lost_approx'])
    print("-" * 40)
    print(f"Máximo absoluto: {max_run['lost_approx']:,} ({max_run['run_name']})")
    print(f"% del límite: {max_run['pct_limit']:.4f}%")
    print(f"Margen de seguridad: {max_run['margin']:.0f}x")
    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L8/L8_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

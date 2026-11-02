#!/usr/bin/env python3
"""
Verificación L5: In-Flight Packets Bias PDR at Simulation End
Reconstruido a partir del Anexo D del documento de limitaciones.

Compara las 25 corridas con MaxPerHopDelay=10s (AODV) vs 2s (Exp_L12).
"""
import json
import sys
import glob
import os
import csv

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return json.load(f)

def analyze_run(json_10s, json_2s):
    d10 = load_json(json_10s)
    d2 = load_json(json_2s)
    if d10 is None or d2 is None:
        return None

    pdr_10s = d10.get('flowmonitor_pdr_weighted', 0) * 100
    pdr_2s = d2.get('flowmonitor_pdr_weighted', 0) * 100
    delta_pdr = pdr_10s - pdr_2s  # en pp

    # Lost packets (aproximado como tx - rx)
    tx_10s = d10.get('flowmonitor_txPackets', 0)
    rx_10s = d10.get('flowmonitor_rxPackets', 0)
    lost_10s = tx_10s - rx_10s

    tx_2s = d2.get('flowmonitor_txPackets', 0)
    rx_2s = d2.get('flowmonitor_rxPackets', 0)
    lost_2s = tx_2s - rx_2s

    delta_lost = lost_2s - lost_10s

    return {
        'pdr_10s': pdr_10s,
        'pdr_2s': pdr_2s,
        'delta_pdr': delta_pdr,
        'lost_10s': lost_10s,
        'lost_2s': lost_2s,
        'delta_lost': delta_lost,
    }

def save_results(results, output_file):
    """Guarda los resultados en un archivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'pdr_10s', 'pdr_2s',
                                                'delta_pdr', 'lost_10s', 'lost_2s',
                                                'delta_lost'])
        writer.writeheader()
        writer.writerows(results)

def main():
    base_10s = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    base_2s = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/Exp_L12_MaxPerHopDelay2s')

    json_files_10s = sorted(glob.glob(os.path.join(base_10s, '*', 'metrics_*.json')))
    if not json_files_10s:
        print(f"No se encontraron JSON en {base_10s}")
        sys.exit(1)

    print(f"{'Corrida':<40} {'PDR 10s':>9} {'PDR 2s':>9} {'Δ PDR':>9} {'Δ Lost':>12}")
    print("-" * 85)
    results = []
    for json_10s in json_files_10s:
        run_name = os.path.basename(os.path.dirname(json_10s))
        json_2s = os.path.join(base_2s, run_name, os.path.basename(json_10s))
        r = analyze_run(json_10s, json_2s)
        if r is None:
            print(f"{run_name:<40} {'SKIP':>9} {'SKIP':>9} {'SKIP':>9} {'SKIP':>12}")
            continue
        r['run_name'] = run_name
        results.append(r)
        print(f"{run_name:<40} {r['pdr_10s']:>8.2f}% {r['pdr_2s']:>8.2f}% "
              f"{r['delta_pdr']:>+9.4f} {r['delta_lost']:>+12,.0f}")
    print("-" * 85)

    # Resumen por N
    print("\nResumen por N (media de las 5 seeds):")
    print(f"{'N':>3} {'Δ PDR pp':>10} {'Δ Lost':>12}")
    print("-" * 30)
    for n in [9, 12, 18, 24, 30]:
        runs_n = [r for r in results if f'_N{n}_' in r['run_name']]
        if runs_n:
            dpdr = sum(r['delta_pdr'] for r in runs_n) / len(runs_n)
            dlost = sum(r['delta_lost'] for r in runs_n) / len(runs_n)
            print(f"{n:>3} {dpdr:>+10.4f} {dlost:>+12,.0f}")
    # Media global
    mean_dpdr = sum(r['delta_pdr'] for r in results) / len(results)
    print("-" * 30)
    print(f"{'Global':>3} {mean_dpdr:>+10.4f}")

    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L5/L5_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

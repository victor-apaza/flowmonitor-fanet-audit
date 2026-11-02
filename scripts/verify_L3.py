#!/usr/bin/env python3
"""
Verificación L3: WiFi Queue Drops Not Reported to FlowMonitor
Reconstruido a partir del Anexo C del documento de limitaciones.

Nota: flowmonitor_lostPackets no está directamente en el JSON.
Se aproxima como txPackets - rxPackets (cota superior).
"""
import json
import sys
import glob
import os
import csv

def analyze_run(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    # FlowMonitor lostPackets (aproximado como tx - rx)
    tx = data.get('flowmonitor_txPackets', 0)
    rx = data.get('flowmonitor_rxPackets', 0)
    fm_drops = tx - rx  # Aproximación (cota superior)

    # QueueMonitor
    qm_queue = data.get('queuemonitor_queueDrops', 0)
    qm_phy = data.get('queuemonitor_phyDrops', 0)
    qm_total = data.get('queuemonitor_totalDrops', 0)

    # Discrepancia
    discrepancy = qm_total - fm_drops
    pct_unreported = (discrepancy / qm_total * 100) if qm_total > 0 else 0

    return {
        'fm_drops': fm_drops,
        'qm_queue': qm_queue,
        'qm_phy': qm_phy,
        'qm_total': qm_total,
        'discrepancy': discrepancy,
        'pct_unreported': pct_unreported,
    }

def save_results(results, output_file):
    """Guarda los resultados en un archivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'fm_drops', 'qm_queue',
                                                'qm_phy', 'qm_total', 'discrepancy',
                                                'pct_unreported'])
        writer.writeheader()
        writer.writerows(results)

def main():
    base_dir = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    json_files = sorted(glob.glob(os.path.join(base_dir, '*', 'metrics_*.json')))
    if not json_files:
        print(f"No se encontraron JSON en {base_dir}")
        sys.exit(1)
    print(f"{'Corrida':<40} {'FM drops':>12} {'QM total':>12} {'Discrep.':>12} {'% no rep.':>10}")
    print("-" * 95)
    results = []
    for json_file in json_files:
        run_name = os.path.basename(os.path.dirname(json_file))
        r = analyze_run(json_file)
        r['run_name'] = run_name
        results.append(r)
        print(f"{run_name:<40} {r['fm_drops']:>12,.0f} {r['qm_total']:>12,.0f} "
              f"{r['discrepancy']:>12,.0f} {r['pct_unreported']:>9.1f}%")
    print("-" * 95)
    # Medias por N
    print("\nResumen por N (media de las 5 seeds):")
    print(f"{'N':>3} {'FM drops':>12} {'QM total':>12} {'Discrep.':>12} {'% no rep.':>10}")
    print("-" * 65)
    for n in [9, 12, 18, 24, 30]:
        runs_n = [r for r in results if f'_N{n}_' in r['run_name']]
        if runs_n:
            fm = sum(r['fm_drops'] for r in runs_n) / len(runs_n)
            qm = sum(r['qm_total'] for r in runs_n) / len(runs_n)
            disc = sum(r['discrepancy'] for r in runs_n) / len(runs_n)
            pct = sum(r['pct_unreported'] for r in runs_n) / len(runs_n)
            print(f"{n:>3} {fm:>12,.0f} {qm:>12,.0f} {disc:>12,.0f} {pct:>9.1f}%")
    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L3/L3_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

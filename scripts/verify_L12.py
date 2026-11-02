#!/usr/bin/env python3
"""
Verificación L12: ReportForwarding() Discards Events
Analiza los logs de las 7 simulaciones (N=30, seed=42, duraciones 20-180s)
y extrae el timestamp de las líneas '📊 [TIME=X.Xs]' que imprime MonitorFlowStats.
"""
import os
import re
import sys
import csv

LOG_DIR = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/L12_logs')
OUTPUT_FILE = os.path.expanduser('~/flowmonitor-fanet-audit/results/L12/L12_results.csv')

DURATIONS = [20, 40, 50, 80, 100, 120, 180]

# Patrón para las líneas de MonitorFlowStats: "📊 [TIME=19.0s] PDR=..."
TIME_RE = re.compile(r'TIME=(\d+\.?\d*)s')

def analyze_log(log_file, duration):
    """Analiza un log línea por línea y extrae el tiempo de los descartes."""
    if not os.path.exists(log_file):
        return None

    discards = 0
    forward = 0
    last_tx = 0
    flow_ids = set()
    timestamps = []
    last_seen_ts = None

    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            # Actualizar el último timestamp visto de las líneas TIME=X.Xs
            m = TIME_RE.search(line)
            if m:
                try:
                    last_seen_ts = float(m.group(1))
                except ValueError:
                    pass

            # Procesar descartes
            if 'not known to be transmitted' in line:
                discards += 1
                if 'forward report' in line:
                    forward += 1
                elif 'last-tx report' in line:
                    last_tx += 1
                m = re.search(r'flowId=(\d+)', line)
                if m:
                    flow_ids.add(m.group(1))
                # Usar el último timestamp visto (de las líneas TIME=)
                if last_seen_ts is not None:
                    timestamps.append(last_seen_ts)

    # Calcular ventana temporal
    if timestamps:
        t_min = min(timestamps)
        t_max = max(timestamps)
        time_window = f"t={t_min:.0f}--{t_max:.0f}s"
    else:
        time_window = "N/A"

    return {
        'duration': duration,
        'discards': discards,
        'forward': forward,
        'last_tx': last_tx,
        'n_flows': len(flow_ids),
        't_min': min(timestamps) if timestamps else None,
        't_max': max(timestamps) if timestamps else None,
        'time_window': time_window,
    }

def save_results(results, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['duration', 'discards', 'forward',
                                                'last_tx', 'n_flows', 't_min', 't_max',
                                                'time_window'])
        writer.writeheader()
        writer.writerows(results)

def main():
    print("=" * 80)
    print("VERIFICACIÓN L12: ReportForwarding() Discards Events")
    print("=" * 80)
    print()

    results = []
    print(f"{'Duration':>8} {'Discards':>10} {'Forward':>8} {'Last-tx':>8} {'Flows':>6} {'Time window':>15}")
    print("-" * 70)

    for dur in DURATIONS:
        log_file = os.path.join(LOG_DIR, f"simulation_{dur}s.log")
        r = analyze_log(log_file, dur)
        if r is None:
            print(f"{dur:>7}s {'SKIP (no log)':>55}")
            continue
        results.append(r)
        print(f"{dur:>7}s {r['discards']:>10} {r['forward']:>8} "
              f"{r['last_tx']:>8} {r['n_flows']:>6} {r['time_window']:>15}")

    print("-" * 70)

    if results:
        total_discards = sum(r['discards'] for r in results)
        print(f"\nTotal descartes: {total_discards}")
        print(f"Rango de descartes: {min(r['discards'] for r in results)}--{max(r['discards'] for r in results)}")

    save_results(results, OUTPUT_FILE)
    print(f"\nResultados guardados en: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()

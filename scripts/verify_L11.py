#!/usr/bin/env python3
"""
Verificación L11: XML Output Omits Empty Bins
Analiza los XML de las 25 corridas de AODV.
"""
import xml.etree.ElementTree as ET
import sys
import glob
import os
import csv

def parse_histogram(xml_elem):
    """Parsea un histograma, devolviendo (nBins_declarados, bins_emitidos)."""
    if xml_elem is None:
        return 0, 0
    n_bins = int(xml_elem.get('nBins', 0))
    emitted = len(xml_elem.findall('bin'))
    return n_bins, emitted

def analyze_run(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    hist_types = {
        'delayHistogram': 'delay',
        'jitterHistogram': 'jitter',
        'packetSizeHistogram': 'packetSize',
        'flowInterruptionsHistogram': 'flowInterruptions',
    }

    results = {}
    for tag, name in hist_types.items():
        declared = 0
        emitted = 0
        for hist in root.findall(f'.//{tag}'):
            d, e = parse_histogram(hist)
            declared += d
            emitted += e
        results[name] = {
            'declared': declared,
            'emitted': emitted,
            'omitted': declared - emitted,
            'pct_omitted': (declared - emitted) / declared * 100 if declared > 0 else 0,
        }
    return results

def save_results(results, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'hist_type', 'declared',
                                                'emitted', 'omitted', 'pct_omitted'])
        writer.writeheader()
        writer.writerows(results)

def main():
    base_dir = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    xml_files = sorted(glob.glob(os.path.join(base_dir, '*', 'flowmonitor_*.xml')))
    if not xml_files:
        print(f"No se encontraron XML en {base_dir}")
        sys.exit(1)

    print(f"{'Corrida':<40} {'Histogram':<18} {'Declared':>12} {'Emitted':>10} {'% omitted':>10}")
    print("-" * 95)
    results = []
    for xml_file in xml_files:
        run_name = os.path.basename(os.path.dirname(xml_file))
        r = analyze_run(xml_file)
        for hist_type, data in r.items():
            entry = {
                'run_name': run_name,
                'hist_type': hist_type,
                'declared': data['declared'],
                'emitted': data['emitted'],
                'omitted': data['omitted'],
                'pct_omitted': data['pct_omitted'],
            }
            results.append(entry)
            print(f"{run_name:<40} {hist_type:<18} {data['declared']:>12,} "
                  f"{data['emitted']:>10,} {data['pct_omitted']:>9.2f}%")
    print("-" * 95)

    # Resumen global por tipo de histograma
    print("\nResumen global por tipo de histograma:")
    print(f"{'Histogram':<18} {'Declared':>12} {'Emitted':>10} {'% omitted':>10}")
    print("-" * 55)
    for hist_type in ['delay', 'jitter', 'packetSize', 'flowInterruptions']:
        entries = [r for r in results if r['hist_type'] == hist_type]
        if entries:
            total_declared = sum(e['declared'] for e in entries)
            total_emitted = sum(e['emitted'] for e in entries)
            pct = (total_declared - total_emitted) / total_declared * 100 if total_declared > 0 else 0
            print(f"{hist_type:<18} {total_declared:>12,} {total_emitted:>10,} {pct:>9.2f}%")

    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L11/L11_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

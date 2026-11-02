#!/usr/bin/env python3
"""
Verificación L2: TCP Flow Inflation by Ephemeral Ports
Reconstruido a partir del Anexo A del documento de limitaciones.
"""
import xml.etree.ElementTree as ET
import sys
import glob
import os
import csv
from collections import defaultdict

def parse_flowmonitor_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    tcp_flows = []
    for flow in root.findall('Ipv4FlowClassifier/Flow'):
        if flow.get('protocol') == '6':  # TCP
            tcp_flows.append({
                'flowId': flow.get('flowId'),
                'src': flow.get('sourceAddress'),
                'dst': flow.get('destinationAddress'),
                'sport': flow.get('sourcePort'),
                'dport': flow.get('destinationPort'),
            })
    return tcp_flows

def analyze_run(xml_file):
    tcp_flows = parse_flowmonitor_xml(xml_file)
    tcp_logical = defaultdict(list)
    for f in tcp_flows:
        key = (f['src'], f['dst'], f['dport'])
        tcp_logical[key].append(f['flowId'])
    n_transport = len(tcp_flows)
    n_logical = len(tcp_logical)
    inflation = n_transport / n_logical if n_logical > 0 else 0
    multi_groups = sum(1 for v in tcp_logical.values() if len(v) > 1)
    return {
        'n_transport': n_transport,
        'n_logical': n_logical,
        'inflation': inflation,
        'multi_groups': multi_groups,
    }

def save_results(results, output_file):
    """Guarda los resultados en un archivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'n_transport', 'n_logical',
                                                'inflation', 'multi_groups'])
        writer.writeheader()
        writer.writerows(results)

def main():
    base_dir = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    xml_files = sorted(glob.glob(os.path.join(base_dir, '*', 'flowmonitor_*.xml')))
    if not xml_files:
        print(f"No se encontraron XML en {base_dir}")
        sys.exit(1)
    print(f"{'Corrida':<40} {'TCP trans':>10} {'TCP logical':>12} {'Inflación':>10} {'Grupos >1':>10}")
    print("-" * 90)
    results = []
    for xml_file in xml_files:
        run_name = os.path.basename(os.path.dirname(xml_file))
        r = analyze_run(xml_file)
        r['run_name'] = run_name
        results.append(r)
        print(f"{run_name:<40} {r['n_transport']:>10} {r['n_logical']:>12} "
              f"{r['inflation']:>9.4f}x {r['multi_groups']:>10}")
    print("-" * 90)
    mean_inflation = sum(r['inflation'] for r in results) / len(results)
    print(f"{'Media inflación':<40} {'':>10} {'':>12} {mean_inflation:>9.4f}x")
    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L2/L2_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

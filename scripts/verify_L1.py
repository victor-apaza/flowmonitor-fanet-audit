#!/usr/bin/env python3
"""
Verificación L1: Routing Flow Aggregation Bias
Reconstruido a partir del Anexo B del documento de limitaciones.
"""
import xml.etree.ElementTree as ET
import sys
import glob
import os
import csv

ROUTING_PORTS = {'654', '698', '521'}

def parse_flowmonitor_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    flow_info = {}
    for flow in root.findall('Ipv4FlowClassifier/Flow'):
        fid = flow.get('flowId')
        flow_info[fid] = {
            'protocol': flow.get('protocol'),
            'src': flow.get('sourceAddress'),
            'dst': flow.get('destinationAddress'),
            'sport': flow.get('sourcePort'),
            'dport': flow.get('destinationPort'),
        }
    flow_stats = {}
    for flow in root.findall('FlowStats/Flow'):
        fid = flow.get('flowId')
        flow_stats[fid] = {
            'tx': int(flow.get('txPackets', 0)),
            'rx': int(flow.get('rxPackets', 0)),
            'lost': int(flow.get('lostPackets', 0)),
            'txBytes': int(flow.get('txBytes', 0)),
        }
    return flow_info, flow_stats

def compute_pdr(flow_ids, flow_stats):
    pdrs = []
    for fid in flow_ids:
        s = flow_stats.get(fid, {})
        rx = s.get('rx', 0)
        lost = s.get('lost', 0)
        total = rx + lost
        pdrs.append(rx / total if total > 0 else 0)
    return sum(pdrs) / len(pdrs) if pdrs else 0

def analyze_run(xml_file):
    flow_info, flow_stats = parse_flowmonitor_xml(xml_file)
    routing_flows = []
    app_flows = []
    for fid, info in flow_info.items():
        is_routing = (info['sport'] in ROUTING_PORTS or info['dport'] in ROUTING_PORTS)
        if is_routing:
            routing_flows.append(fid)
        else:
            app_flows.append(fid)
    pdr_all = compute_pdr(list(flow_info.keys()), flow_stats)
    pdr_app = compute_pdr(app_flows, flow_stats)
    pdr_routing = compute_pdr(routing_flows, flow_stats) if routing_flows else 0
    return {
        'total': len(flow_info),
        'routing': len(routing_flows),
        'app': len(app_flows),
        'pdr_all': pdr_all * 100,
        'pdr_app': pdr_app * 100,
        'pdr_routing': pdr_routing * 100,
        'delta_pp': (pdr_app - pdr_all) * 100,
    }

def save_results(results, output_file):
    """Guarda los resultados en un archivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'total', 'routing', 'app',
                                                'pdr_all', 'pdr_app', 'pdr_routing', 'delta_pp'])
        writer.writeheader()
        writer.writerows(results)

def main():
    base_dir = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    xml_files = sorted(glob.glob(os.path.join(base_dir, '*', 'flowmonitor_*.xml')))
    if not xml_files:
        print(f"No se encontraron XML en {base_dir}")
        sys.exit(1)
    print(f"{'Corrida':<40} {'Total':>6} {'Routing':>8} {'App':>6} {'PDR_all':>9} {'PDR_app':>9} {'Δ pp':>8}")
    print("-" * 100)
    results = []
    for xml_file in xml_files:
        run_name = os.path.basename(os.path.dirname(xml_file))
        r = analyze_run(xml_file)
        r['run_name'] = run_name
        results.append(r)
        print(f"{run_name:<40} {r['total']:>6} {r['routing']:>8} {r['app']:>6} "
              f"{r['pdr_all']:>8.4f}% {r['pdr_app']:>8.4f}% {r['delta_pp']:>+8.4f}")
    print("-" * 100)
    mean_delta = sum(r['delta_pp'] for r in results) / len(results)
    print(f"{'Media Δ PDR':<40} {'':>6} {'':>8} {'':>6} {'':>9} {'':>9} {mean_delta:>+8.4f}")
    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L1/L1_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

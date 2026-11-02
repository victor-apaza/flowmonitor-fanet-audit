#!/usr/bin/env python3
"""
Verificación L6: timesForwarded Ignores IP Fragments
Reconstruido a partir del Anexo E del documento de limitaciones.

Identifica flujos fragmentados (bytes/pkt > 1500) y compara su hop count
con el de los flujos no fragmentados.
"""
import xml.etree.ElementTree as ET
import sys
import glob
import os
import csv

FRAGMENTATION_THRESHOLD = 1500  # MTU típico de WiFi

def parse_flowmonitor_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    flow_info = {}
    for flow in root.findall('Ipv4FlowClassifier/Flow'):
        fid = flow.get('flowId')
        flow_info[fid] = {
            'sport': flow.get('sourcePort'),
            'dport': flow.get('destinationPort'),
        }
    flow_stats = {}
    for flow in root.findall('FlowStats/Flow'):
        fid = flow.get('flowId')
        flow_stats[fid] = {
            'tx': int(flow.get('txPackets', 0)),
            'rx': int(flow.get('rxPackets', 0)),
            'txBytes': int(flow.get('txBytes', 0)),
            'timesForwarded': int(flow.get('timesForwarded', 0)),
        }
    return flow_info, flow_stats

def analyze_run(xml_file):
    flow_info, flow_stats = parse_flowmonitor_xml(xml_file)
    fragmented = []
    normal = []
    for fid, s in flow_stats.items():
        if s['tx'] == 0:
            continue
        bpp = s['txBytes'] / s['tx']
        hop = 1 + s['timesForwarded'] / s['rx'] if s['rx'] > 0 else 0
        entry = {
            'flowId': fid,
            'sport': flow_info.get(fid, {}).get('sport', '?'),
            'dport': flow_info.get(fid, {}).get('dport', '?'),
            'tx': s['tx'],
            'rx': s['rx'],
            'txBytes': s['txBytes'],
            'bytes_per_pkt': bpp,
            'timesForwarded': s['timesForwarded'],
            'hop_count': hop,
        }
        if bpp > FRAGMENTATION_THRESHOLD:
            fragmented.append(entry)
        else:
            normal.append(entry)

    def mean_hop(entries):
        hops = [e['hop_count'] for e in entries if e['hop_count'] > 0 and e['hop_count'] < 20]
        return sum(hops) / len(hops) if hops else 0

    return {
        'n_fragmented': len(fragmented),
        'n_normal': len(normal),
        'hop_normal': mean_hop(normal),
        'hop_fragmented': mean_hop(fragmented) if fragmented else 0,
        'fragmented_details': fragmented,
    }

def save_results(results, output_file):
    """Guarda los resultados en un archivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    clean_results = []
    for r in results:
        clean_results.append({k: v for k, v in r.items() if k != 'fragmented_details'})
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['run_name', 'n_fragmented', 'n_normal',
                                                'hop_normal', 'hop_fragmented'])
        writer.writeheader()
        writer.writerows(clean_results)

def main():
    base_dir = os.path.expanduser('~/flowmonitor-fanet-audit/data/raw/AODV')
    xml_files = sorted(glob.glob(os.path.join(base_dir, '*', 'flowmonitor_*.xml')))
    if not xml_files:
        print(f"No se encontraron XML en {base_dir}")
        sys.exit(1)
    print(f"{'Corrida':<40} {'Frag.':>6} {'Normal':>7} {'Hop norm':>9} {'Hop frag':>9}")
    print("-" * 80)
    results = []
    for xml_file in xml_files:
        run_name = os.path.basename(os.path.dirname(xml_file))
        r = analyze_run(xml_file)
        r['run_name'] = run_name
        results.append(r)
        print(f"{run_name:<40} {r['n_fragmented']:>6} {r['n_normal']:>7} "
              f"{r['hop_normal']:>9.3f} {r['hop_fragmented']:>9.3f}")
    print("-" * 80)
    mean_hop_normal = sum(r['hop_normal'] for r in results) / len(results)
    frag_runs = [r for r in results if r['n_fragmented'] > 0]
    mean_hop_frag = sum(r['hop_fragmented'] for r in frag_runs) / len(frag_runs) if frag_runs else 0
    print(f"{'Media global':<40} {'':>6} {'':>7} {mean_hop_normal:>9.3f} {mean_hop_frag:>9.3f}")
    output_file = os.path.expanduser('~/flowmonitor-fanet-audit/results/L6/L6_results.csv')
    save_results(results, output_file)
    print(f"\nResultados guardados en: {output_file}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Verificación L9: Histogram Does Not Implement N, μ, s
Inspección de código fuente de NS-3.47.
"""
import os
import re
import sys

HISTOGRAM_H = "/home/vic/ns3.47/ns-allinone-3.47/ns-3.47/src/stats/model/histogram.h"

def main():
    if not os.path.exists(HISTOGRAM_H):
        print(f"ERROR: No se encontró {HISTOGRAM_H}")
        sys.exit(1)

    with open(HISTOGRAM_H, 'r') as f:
        content = f.read()

    print("=" * 80)
    print("VERIFICACIÓN L9: Histogram Does Not Implement N, μ, s")
    print("=" * 80)
    print()

    # 1. Verificar el @todo
    print("1. Buscando @todo en histogram.h...")
    todo_matches = re.findall(r'@todo.*', content)
    if todo_matches:
        for t in todo_matches:
            print(f"   Encontrado: {t.strip()}")
    else:
        print("   NO se encontró @todo")
    print()

    # 2. Verificar métodos existentes
    print("2. Métodos existentes en la API:")
    methods_existing = ['GetNBins', 'GetBinStart', 'GetBinEnd', 'GetBinWidth', 'GetBinCount', 'AddValue']
    for m in methods_existing:
        if m in content:
            print(f"   ✅ {m}() existe")
        else:
            print(f"   ❌ {m}() NO existe")
    print()

    # 3. Verificar métodos ausentes
    print("3. Métodos AUSENTES (que deberían existir según el paper):")
    methods_missing = ['GetN', 'GetMean', 'GetStdDev', 'GetVariance']
    missing_count = 0
    for m in methods_missing:
        # Buscar declaración de método (no solo mención en comentario)
        if re.search(rf'\b{m}\s*\(', content):
            print(f"   ❌ {m}() existe (no debería)")
        else:
            print(f"   ✅ {m}() NO existe (confirmado)")
            missing_count += 1
    print()

    # 4. Conclusión
    print("=" * 80)
    if missing_count == len(methods_missing):
        print(f"RESULTADO: L9 CONFIRMADO. Los {missing_count} métodos no existen.")
    else:
        print(f"RESULTADO: L9 NO confirmado. {len(methods_missing) - missing_count} métodos existen.")
    print("=" * 80)

if __name__ == '__main__':
    main()

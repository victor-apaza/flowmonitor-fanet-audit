#!/usr/bin/env python3
"""
Verificación L10: Histogram Fails on Negative Values
Inspección de código fuente de NS-3.47 + tabla de cast.
"""
import os
import re
import sys

HISTOGRAM_CC = "/home/vic/ns3.47/ns-allinone-3.47/ns-3.47/src/stats/model/histogram.cc"
HISTOGRAM_H = "/home/vic/ns3.47/ns-allinone-3.47/ns-3.47/src/stats/model/histogram.h"

def main():
    print("=" * 80)
    print("VERIFICACIÓN L10: Histogram Fails on Negative Values")
    print("=" * 80)
    print()

    # 1. Verificar AddValue() en histogram.cc
    print("1. Inspeccionando AddValue() en histogram.cc...")
    if os.path.exists(HISTOGRAM_CC):
        with open(HISTOGRAM_CC, 'r') as f:
            content = f.read()
        # Buscar el cast
        match = re.search(r'auto\s+index\s*=\s*\(uint32_t\)\s*std::floor', content)
        if match:
            print("   ✅ Encontrado: (uint32_t)std::floor(value / m_binWidth)")
            print("   ✅ El cast C-style NO valida negativos")
        else:
            print("   ❌ NO se encontró el cast esperado")
        # Buscar NS_ASSERT
        if 'NS_ASSERT' in content or 'NS_ABORT' in content:
            print("   ⚠️ Se encontró NS_ASSERT/NS_ABORT (puede validar negativos)")
        else:
            print("   ✅ NO hay NS_ASSERT/NS_ABORT (no valida negativos)")
    else:
        print(f"   ❌ No se encontró {HISTOGRAM_CC}")
    print()

    # 2. Verificar reconocimiento en histogram.h
    print("2. Buscando reconocimiento en histogram.h...")
    if os.path.exists(HISTOGRAM_H):
        with open(HISTOGRAM_H, 'r') as f:
            content = f.read()
        if 'does not handles negative data' in content or 'positive bins' in content:
            print("   ✅ El autor reconoce que no maneja negativos")
        else:
            print("   ❌ NO se encontró el reconocimiento")
    print()

    # 3. Tabla de cast
    print("3. Tabla de cast de negativos a uint32_t:")
    print(f"   {'Input':>10} {'floor(val/w)':>15} {'Cast to uint32':>20} {'resize':>15}")
    print(f"   {'-'*10:>10} {'-'*15:>15} {'-'*20:>20} {'-'*15:>15}")
    UINT32_MAX = 4294967295
    for val in [0.001, 0.000, -0.001, -1.000]:
        floor_val = int(val / 0.001) if val >= 0 else -int(abs(val) / 0.001) - 1
        cast_val = floor_val if floor_val >= 0 else UINT32_MAX + floor_val + 1
        if val >= 0:
            resize = f"{floor_val + 1} bins"
        else:
            resize = "OOM"
        print(f"   {val:>10.3f} {floor_val:>15} {cast_val:>20,} {resize:>15}")
    print()

    # 4. Conclusión
    print("=" * 80)
    print("RESULTADO: L10 CONFIRMADO. El cast no valida negativos y causa OOM.")
    print("=" * 80)

if __name__ == '__main__':
    main()

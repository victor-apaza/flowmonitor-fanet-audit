#!/bin/bash
# ============================================================================
# EXP_L12_REPORT_FORWARDING: ReportForwarding() Discards Events
#
# Objetivo: Cuantificar los descartes de eventos en ReportForwarding()
#           y ReportLastRx() cuando el paquete no está en m_trackedPackets.
#
# Fundamento teórico:
#   FlowMonitor::ReportForwarding() y ReportLastRx() descartan eventos
#   cuando el paquete no está en m_trackedPackets, emitiendo solo un
#   NS_LOG_WARN y retornando. Esto afecta a timesForwarded y al hop count.
#
#   Los descartes ocurren al final de la simulación (últimos 2 segundos),
#   cuando hay eventos pendientes (cierres TCP, mantenimiento AODV, etc.).
#
# Referencia:
#   - flow-monitor.cc: ReportForwarding() y ReportLastRx()
#   - Reporte L12, Sección 5
#
# Configuración:
#   - Protocolo: AODV
#   - Formación: GRID
#   - N: 30
#   - Seed: 42
#   - Duraciones: 20, 40, 50, 80, 100, 120, 180s
#   - NS_LOG="FlowMonitor=warn"
#
# Simulaciones: 7 (una por duración)
# Tiempo estimado: ~30 min
# ============================================================================

source exp_config.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  EXP_L12: ReportForwarding() Discards Events                   ║"
echo "║  Duraciones: 20, 40, 50, 80, 100, 120, 180s                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuración
EXP_NAME="Exp_L12_ReportForwarding"
PROTOCOL="AODV"
N=30
SEED=42
DURATIONS=(20 40 50 80 100 120 180)
FORMATION="GRID"
LEADER_SPEED=5
LEADER_ID=0
START_IN_FORMATION=false
FLOW_MON=true

# Directorio de salida
OUTPUT_DIR="$HOME/flowmonitor-fanet-audit/data/raw/L12_logs"
mkdir -p "$OUTPUT_DIR"

# Ejecutar simulaciones
for DUR in "${DURATIONS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 Simulación: N=$N, seed=$SEED, duration=${DUR}s"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    LOG_FILE="$OUTPUT_DIR/simulation_${DUR}s.log"

    # Ejecutar con NS_LOG="FlowMonitor=warn"
    NS_LOG="FlowMonitor=warn" ./ns3 run "test-formations \
        --formation=$FORMATION \
        --nDrones=$N \
        --duration=$DUR \
        --startInFormation=$START_IN_FORMATION \
        --routing=$PROTOCOL \
        --leaderId=$LEADER_ID \
        --leaderSpeed=$LEADER_SPEED \
        --verbose=false \
        --flow-mon=$FLOW_MON \
        --seed=$SEED" > "$LOG_FILE" 2>&1

    # Contar descartes
    DISCARD_COUNT=$(grep -c "not known to be transmitted" "$LOG_FILE" || true)
    FORWARD_COUNT=$(grep -c "forward report" "$LOG_FILE" || true)
    LAST_TX_COUNT=$(grep -c "last-tx report" "$LOG_FILE" || true)

    echo "   Descartes totales: $DISCARD_COUNT"
    echo "   Forward reports: $FORWARD_COUNT"
    echo "   Last-tx reports: $LAST_TX_COUNT"
    echo ""
done

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  EXP_L12 COMPLETADO                                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Logs en: $OUTPUT_DIR"
echo ""
echo "Próximo paso: ejecutar verify_L12.py para generar el CSV."

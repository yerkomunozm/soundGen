#!/usr/bin/env bash
#
# generate_all.sh — Genera los 12 intervalos desde una nota base.
# Uso: ./generate_all.sh [nota] [duración] [instrumento]
#   nota:        C4 (default), A3, F#4, etc.
#   duración:    2.0 (default), en segundos
#   instrumento: piano (default), organ, sine
#
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$DIR/venv/bin/python"
NOTE="${1:-C4}"
DURATION="${2:-2.0}"
INSTRUMENT="${3:-piano}"

INTERVALS=(
    segunda_menor
    segunda_mayor
    tercera_menor
    tercera_mayor
    cuarta_justa
    tritono
    quinta_justa
    sexta_menor
    sexta_mayor
    septima_menor
    septima_mayor
    octava
)

echo "Generando todos los intervalos desde $NOTE (instrumento: $INSTRUMENT)..."
for interval in "${INTERVALS[@]}"; do
    echo "  → $NOTE  +  $interval"
    "$VENV_PYTHON" "$DIR/generate_interval.py" "$NOTE" "$interval" \
        --duration "$DURATION" --instrument "$INSTRUMENT"
done

echo ""
echo "Completado. Archivos en: $DIR/output/"

#!/bin/bash
set -e

echo "========================================================================"
echo "🚀 UNIFIED BENCHMARK + VISUAL COMPARISON — ALL 6 YOLO26-SEM MODELS"
echo "========================================================================"

# Any extra flags (--save-all, --splits ..., --device ...) are passed through.
PYTHONPATH=. python run_full_benchmark.py "$@"

echo -e "\n✅ Unified benchmark complete."
echo "   Matrix CSV        : predictions_stitched/benchmark_matrix.csv"
echo "   Visual comparisons: predictions_stitched/<model_name>/{small_defects,missed_defects,false_positives}/"

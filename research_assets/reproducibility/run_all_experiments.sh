#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# IEEE Access Research Experiment Runner
# Executes all experiments in dependency order from the project root.
# Usage:
#   bash research_assets/reproducibility/run_all_experiments.sh
#   bash research_assets/reproducibility/run_all_experiments.sh --skip-slow
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXPERIMENTS_DIR="$PROJECT_ROOT/research_assets/experiments"

echo "============================================================"
echo "  IEEE Access Research Experiment Suite"
echo "  Project root: $PROJECT_ROOT"
echo "============================================================"

# Activate virtual environment if present
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "  Activated .venv"
elif [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "  Activated venv"
fi

# Install research dependencies
echo ""
echo "  Installing research dependencies..."
pip install -q -r "$SCRIPT_DIR/requirements_experiments.txt"

# Set Python path
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

cd "$PROJECT_ROOT"

# Run master experiment runner
SKIP_SLOW=""
if [[ "${1:-}" == "--skip-slow" ]]; then
    SKIP_SLOW="--skip-slow"
    echo "  Mode: skip-slow (skipping scalability and cross-validation)"
fi

echo ""
python "$EXPERIMENTS_DIR/run_all_experiments.py" $SKIP_SLOW

echo ""
echo "============================================================"
echo "  All experiments complete."
echo "  Results: research_assets/results/"
echo "  Figures:  research_assets/figures/"
echo "  Reports:  research_assets/reports/"
echo "============================================================"

#!/usr/bin/env bash
set -euo pipefail

# ARK Setup — разворачивает среду разработки
# Запуск: bash setup.sh

echo "============================================================"
echo "  ARK Setup"
echo "============================================================"

# 1. Python deps
echo ""
echo "[1/4] Installing Python dependencies..."
pip install lark-parser z3-solver --quiet 2>/dev/null || \
pip install lark-parser z3-solver --break-system-packages --quiet 2>/dev/null || \
pip3 install lark-parser z3-solver --quiet 2>/dev/null
echo "  ✓ lark-parser, z3-solver"

# 2. Verify project structure
echo ""
echo "[2/4] Checking project structure..."
REQUIRED_FILES=(
  "ark.py"
  "CLAUDE.md"
  "docs/DSL_SPEC.md"
  "specs/root.ark"
  "specs/test_minimal.ark"
  "tools/parser/ark_grammar.lark"
  "tools/parser/ark_parser.py"
  "tools/verify/ark_verify.py"
  "tools/verify/ark_impact.py"
  "tools/codegen/ark_codegen.py"
  "tools/visualizer/ark_visualizer.py"
  "dsl/stdlib/types.ark"
)

MISSING=0
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "  ✗ MISSING: $f"
    MISSING=$((MISSING + 1))
  fi
done

if [ "$MISSING" -eq 0 ]; then
  echo "  ✓ All ${#REQUIRED_FILES[@]} required files present"
else
  echo "  ⚠ $MISSING files missing — project may be incomplete"
fi

# 3. Create output directories
echo ""
echo "[3/4] Creating directories..."
mkdir -p specs/game specs/infra specs/pipeline generated/{rust,cpp,proto}
echo "  ✓ specs/game, specs/infra, specs/pipeline, generated/"

# 4. Smoke test
echo ""
echo "[4/4] Running smoke test..."
echo ""

python ark.py pipeline specs/test_minimal.ark --target rust 2>&1

RESULT=$?
echo ""
if [ "$RESULT" -eq 0 ]; then
  echo "============================================================"
  echo "  ✓ ARK is ready."
  echo ""
  echo "  Next steps:"
  echo "    cat CLAUDE.md              — read master instructions"
  echo "    cat docs/DSL_SPEC.md       — read language spec"
  echo "    python ark.py --help       — see all commands"
  echo "============================================================"
else
  echo "============================================================"
  echo "  ✗ Smoke test failed. Check errors above."
  echo "============================================================"
  exit 1
fi

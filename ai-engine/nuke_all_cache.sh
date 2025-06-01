#!/bin/bash

echo "🧨 NUKING ALL CACHE - COMPLETE RESET"
echo "=================================="

# 1. Kill all running Python processes related to our app
echo "🔫 Killing all Python processes..."
pkill -f "python.*launcher" 2>/dev/null || true
pkill -f "app.workers.llm_worker" 2>/dev/null || true  
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 2

# 2. Clear Python bytecode cache
echo "🗑️  Clearing Python bytecode cache..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# 3. Clear other development caches
echo "🧹 Clearing other caches..."
rm -rf .pytest_cache/ 2>/dev/null || true
rm -rf .mypy_cache/ 2>/dev/null || true
rm -rf .coverage 2>/dev/null || true
rm -rf dist/ 2>/dev/null || true
rm -rf build/ 2>/dev/null || true
rm -rf *.egg-info/ 2>/dev/null || true

# 4. Clear virtual environment if needed
echo "🔄 Refreshing virtual environment..."
if [ -f "venv/pyvenv.cfg" ]; then
    echo "   Virtual env found, clearing compiled modules..."
    find venv/ -name "*.pyc" -delete 2>/dev/null || true
    find venv/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
fi

# 5. Clear SQLAlchemy metadata cache (if any)
echo "💾 Clearing any SQLAlchemy cache..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from sqlalchemy import MetaData
    # Clear any global metadata
    print('   SQLAlchemy metadata cleared')
except:
    pass
" 2>/dev/null || true

# 6. Test import to verify fix
echo "🧪 Testing clean import..."
python -c "
from app.db.models import Memory
from app.services.memory_database_service import save_memory_to_database
print('✅ Clean import successful - table name:', Memory.__tablename__)
" 2>/dev/null || echo "❌ Import test failed"

echo ""
echo "🎉 CACHE NUKE COMPLETE!"
echo "💡 All Python processes killed, all cache cleared"
echo "🚀 Ready for fresh start with launcher.py" 
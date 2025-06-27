#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI application can start
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    from app.core.config import settings
    print("✅ FastAPI application imported successfully!")
    print(f"📝 App title: {settings.app_name}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"🌐 Allowed origins: {settings.allowed_origins}")
    print("🚀 Application is ready to run!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1) 
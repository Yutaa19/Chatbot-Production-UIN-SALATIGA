#!/usr/bin/env python3
# scripts/test_system.py
"""
System integration test — pastikan seluruh komponen berjalan.
Jalankan sebelum/after deploy.
"""

import os
import sys
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_health():
    resp = requests.get("http://localhost:8000/api/health", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('redis') is True
    assert data.get('qdrant') is True
    print("✅ Health check: OK")

def test_chat():
    payload = {"query": "Apa visi UIN Salatiga?"}
    resp = requests.post("http://localhost:8000/api/ask", json=payload, timeout=15)
    assert resp.status_code == 200
    data = resp.json()
    assert 'answer' in data
    assert len(data['answer']) > 10
    print("✅ Chat endpoint: OK")

if __name__ == "__main__":
    print("🧪 Menjalankan system test...")
    test_health()
    test_chat()
    print("🎉 Semua test lulus!")
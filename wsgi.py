# wsgi.py
import sys
import os

# Tambahkan root project ke Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.app import application

if __name__ == "__main__":
    application.run()
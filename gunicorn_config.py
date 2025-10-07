# gunicorn.conf.py
import os

bind = "127.0.0.1:8000"  # Hanya bind ke localhost (Nginx sebagai reverse proxy)
workers = 2              # 2 worker untuk 2 vCPU
worker_class = "sync"
timeout = 90
keepalive = 5
max_requests = 400
max_requests_jitter = 40
preload_app = False

# Logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
accesslog = os.path.join(log_dir, "gunicorn_access.log")
errorlog = os.path.join(log_dir, "gunicorn_error.log")
loglevel = "info"
capture_output = True

# Security
user = "chatbot"
group = "chatbot"
worker_tmp_dir = "/dev/shm"
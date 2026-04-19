"""
Gunicorn configuration file for Django Chatbot application
"""

import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/gunicorn/chatbot_access.log"
errorlog = "/var/log/gunicorn/chatbot_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "chatbot_django"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/chatbot.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

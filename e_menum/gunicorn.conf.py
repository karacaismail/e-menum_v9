"""
Gunicorn configuration file for E-Menum Django application.

This configuration is optimized for production deployment on Hetzner VPS
behind Nginx reverse proxy.

Usage:
    gunicorn -c gunicorn.conf.py config.wsgi:application

Environment Variables:
    GUNICORN_WORKERS: Number of worker processes (default: CPU * 2 + 1)
    GUNICORN_THREADS: Number of threads per worker (default: 2)
    GUNICORN_BIND: Address to bind to (default: 0.0.0.0:8000)
    GUNICORN_TIMEOUT: Worker timeout in seconds (default: 120)
    GUNICORN_LOG_LEVEL: Logging level (default: info)
"""

import multiprocessing
import os

# =============================================================================
# SERVER SOCKET
# =============================================================================

# Bind to the specified address
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# Backlog - maximum number of pending connections
backlog = 2048


# =============================================================================
# WORKER PROCESSES
# =============================================================================

# Worker count: (2 * CPU) + 1 is a good baseline
# For Hetzner CX21 (2 vCPU), default is 5 workers
_default_workers = multiprocessing.cpu_count() * 2 + 1
workers = int(os.environ.get('GUNICORN_WORKERS', _default_workers))

# Worker class
# 'sync' - Standard synchronous workers (default)
# 'gevent' - Async workers using gevent
# 'eventlet' - Async workers using eventlet
# 'gthread' - Threaded workers
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')

# Threads per worker (for gthread worker class)
# Also affects sync workers for handling concurrent requests
threads = int(os.environ.get('GUNICORN_THREADS', 2))

# Maximum number of simultaneous clients per worker
worker_connections = 1000

# Maximum number of requests a worker will process before restarting
# Helps prevent memory leaks
max_requests = 1000
max_requests_jitter = 50  # Randomize restart to prevent all workers restarting at once


# =============================================================================
# TIMEOUTS
# =============================================================================

# Worker timeout (seconds) - kill and restart worker if no response
# Set higher for long-running requests (e.g., AI content generation)
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))

# Graceful timeout (seconds) - time to finish requests during graceful restart
graceful_timeout = 30

# Keep-alive timeout (seconds)
# After this many seconds of inactivity, close the connection
# Should be higher than Nginx proxy timeout
keepalive = 5


# =============================================================================
# SECURITY
# =============================================================================

# Limit the allowed size of an incoming HTTP request line (default 4094)
limit_request_line = 4094

# Limit the number of headers in a request
limit_request_fields = 100

# Limit the size of a request header field
limit_request_field_size = 8190

# Run workers as the specified user
# user = 'www-data'
# group = 'www-data'

# Process umask
umask = 0o022


# =============================================================================
# SERVER MECHANICS
# =============================================================================

# Daemonize the Gunicorn process (runs in background)
# Set to False when using systemd or Docker
daemon = False

# Pidfile location for process management
pidfile = os.environ.get('GUNICORN_PIDFILE', None)

# Working directory
# chdir = '/path/to/app'

# Preload application code before worker processes are forked
# Saves memory but changes in code require full restart
preload_app = True

# Restart workers when code changes (development only)
# Never enable in production
reload = False

# Temporary directory for worker heartbeat files
# Using /dev/shm for faster I/O in containers
tmp_upload_dir = None

# Explicitly disable statsd to prevent control server socket errors
statsd_host = None
statsd_prefix = ''

# Forwarded allow IPs - trust X-Forwarded-* headers from these IPs
# '*' trusts all proxies - only use if behind trusted proxy
forwarded_allow_ips = os.environ.get('GUNICORN_FORWARDED_ALLOW_IPS', '127.0.0.1')

# Access log - use '-' for stdout
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')

# Error log - use '-' for stderr
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')

# Log level
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')


# =============================================================================
# LOGGING
# =============================================================================

# Access log format
# %(h)s - Remote address
# %(l)s - '-' (not used)
# %(u)s - User name
# %(t)s - Date/time
# %(r)s - Status line (e.g., GET / HTTP/1.1)
# %(m)s - Request method
# %(U)s - URL path
# %(q)s - Query string
# %(H)s - Protocol
# %(s)s - Status code
# %(B)s - Response length
# %(b)s - Response length or '-'
# %(f)s - Referer
# %(a)s - User agent
# %(T)s - Request time in seconds
# %(D)s - Request time in microseconds
# %(L)s - Request time in decimal seconds
# %(p)s - Process ID
# %({header}i)s - Request header
# %({header}o)s - Response header

# JSON format for structured logging (production)
access_log_format = (
    '{"time":"%(t)s", "method":"%(m)s", "path":"%(U)s", "query":"%(q)s", '
    '"status":%(s)s, "size":%(B)s, "duration":"%(L)ss", "ip":"%(h)s", '
    '"agent":"%(a)s", "referer":"%(f)s"}'
)

# Capture output from stdout/stderr of workers
capture_output = True

# Enable stdio inheritance for logging
enable_stdio_inheritance = True


# =============================================================================
# PROCESS NAMING
# =============================================================================

# Process name prefix
proc_name = 'emenum-gunicorn'


# =============================================================================
# SERVER HOOKS
# =============================================================================

def on_starting(server):
    """
    Called just before the master process is initialized.
    """
    pass


def on_reload(server):
    """
    Called to recycle workers during a reload via SIGHUP.
    """
    pass


def when_ready(server):
    """
    Called just after the server is started.
    """
    pass


def pre_fork(server, worker):
    """
    Called just before a worker is forked.
    """
    pass


def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    Close database connections so each worker gets its own connection.
    """
    from django.db import connections
    for conn in connections.all():
        conn.close()


def pre_exec(server):
    """
    Called just before a new master process is forked.
    """
    pass


def child_exit(server, worker):
    """
    Called in the master process after a worker has exited.
    """
    pass


def worker_exit(server, worker):
    """
    Called in the worker process after it has exited.
    """
    from django.db import connections
    for conn in connections.all():
        conn.close()


def nworkers_changed(server, new_value, old_value):
    """
    Called when the number of workers changes.
    """
    pass


def worker_int(worker):
    """
    Called when a worker receives SIGINT or SIGQUIT.
    """
    pass


def worker_abort(worker):
    """
    Called when a worker receives SIGABRT.
    """
    pass


# =============================================================================
# SSL (if not terminating at Nginx)
# =============================================================================

# Uncomment and configure if SSL is needed at Gunicorn level
# keyfile = '/path/to/server.key'
# certfile = '/path/to/server.crt'
# ssl_version = 'TLSv1_2'
# ca_certs = '/path/to/ca.crt'
# ciphers = 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256'

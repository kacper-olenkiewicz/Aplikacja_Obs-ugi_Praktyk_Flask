import multiprocessing

bind = "0.0.0.0:5000"
# 2 workery na rdzeń — dobre dla I/O-heavy aplikacji webowych
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 60
keepalive = 5
max_requests = 1000          # recykling workerów zapobiega wyciekowi pamięci
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
loglevel = "info"

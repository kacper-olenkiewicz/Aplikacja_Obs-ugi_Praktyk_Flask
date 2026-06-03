import os

bind = "0.0.0.0:5000"
# W kontenerze multiprocessing.cpu_count() widzi rdzenie hosta, nie limity
# cgroup — dlatego liczba workerów jest sterowana zmienną WEB_WORKERS.
workers = int(os.getenv("WEB_WORKERS", "4"))
worker_class = "sync"
timeout = 60
keepalive = 5
max_requests = 1000          # recykling workerów zapobiega wyciekowi pamięci
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
loglevel = "info"

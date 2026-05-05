import os

workers = 1
threads = 1
worker_class = "sync"
timeout = 120 #for groq/gemini api calls
max_requests = 50  # to prevent memory leak
max_request_jitter = 10
# bind = "0.0.0.0:8000"
bind = f"0.0.0.0:{os.environ.get('PORT', 10000)}"
preload_app = True #load modal once before fork
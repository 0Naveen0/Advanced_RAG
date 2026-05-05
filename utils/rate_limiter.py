import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
	def __init__(self,max_requests:int = 10,window_seconds:int = 60):
		self.max_requests = max_requests
		self.window = window_seconds
		self.requests = defaultdict(list)
		self.lock = Lock()
		
	def is_allowed(self,client_ip:str)->bool:
		now = time.time()
		with self.lock:
			self.requests[client_ip] = [t for t in self.requests[client_ip] if now-t < self.window]
			if len(self.requests[client_ip])>=self.max_requests:
				return False
			self.requests[client_ip].append(now)
		return True
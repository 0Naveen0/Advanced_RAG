import json
import os
import uuid
from datetime import datetime
from config.config import LOG_PATH
from observability.langfuse_tracer import LangfuseTracer

class Logger:
	_instance = None
	
	def __init__(self,logpath:str=LOG_PATH):
		self.logpath = logpath
		os.makedirs(os.path.dirname(logpath),exist_ok=True)
		
	@classmethod
	def get_instance(cls):
		if cls._instance is None:
			cls._instance = Logger()
		return cls._instance
		
	def build_log(self,query:str,answer:str,confidence:str,source:str,chunk_ids:list,retrieval_scores:list,reranker_scores:list,rewrite_triggered:bool,rewritten_query:str,latency:dict,anomalies:list,progress:dict)->dict:
			return {
				"request_id": str(uuid.uuid4()),
				"timestamp":datetime.now().isoformat(),
				"query":query,
				"answer":answer,
				"confidence":confidence,
				"source":source,
				"chunk_ids":chunk_ids,
				"retrieval_scores":retrieval_scores,
				"reranker_scores":reranker_scores,
				"rewrite_triggered":rewrite_triggered,
				"rewritten_query":rewritten_query,
				"latency":latency,
				"anomalies": anomalies,
        "progress" : progress
				}
				
	def write_log(self,log:dict):
		logs = []
		# Load existing log file if any
		if os.path.exists(self.logpath):
			try:
				with open(self.logpath,'r') as f:
					logs = json.load(f)
			except(json.JSONDecodeError,IOError):
				logs = []
		logs.append(log)
		with open(self.logpath,'w') as f:
			json.dump(logs,f,indent=2)
			
	def log_request(self,**kwargs)->dict:
		log = self.build_log(**kwargs)
		self.write_log(log)
		LangfuseTracer.trace(log)
		print(f"[Logger] {log['request_id']} |"
			f"latency:{log['latency']['total']}s|" 
			f"confidence:{log['confidence']}|" 
			f"anomalies:{log['anomalies']} |"
			f"progress:{log['progress']}|" 
		)
		return log
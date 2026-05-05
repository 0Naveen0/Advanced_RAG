# import os
# from langfuse import Langfuse
# # from langfuse.otel import Langfuse

# class LangfuseTracer:
# 	_client = None
	
# 	@classmethod
# 	def get_client(cls):		
# 		cls._client = Langfuse(public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),secret_key=os.getenv("LANGFUSE_SECRET_KEY"),host=os.getenv("LANGFUSE_BASE_URL"),)
# 		return cls._client

# 	@staticmethod	
# 	def trace(log:dict):
# 		client = LangfuseTracer.get_client()
# 		if client is None:
# 			print("Langfuse client not initialized. Skipping trace.")
# 			return
# 		# with trace(
#     #      name="eka_request",
#     #      input={"query": log['query']},
#     #      output={"answer": log["answer"]},
#     #      metadata=log
#     #  ):
# 		#  pass

# 		client.start_trace(name="eka_request",input={"query":log['query']},output = {"answer":log["answer"]},metadata=log)
# 		client.flush()

from langfuse import Langfuse
import os
from dotenv import load_dotenv

class LangfuseTracer:
	_client = None
	
	@classmethod
	def get_client(cls):
		# load_dotenv("../.env")
		#load_dotenv("/content/drive/MyDrive/ColabNotebooks/EKA_RAG_Project_v2/.env")
		load_dotenv(".env")
		# print(f"Public_key={os.getenv('LANGFUSE_PUBLIC_KEY')}")
		cls._client = Langfuse(public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),secret_key=os.getenv("LANGFUSE_SECRET_KEY"),base_url=os.getenv("LANGFUSE_BASE_URL"),debug=True)
		return cls._client
	@staticmethod	
	def trace(log:dict):
		client = LangfuseTracer.get_client()
		if (client is None) or  (not client.auth_check()):
			print(f"Authentication Error.Flush not completed.")
			return
		with client.start_as_current_observation(as_type="span",name="eka_request",input=log['query'],) as trace:
			trace.update(
        output = log['answer'],
        metadata ={
          'anomalies' :log['anomalies'],
          'confidence' : log['confidence'],
          'source' : log['source'],
          'chunk_ids':','.join(map(str,log['chunk_ids'])),
				  'rewrite_triggered':log['rewrite_triggered'],
				  'rewritten_query':log['rewritten_query'],
          'progress' : log['progress']
          }
          )

			trace.score(name="query_size_chars",value=len(log['query']))
			trace.score(name='latency_total',value=log['latency']['total'])
			trace.score(name='latency_retrieval',value=log['latency']['retrieval'])
			trace.score(name='latency_reranking',value=log['latency']['reranking'])
			trace.score(name='latency_rewrite',value=log['latency']['rewrite'])
			trace.score(name='latency_generation',value=log['latency']['generation'])
			for i,score in enumerate(log['retrieval_scores']):
				trace.score(name=f"retrieval_score_{i}",value=score)
			for i,score in enumerate(log['reranker_scores']):
				trace.score(name=f"reranker_score_{i}",value=score)
			try:
				client.flush()
				print(f"Flush completed successfully")
			except Exception as e:
				print(f"Flush error:{e}")
# metadata ={
				#'latency_total' :log['latency']['total'],
				#'latency_retrieval' :log['latency']['retrieval'],
				#'latency_reranking' :log['latency']['reranking'],
				#'latency_rewrite' :log['latency']['rewrite'],
				#'latency_generation' :log['latency']['generation'],
				#'retrieval_scores' :log['retrieval_scores'],
				#'reranker_scores' :log['reranker_scores'],
				# 'anomalies' :log['anomalies'],
				# 'confidence' : log['confidence'],
				# 'source' : log['source'],
				# 'chunk_ids':log['chunk_ids']
				# 'rewrite_triggered':log['rewrite_triggered']
				# 'rewritten_query':log['rewritten_query']	
				# }
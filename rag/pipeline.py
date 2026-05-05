from rag.guard import Guard
from config.config import SIMILARITY_THRESHOLD,MAX_ALLOWED_CHUNKS,LOG_PATH,REFUSAL_MESSAGE
# from rag.retriever import Retriever
from rag.generator import Generator
from rewriter.query_rewriter import QueryRewriter

from reranker.hf_reranker import HfReranker,select_chunks,remove_duplicate_chunks
import time
from observability.logger import Logger
from observability.anomaly_detector import AnomalyDetector
from models.groq_model import GroqGenerator
from math import exp
from models.hf_embedding import HFEmbeddingModel
import os
import psutil

#REFUSAL_MESSAGE = "I do not have sufficient information in the knowledge base to answer this question."
def get_mem():
  return psutil.Process(os.getpid()).memory_info().rss/1024/1024

# from math import exp
def sigmoid(x):
  x_float = float(x)
  result = 1 / (1 + exp(-x_float))
  #return f"{result:.17f}"
  return result

class Pipeline :
	# def __init__(self,embedding_model,retriever,generator):
	# 	self.embedding_model = embedding_model
	# 	self.retriever = retriever
	# 	self.generator = generator

	def __init__(self,retriever,generator,embedding_model,groqq):
		self.retriever = retriever
		self.generator = generator
		self.groqq = groqq
		self.hf_embedding_model = embedding_model

	def run(self,query):
		answer = {"message":"Running Tests","Chroma":"Trying","Generator":"Trying","Groq":"Trying","hf_embedding_model":"Trying","QueryRewriter":"Trying","query":query}
		print(f"[MEM]start:{get_mem():.3f}MB \n[Debug]Status:{answer}")
	
		try:
			answer["Chroma"]= "Loaded" if self.retriever.collection.count()>0 else "Loading Failed"
		except Exception as e:
			raise RuntimeError(f"Error getting chroma:{e}\n[Debug]Status:{answer}")
		print(f"[MEM]Chroma start:{get_mem():.3f}MB\n[Debug]Status:{answer}")
		try:
			answer["Generator"]= "Loaded" if self.generator else "Loading Failed"
		except Exception as e:
			raise RuntimeError(f"Error getting Generator:{e}\n[Debug]Status:{answer}")		
		print(f"[MEM]Generator start:{get_mem():.3f}MB\n[Debug]Status:{answer}")
		try:
			answer["Groq"]= "Loaded" if self.groqq else "Loading Failed"
		except Exception as e:
			raise RuntimeError(f"Error getting Groq:{e}\n[Debug]Status:{answer}")    
		print(f"[MEM]Groq start:{get_mem():.3f}MB\n[Debug]Status:{answer}")
		try:
			answer["hf_embedding_model"]= "Loaded" if self.hf_embedding_model else "Loading Failed"
		except Exception as e:
			raise RuntimeError(f"Error getting hf_embedding_model:{e}\n[Debug]Status:{answer}")     
		print(f"[MEM]hf_embedding_model start:{get_mem():.3f}MB\n[Debug]Status:{answer}")
		try:
			qrewriter = QueryRewriter(self.groqq)
			answer["QueryRewriter"]= "Loaded" if qrewriter else "Loading Failed"
		except Exception as e:
			raise RuntimeError(f"Error getting QueryRewriter:{e}\n[Debug]Status:{answer}")
		print(f"[MEM]QueryRewriter start:{get_mem():.3f}MB\n[Debug]Status:{answer}")
		try:
			reranker = HfReranker()
			answer["HfReranker"]= "Loaded" if reranker else "Loading Failed"
		except Exception as e:
			raise RuntimeError(f"Error getting HfReranker:{e}\n[Debug]Status:{answer}")
		print(f"[MEM]HfReranker start:{get_mem():.3f}MB\n[Debug]Status:{answer}")

		return answer

  
	def run_production(self,query):		
		# self.hf_embedding_model = HFEmbeddingModel()
		# self.retriever = Retriever()		
		# groqq = GroqGenerator()
		# self.generator = Generator(groqq)		
		qrewriter = QueryRewriter(self.groqq)
		total_start = time.time()
		latency={"total":0.0,"retrieval":0.0,"reranking":0.0,"rewrite":0.0,"generation":0.0}
		progress ={"embeddings":None,"retrieval":None,"empty_retrieval":None,"reranker":None,"guard":None,"generation":None,"rw_embeddings":None,"rw_retrieval":None,"rw_reranker":None,"rw_guard":None}
		rewrite_triggered = False
		rewrite_success = False
		rewritten_query = None
		retrieval_scores = []
		reranker_scores = []
		chunk_ids = []
		# Embed query
		print(f"[MEM]start:{get_mem():.3f}MB")
		query_embeddings = self.hf_embedding_model.embed([query])[0]
		print(f"[MEM]query_embeddings:{get_mem():.3f}MB")
		print(f"[Debug]query_embeddings->{len(query_embeddings)}")
		progress['embeddings']="Passed"
		# Retrieve Chunks
		t0_retrieval = time.time()
	
		print(f"[Debug]Chroma Collection Count->{self.retriever.collection.count()}")
		results = self.retriever.retrieve(query_embeddings)
		print(f"[MEM]retriever:{get_mem():.3f}MB")			
		print(f"[Debug]Retrieval Count->{len(results)}")
		progress['retrieval']="Passed"
		latency['retrieval'] = round(time.time()-t0_retrieval,3)
		final_result = ({"answer":REFUSAL_MESSAGE,"progress":progress,"latency":latency['total'],"guard_scores":[],"retrieval_scores":[(1-distance) for distance in results['distances'][0]],"reranker_scores_before":[],"reranker_scores_after":[],"confidence":"low","source":None,"chunk_ids":None,'rewrite_triggered':rewrite_triggered,'rewrite_success':rewrite_success})
		if(not results or len(results['documents'][0])==0):
			print(f"[Debug]EmptyRetrieval->{final_result}")
			progress['empty_retrieval']="Passed"
			latency['total'] = round(time.time()-total_start,3)
			self._log(query,final_result,latency,[],[],[],False,None)
			return final_result
		
		# Rerank Chunks
		raw_chunks = []
		# reranker = Reranker()
		reranker = HfReranker()
		for doc,distance,metadata in zip(results['documents'][0],results['distances'][0],results['metadatas'][0]):
				raw_chunks.append({'text':doc,'similarity':1-distance,'metadata':metadata})
		t0_reranking = time.time()
		retrieval_scores = [chunk['similarity'] for chunk in raw_chunks]
		# print(f"retrieval_scores->{retrieval_scores}")
		reranked_chunks = 	reranker.rerank(query=query,chunks=raw_chunks)
		reranker_scores_ = [f"(Reranker->{sigmoid(chunk['reranker_score'])},Similarity->{chunk['similarity']})" for chunk in reranked_chunks]
		# print(f"Reranker Score Before->{reranker_scores}")
		selected_chunks = select_chunks(reranked_chunks,max_chunks=MAX_ALLOWED_CHUNKS)
		reranker_scores = [sigmoid(chunk['reranker_score']) for chunk in selected_chunks]
		# reranker_scores = [f"(Reranker->{sigmoid(chunk['reranker_score'])},Similarity->{chunk['similarity']})" for chunk in selected_chunks]
		# print(f"Reranker Score After Select Chunks->{reranker_scores}")
		reranked_results = {
						'documents': [[chunk['text'] for chunk in selected_chunks]],
						'distances': [[1-chunk['similarity'] for chunk in selected_chunks]],
						'metadatas': [[chunk['metadata'] for chunk in selected_chunks]],
            'reranker_score':[[sigmoid(chunk['reranker_score']) for chunk in selected_chunks]]
						}    
		# reranked_results = {
		# 				'documents': [[chunk['text'] for chunk in reranked_chunks]],
		# 				'distances': [[1-chunk['similarity'] for chunk in reranked_chunks]],
		# 				'metadatas': [[chunk['metadata'] for chunk in reranked_chunks]]
		# 				}
		# reranker_scores = [chunk['reranker_score'] for chunk in reranked_chunks]
		latency['reranking'] = round(time.time()-t0_reranking,3)
		print(f"[MEM]Rerank:{get_mem():.3f}MB")		
		print(f"[Debug]Rerank->{reranker_scores}")
		progress['reranker']="Passed"
		# Guard Chunks using confidence
		# guard_output = Guard.filter_results(results)
		guard_output = Guard.filter_results_v1(reranked_results)
		# {'chunks':filtered_chunks,'retrieval_status':retrieval_status,'top_score':highest_similarity,'gap':diff}
		retrieval_status = guard_output['retrieval_status']
		filtered_chunks = guard_output['chunks']
		guard_scores = [f"(Guard->{chunk['reranker_score']},Similarity->{chunk['similarity']},Confidence->{chunk['confidence']})" for chunk in filtered_chunks]
		# print(f"Guard Scores->{guard_scores}")
		print(f"[MEM]Guard:{get_mem():.3f}MB")
		print(f"[Debug]Guard->{guard_scores}")
		progress['guard']="Passed"
		if(retrieval_status=="REFUSE" or (not filtered_chunks)):
			latency['total'] = round(time.time()-total_start,3)
			self._log(query,final_result,latency,retrieval_scores,reranker_scores,[],rewrite_triggered,rewritten_query)
			# guard_scores = [f"(Guard->{chunk['reranker_score']},Similarity->{chunk['similarity']},Confidence->{chunk['confidence']})" for chunk in filtered_chunks]		
			return final_result
		elif(retrieval_status=="GAP_ZONE"):	
				#query rewrite
			t0_rewrite = time.time()  
			# rewritten_query = qrewriter.rewrite(query) #For Tinyllma   
			rewritten_query = qrewriter.rewrite_with_groq(query)    
			# rewritten_query_embeddings = self.embedding_model.embed([rewritten_query])[0]
			rewritten_query_embeddings = self.hf_embedding_model.embed([rewritten_query])[0]
			print(f"[MEM]rw_eguardmbeddings:{get_mem():.3f}MB")
			print(f"[Debug]rw_eguardmbeddings->{len(rewritten_query_embeddings)}")
			progress['rw_eguardmbeddings']="Passed"
			rewritten_results =  self.retriever.retrieve(rewritten_query_embeddings)
			rewrite_triggered =True
			print(f"[MEM]rw_retrieval:{get_mem():.3f}MB")      
			print(f"[Debug]rw_retrieval_count->{len(rewritten_results)}")
			progress['rw_retrieval']="Passed"
			latency['rewrite'] = round(time.time()-t0_rewrite,3)

			if rewritten_results and len(rewritten_results['documents'][0])>0:
				raw_chunks=[]
				for doc,distance,metadata in zip(results['documents'][0],results['distances'][0],results['metadatas'][0]):
					raw_chunks.append({'text':doc,'similarity':1-distance,'metadata':metadata})
				rw_reranked_chunks = 	reranker.rerank(query=rewritten_query,chunks=raw_chunks)
				rw_selected_chunks = select_chunks(reranked_chunks,max_chunks=MAX_ALLOWED_CHUNKS)
				rw_reranked_results = {
				'documents': [[chunk['text'] for chunk in rw_selected_chunks]],
				'distances': [[1-chunk['similarity'] for chunk in rw_selected_chunks]],
				'metadatas': [[chunk['metadata'] for chunk in rw_selected_chunks]],
        'reranker_score':[[sigmoid(chunk['reranker_score']) for chunk in rw_selected_chunks]]
				}
				print(f"[MEM]rw_reranker:{get_mem():.3f}MB")
				print(f"[Debug]rw_reranker->{len(rewritten_results)}")
				progress['rw_reranker']="Passed"
				rw_guard_output = Guard.filter_results_v1(rw_reranked_results)

				rw_status = rw_guard_output['retrieval_status'] 
				rw_chunks = rw_guard_output['chunks']
				guard_scores = [f"(Guard->{chunk['reranker_score']},Similarity->{chunk['similarity']},Confidence->{chunk['confidence']})" for chunk in rw_chunks]
				if rw_status == "HIGH":
					filtered_chunks = rw_chunks
					rewrite_success=True
				elif rw_status == "GAP_ZONE":
					filtered_chunks = filtered_chunks + rw_chunks
					# filtered_chunks=remove_duplicate_chunks(filtered_chunks)
					filtered_chunks.sort(key=lambda x:x['reranker_score'],reverse=True)
				print(f"[MEM]rw_Guard:{get_mem():.3f}MB")
				print(f"[Debug]rw_Guard->{guard_scores}")
				progress['rw_guard']="Passed"
		# 	answer = self.generator.generate(query,filtered_chunks)
		# else:
		# 	answer = self.generator.generate(query,filtered_chunks)
		if(retrieval_status=="REFUSE" or (not filtered_chunks)):
			latency['total'] = round(time.time()-total_start,3)
			self._log(query,final_result,latency,retrieval_scores,reranker_scores,[],rewrite_triggered,rewritten_query)
			return final_result

		t0_generation = time.time()		
		filtered_chunks=remove_duplicate_chunks(filtered_chunks)	
		# answer = self.generator.generate(query,filtered_chunks[:MAX_ALLOWED_CHUNKS])

		answer = self.generator.generate_with_groq(query,filtered_chunks[:MAX_ALLOWED_CHUNKS],self.groqq)
		# answer ="From LLM"
		print(f"[MEM]Generation:{get_mem():.3f}MB")
		print(f"[Debug]Generation->{answer}")
		progress['generation']="Passed"
		latency['generation'] = round(time.time()-t0_generation,3)
		top_meta = filtered_chunks[0]["metadata"]
		confidence= filtered_chunks[0]['confidence']
		if(retrieval_status=="GAP_ZONE"):
			# latency['total'] = round(time.time()-total_start,3)
			# self._log(query,final_result,latency,retrieval_scores,reranker_scores,[],rewrite_triggered,rewritten_query)
			confidence= 'LOW'
		# chunk_ids = [c['metadata']['chunk_id'] for c in filtered_chunks[:MAX_ALLOWED_CHUNKS] ]
		chunk_ids = [f"{c['metadata']['source']}_{c['metadata']['chunk_id']}" for c in filtered_chunks[:MAX_ALLOWED_CHUNKS] ]
		latency['total'] = round(time.time()-total_start,3)
		final_result = ({"answer":answer,"progress":progress,"latency":latency['total'],"guard_scores":guard_scores,"retrieval_scores":retrieval_scores,"reranker_scores_before":reranker_scores_,"reranker_scores_after":reranker_scores,"confidence":confidence,"source":top_meta["source"],"chunk_id":top_meta["chunk_id"],'rewrite_triggered':rewrite_triggered,'rewrite_success':rewrite_success})
		# final_result = ({"answer":answer,"confidence":confidence,"source":top_meta["source"],"chunk_ids":chunk_ids,'rewrite_triggered':rewrite_triggered,'rewrite_success':rewrite_success})
		self._log(query,final_result,latency,retrieval_scores,reranker_scores,chunk_ids,rewrite_triggered,rewritten_query)

		return final_result

	def _log(self,query,final_result,latency,retrieval_scores,reranker_scores,chunk_ids,rewrite_triggered,rewritten_query):
		logger = Logger.get_instance()
		temp_log = {
					"latency":latency,
					"confidence":final_result.get('confidence','low'),
					"chunk_ids":chunk_ids,
					"rewrite_triggered":rewrite_triggered
					}
		anomalies = AnomalyDetector.detect(temp_log)
		logger.log_request(query=query,answer=final_result.get('answer',''),confidence=final_result.get('confidence','low'),source=final_result.get('source',None),chunk_ids=chunk_ids,retrieval_scores=retrieval_scores,reranker_scores=reranker_scores,rewrite_triggered=rewrite_triggered,rewritten_query=rewritten_query,latency=latency,anomalies=anomalies,progress=final_result.get('progress',None))

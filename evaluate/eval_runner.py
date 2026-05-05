import json
import time
from rag.orchestrator import RAGOrchestrator
# from rag.ragorchestrator import RagOrchestrator
from evaluate.metrics import Metrics
from config.config import REFUSAL_MESSAGE

class EvalRunner:
		
	def __init__(self,dataset_path:str):
			with open(dataset_path,"r") as f :
				self.dataset = json.load(f)
				self.ragorchestrator = RAGOrchestrator()
				self.results = []
			
	def run(self)->list:
		print(f"[EvalRunner] Running evaluation on {len(self.dataset)} queries...\n")
		for item in self.dataset:
				result = self._evaluate_single(item)
				self.results.append(result)
				self._print_progress(result)
			
		return self.results
		
	def _evaluate_single(self,item:dict)->dict:
		query = item['query']
		expected_chunk = item.get('expected_chunk_id',[])
		expected_keywords = item.get('expected_keywords',[])
		should_accept = item.get('should_be_accepted',True)
		should_refuse = not should_accept
		category = item.get('category','unknown')
		difficulty_level = item.get('difficulty_level','unknown')
		
		#Run pipeline and log latency
		start = time.time()
		# response = self.ragorchestrator.run(query)
		# response = self.ragorchestrator.run_test(query)
		response = self.ragorchestrator.run_groq(query)
		latency = round(time.time()-start,3)
		
		#Extract Response
		print(f"[Debug] {response}")
		answer = response.get('answer','')
		retrieved_id = response.get('chunk_id',None)
		print(f"[Debug retrieved_id] {retrieved_id}")
		confidence = response.get('confidence','low')
		rewritten = response.get('rewrite_triggered','False')
		was_refused = (answer == REFUSAL_MESSAGE)
		
		#Calculate metrics
		retrieved_ids = [str(retrieved_id)] if retrieved_id is not None else []
		# retrieved_ids = [str(x) for x in response.get('chunk_ids',[])]
		print(f"[Debug retrieved_ids] {retrieved_ids}")
		precision = Metrics.retrieval_precision(expected_chunk,retrieved_ids)
		recall = Metrics.retrieval_recall(expected_chunk,retrieved_ids)
		f1 = Metrics.f1_score(precision,recall)
		kw_match = Metrics.keyword_match(expected_keywords,answer)
		refusal_ok = Metrics.refusal_correct(should_refuse,was_refused)
		
		return {'id':item['query_id'],'query':query,'category':category,'difficulty_level':difficulty_level,
		'expected_chunk':expected_chunk,'retrieved_ids':retrieved_ids,'precision':precision,'recall':recall,
		'f1':f1,'keyword_match':kw_match,'refusal_correct':refusal_ok,'should_refuse':should_refuse,'was_refused':was_refused,
		'confidence':confidence,'rewrite_triggered':rewritten,'latency_seconds':latency,'answer':answer}
		
	def _print_progress(self,result:dict):
		status = "Success" if (result['f1']>0 or result['refusal_correct']) else 'X'
		print(f"[{status}] {result['id']} | F1 : {result['f1']:.2f} | KW: {result['keyword_match']:.2f} | Refusal:{result['refusal_correct']} | Latency : {result['latency_seconds']}")

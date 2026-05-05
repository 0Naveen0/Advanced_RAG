class Metrics:
	@staticmethod
	def retrieval_precision(expected_chunk_id:list,retrieved_chunk_id:list)->float:
		"""From retrieved how much was relevant"""
		if not retrieved_chunk_id:
			return	0.0
		relevant = set(str(x) for x in expected_chunk_id)
		retrieved = set(str(x) for x in retrieved_chunk_id)
		return len(relevant & retrieved)/len(retrieved)
	
	@staticmethod
	def retrieval_recall(expected_chunk_id:list,retrieved_chunk_id:list)->float:
		"""From what was relevant,how much was retrieved"""
		if not expected_chunk_id:
				return 0.0
		relevant = set(str(x) for x in expected_chunk_id)
		retrieved = set(str(x) for x in retrieved_chunk_id)
		return len(relevant & retrieved)/len(relevant)
		
	@staticmethod
	def f1_score(precision:float,recall:float)->float:
		if precision + recall == 0:
			return 0.0
		return 2*(precision * recall)/(precision + recall)
		
	@staticmethod
	def refusal_correct(should_refuse:bool,was_refused:bool)->bool:
		return should_refuse == was_refused
		
	@staticmethod
	def keyword_match(expected_keywords:list,answer:str)->float:
		"""Ratio of expected keywords found in answer"""
		if not expected_keywords:
				return 0.0
		answer_lower=answer.lower()
		matched = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
		return matched/len(expected_keywords)
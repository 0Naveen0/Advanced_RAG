from sentence_transformers import CrossEncoder # cross-encoder/ms-marco-MiniLM-L6-v2
from config.config import RERANKER_MODEL_NAME,RERANKER_TOP_K,RERANKER_GAP_POSITIVE,RERANKER_GAP_NEGATIVE #3	#top_k = 10

def remove_duplicate_chunks(filtered_chunks:list)->list:
	deduplicated_chunks = []
	seen =set()
	# print(type(filtered_chunks))
	# print(filtered_chunks)
	if not filtered_chunks:
		return filtered_chunks
	for data in (filtered_chunks):
		if isinstance(data, dict):
			meta = data.get('metadata', {})
		elif isinstance(data, list) and len(data) > 0:
            
			if isinstance(data[0], dict):
				meta = data[0].get('metadata', {})
			else:
				continue
		else:
			continue
		# print (f"[Meta]{meta}")
		id = f"{meta.get('source')}_{meta.get('chunk_id')}"
		if id not in seen:
			seen.add(id)
			deduplicated_chunks.append(data)			
	return deduplicated_chunks


def select_chunks(reranked_chunks:list,max_chunks:int = 2)->list:
	
	if not reranked_chunks:
		return []
	seen = set()
	selected_chunk = []
	top_score = reranked_chunks[0]['reranker_score']
	# selected_chunk =  [reranked_chunks[0]]

	for chunk in reranked_chunks:
		key = f"{chunk['metadata']['source']}_{chunk['metadata']['chunk_id']}"
		if key in seen:
			continue
		
		if len(selected_chunk)==0:
			selected_chunk.append(chunk)
			seen.add(key)
			continue

		score = chunk['reranker_score']
		if len(selected_chunk)< max_chunks:
			if top_score > 0 and (score/top_score)>=RERANKER_GAP_POSITIVE :
				selected_chunk.append(chunk)
				seen.add(key)		
			elif top_score<=0 and score>= top_score-RERANKER_GAP_NEGATIVE :
				selected_chunk.append(chunk)
				seen.add(key)

		if len(selected_chunk)>= max_chunks:
			break
	return selected_chunk




class Reranker:
	def __init__(self):
		self.model = None
	
	def get_model(self):
		if self.model is None:
			self.model = CrossEncoder(RERANKER_MODEL_NAME)
		return self.model


		
	# @staticmethod	
	def rerank(self,query:str,chunks:list,top_n:int =RERANKER_TOP_K )->list:
		if not chunks:
			return chunks		
		model = self.get_model()
		pairs = [(query,chunk['text']) for chunk in chunks]
		scores = model.predict(pairs)
		print(scores)
		i=0
		for score,chunk in zip(scores,chunks):
			print(f"Score:{score}\t distance:{chunk['similarity']}Chunk:{chunk}")
			chunk['reranker_score'] = float(score)	
			i+=1		 
		reranked_chunks = sorted(chunks,key=lambda x:x['reranker_score'],reverse = True)		
		#return reranked_chunks[:top_n]
		return reranked_chunks

    #  # Pair scores with original chunks and sort
    #     scored_chunks = []
    #     for i, chunk in enumerate(chunks):
    #         chunk_copy = chunk.copy()  # Avoid modifying original dict
    #         chunk_copy['reranker_score'] = float(scores[i]) # Ensure score is a float
    #         scored_chunks.append(chunk_copy)
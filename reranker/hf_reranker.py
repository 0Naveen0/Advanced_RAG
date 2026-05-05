import requests
import time
import os
from dotenv import load_dotenv
from config.config import RERANKER_MODEL_NAME,RERANKER_TOP_K,RERANKER_GAP_POSITIVE,RERANKER_GAP_NEGATIVE #3	#top_k = 10
load_dotenv()
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

class HfReranker:
  
  def __init__(self):
    self.SPACES_URL =f"{os.getenv('HF_SPACES_RERANKER')}/rerank"

  def rerank(self,query:str,chunks:list,top_n:int =RERANKER_TOP_K )->list:
    if not chunks:
      return chunks  
    docs = [chunk['text'] for chunk in chunks]
    result = self.hf_reranker(query,docs)
    data = result['data']
    scores = [score['score'] for score in data['results']]
    i=0
    for score,chunk in zip(scores,chunks):
      # print(f"Score:{score}\t distance:{chunk['similarity']}Chunk:{chunk}")
      chunk['reranker_score'] = float(score)	
      i+=1		 
    reranked_chunks = sorted(chunks,key=lambda x:x['reranker_score'],reverse = True)		
    #return reranked_chunks[:top_n]
    return reranked_chunks




  def hf_reranker(self,query,docs):
    # print(f"Testing public reranker at :{SPACES_URL}\n")
    # print(f"Query:{query}\n")
    result = {'data': None,'status':'failed','error':'','time_taken':0}
    payload = {
    	"query":query,
    	"documents":docs
    }
    try:
      start_time = time.time()
      response = requests.post(self.SPACES_URL,json=payload,timeout=60)
      if response.status_code==503:
        print("Booting .Retrying in 15s...")
        time.sleep(15)
        return self.hf_reranker(query,docs)
      response.raise_for_status()
      result['data'] = response.json()
      result['status'] = "success"
    
    except requests.exceptions.RequestException as e:
      result['error'] = e;
    result['time_taken'] = time.time()-start_time
    return result
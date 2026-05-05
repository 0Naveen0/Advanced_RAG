#  Create chunks using tokenizer of same model as llm for consistant context window for production alignment and to avoid token oerflow   

# from transformers import AutoTokenizer 
# from config.config import LLM_MODEL_NAME,CHUNK_SIZE,CHUNK_OVERLAP

# CHUNK_SIZE = CHUNK_SIZE
# CHUNK_OVERLAP = CHUNK_OVERLAP

# class Chunker:
# 	def __init__(self):
# 		self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
		
# 	def chunk_text(self,text):
# 		tokens = self.tokenizer.encode(text)
# 		chunks = []
# 		start =0
# 		while start<len(tokens):
# 			end = start + CHUNK_SIZE
# 			chunk_token = tokens[start:end]
# 			chunk_text = self.tokenizer.decode(chunk_token)
# 			chunks.append(chunk_text)
# 			start = start+ CHUNK_SIZE - CHUNK_OVERLAP
# 		return chunks

#Using singleton tokenizer		

from config.model_loader import get_llm 
from config.config import CHUNK_SIZE,CHUNK_OVERLAP

CHUNK_SIZE = CHUNK_SIZE
CHUNK_OVERLAP = CHUNK_OVERLAP

class Chunker:
	def __init__(self):
		model,tokenizer = get_llm()
		self.tokenizer = tokenizer
		
	def chunk_text(self,text):
		tokens = self.tokenizer.encode(text)
		chunks = []
		start =0
		while start<len(tokens):
			end = start + CHUNK_SIZE
			chunk_token = tokens[start:end]
			chunk_text = self.tokenizer.decode(chunk_token)
			chunks.append(chunk_text)
			start = start+ CHUNK_SIZE - CHUNK_OVERLAP
		return chunks




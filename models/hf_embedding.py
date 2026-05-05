import requests
import os
from dotenv import load_dotenv
load_dotenv()
class HFEmbeddingModel:
	def __init__(self):
		self.url = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
		self.HF_TOKEN = os.getenv("HF_TOKEN_WRITE")


	def embed(self,texts):		
		headers = {
			"Authorization": f"Bearer {self.HF_TOKEN}",
			"Content-Type": "application/json"
			}

		# headers = {
		# 	"Authorization": self.HF_TOKEN,
		# 	"Content-Type": "application/json"
		# 	}
		# print(f"URL={self.url} | headers={headers} ")
		response = requests.post(self.url, headers=headers, json={"inputs": texts,"options":{"wait_for_model":True,"use_cache":True}},timeout=60)
		# print(f"[Response_{type(response)}]{response}")
		response.raise_for_status()
		return response.json()
import os
import time
import random
from groq import Groq
from dotenv import load_dotenv
from config.config import TEMPERATURE,MAX_RETRIES,REFUSAL_MESSAGE,GROQ_MODEL

load_dotenv()

class GroqGenerator:

	def __init__(self):
		self.client = Groq(api_key=os.getenv("GROQ_TOKEN"))
		self.model = GROQ_MODEL
		self.temperature = TEMPERATURE
		
	# def build_groq_prompt(query:str,context:list[dict])->list[dict]:
	# 	system_propmt = ("You are a Laravel Assistant.Answer using ONLY provided context." "Cite source file and chunk id for all claims (eg.[FILE:filename.pdf | CHUNKID:1)]" "If answer is not present within the context,say that you do not know" "Do not use internal knowledge")
	# 	context_entries =[]
	# 	for data in context:
	# 		entry =(f"FILE:{data['source']}|CHUNK_ID:{data['chunk_id']}\n" f"CONTENT:{data['content']}")
	# 		context_entries.append(entry)
	# 	context_block = "\n----\n".join(context_entries)
	# 	messages = [
	# 				{"role" : "system","content":system_propmt},
	# 				{"role" : "user","content":f"CONTEXT:\n{context_block}\n\nQuery:{query}"}
	# 	]
	# 	return messages
		
		
	def generate_with_groq(self,messages:list[dict])->str:
		# if self.model != model:
		# 	self.model = model
		max_retries = MAX_RETRIES
		retry_delay = 2
		backoff_factor = 2
		for attempt in range(max_retries):
			try:
				chat_completion = self.client.chat.completions.create(messages=messages,model=self.model,temperature=self.temperature,)
				return chat_completion.choices[0].message.content	
			
			except Exception as e:
				if attempt == max_retries-1:
					print(f"[GroqError]Final attempt failed:{e}")
					return "Sorry, we are unable to process request at this moment."
			sleep_time = (retry_delay * (backoff_factor ** attempt )) + random.uniform(0,1)
			print(f"[Generation]Attempt {attempt+1} failed.Retrying in {sleep_time:.2f}s....")
			time.sleep(sleep_time)
			
		return "[Generation][Total Attempt:{attempt+1}]Sorry, we are unable to process request at this moment."
from config.config import MAX_CONTEXT_TOKENS,MAX_ALLOWED_CHUNKS,REFUSAL_MESSAGE
from config.config import GROQ_MODEL
# from model.groq_model import GROQ_MODEL

class Generator:
	def __init__(self,llm_model):
		self.llm = llm_model
    # self.groq_model = GROQ_MODEL

	def build_context(self,filtered_chunks):
		context = ""
		i=0
		for chunk in filtered_chunks:
			if(i<MAX_ALLOWED_CHUNKS):
				context+= f"Context {i+1}:\n"+chunk["text"]+"\nSource: "+f"{chunk["metadata"]["source"]}"+f"\nChunk Id: {chunk["metadata"]["chunk_id"]}"+"\n\n"
				i+=1
		return context[:MAX_CONTEXT_TOKENS*4]


	def generate_with_groq(self,query,filtered_chunks,model):
		context = self.build_context(filtered_chunks)
		system_prompt_ = ("\nYou are a Laravel Assistant.Answer using ONLY provided context.",
                     "Cite source file and chunk id for all claims (eg.[FILE:filename.pdf | CHUNKID:1)]",
                     "If answer is not present within the context,say that you do not know",
                     "Do not use internal knowledge"
                    )
		system_prompt = '\n'.join(str(x) for x in system_prompt_)
		print(f"System-{system_prompt}")
		PROMPT_TEMPLATE_GROQ = """
				<|begin_of_text|>
        <|start_header_id|>system<|end_header_id|>
        {system_prompt}<|eot_id|>
        <|start_header_id|>user<|end_header_id|>
				
				Context:
				{context}
				
				Query: {query}
				<|eot_id|>
        <|start_header_id|>assistance<|end_header_id|>				
				"""
		messages = [
			{'role':'system','content':system_prompt},
			{'role':'user','content':f'\nContext:\n{context}\n\nQuery:\n{query}'},
			{'role':'assistant','content':''}
		]		
		prompt  = PROMPT_TEMPLATE_GROQ.format(system_prompt=system_prompt,context=context,query=query,REFUSAL_MESSAGE=REFUSAL_MESSAGE)
		print(f"Prompt-{messages}")
		raw_output = model.generate_with_groq(messages)
		print(f"[GROQ_Answer]->{raw_output}")
		return raw_output

	def generate(self,query,filtered_chunks):
		context = self.build_context(filtered_chunks)
		# PROMPT_TEMPLATE = """
		# 			    ### System :
		# 			    You are a Laravel Expert Assistant.

		# 			    ### Rules:
		# 					- Use only the provided context to answer the question.
		# 					- If the answer is not explicitely contained in the context,
		# 						say I can not find this information in the provided context.
		# 					- Cite the chunk id when answering.
		# 					- Do not repeat instructions.
		# 					- Do not use prior knowledge.
		# 					- Do not repeat Knowledge_Base section.
		# 					- Answer concisely.
		# 					- Only output the final answer.

		# 			    ### Knowledge_Base:
		# 			    {context}

		# 	        ### Question:
		# 	        {query}

		# 	        ### Answer:

		# 		  """


		PROMPT_TEMPLATE = """
				<|System|> You are a laravel Expert Assistant.
				Answer using only the provided context.
				If the answer is not in the context,say: {REFUSAL_MESSAGE}</s>
				<|User|>
				Context:
				{context}
				
				Question: {query}
				</s>
				<|assistant|>
				"""
		prompt  = PROMPT_TEMPLATE.format(context=context,query=query,REFUSAL_MESSAGE=REFUSAL_MESSAGE)
		print(f"Filtered Chunks->{filtered_chunks}")
		print(f"Context->{context}")
		print(f"Prompt->{prompt}")
		print(f"LLM -> {self.llm}")
		raw_output = self.llm.generate(prompt)
		# answer = raw_output[len(prompt):].strip()
		print(f"Raw_output -> {raw_output}")
		answer = self.get_answer_from_text(raw_output)
		# return raw_output
		print(f"Answer -> {answer}")
		return answer
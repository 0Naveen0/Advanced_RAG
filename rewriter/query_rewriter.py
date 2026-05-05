# import torch

class QueryRewriter:
    def __init__(self,llm_model=None) -> None:
        self.llm = llm_model
        self.REWRITE_TEMPLATE ="""
				  <|System|> 
             You are a search query optimizer.
             Rewrite the query for better document retrieval.
             Use precise, technical wording.
             Preserve original meaning.
             Return only one rewritten question.</s>          
				  <|User|>				
				    Query: {query}</s>  
				  <|assistant|>
				  """
        # self.REWRITE_TEMPLATE_GROQ ="""
				# <|begin_of_text|>
        # <|start_header_id|>system<|end_header_id|>
        #   You are a search query optimizer.
        #    Rewrite the query for better document retrieval.
        #    Use precise, technical wording.
        #    Preserve original meaning.
        #    Return only one rewritten question.<|eot_id|>
        # <|start_header_id|>user<|end_header_id|>				
				# Query: {query}<|eot_id|>
        # <|start_header_id|>assistant<|end_header_id|>
				# """
        

    def get_answer_from_text(self, text,start_tag,splitter):
        answer =text
        answer_start_tag = start_tag
        mylist = text.split(splitter)
        for item in mylist:
            # print(item)
            if answer_start_tag in item:
                answer = item
        return answer
  
    # @staticmethod
    def rewrite(self, query_text: str):
        prompt = self.REWRITE_TEMPLATE.format(query=query_text)
        result = self.llm.generate(prompt)
        #answer = self.get_answer_from_text(result,"Rephrased Question:","###")
        return result

    def rewrite_with_groq(self, query_text: str):
      system_prompt = """
           You are a search query optimizer.
           Rewrite the query for better document retrieval.
           Use precise, technical wording.
           Preserve original meaning.
           Return only one rewritten question without tag (eg.Rewritten Query: or Rephrased Question: etc ).
           """
      messages = [
			  {'role':'system','content':system_prompt},
			  {'role':'user','content':f'\nQuery:\n{query_text}'},
			  {'role':'assistant','content':''}
		  ]
      result = self.llm.generate_with_groq(messages)    
      return result


        
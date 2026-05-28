from langfuse import Langfuse
import os
from dotenv import load_dotenv
from typing import Any
import logging
from config.constants import REDUCTION_WARNING_THRESHOLD

logger = logging.getLogger(__name__)
class LangfuseTracer:
    _client = None
    
    @classmethod
    def get_client(cls):
        # load_dotenv("../.env")
        #load_dotenv("/content/drive/MyDrive/ColabNotebooks/EKA_RAG_Project_v2/.env")
        load_dotenv(".env")
        # print(f"Public_key={os.getenv('LANGFUSE_PUBLIC_KEY')}")
        cls._client = Langfuse(public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),secret_key=os.getenv("LANGFUSE_SECRET_KEY"),base_url=os.getenv("LANGFUSE_BASE_URL"),debug=True)
        return cls._client
    @staticmethod    
    def trace(log:dict):
        client = LangfuseTracer.get_client()
        if (client is None) or  (not client.auth_check()):
            print(f"Authentication Error.Flush not completed.")
            return
        with client.start_as_current_observation(as_type="span",name="eka_request",input=log['query'],) as trace:
            trace.update(
        output = log['answer'],
        metadata ={
          'anomalies' :log['anomalies'],
          'confidence' : log['confidence'],
          'source' : log['source'],
          'chunk_ids':','.join(map(str,log['chunk_ids'])),
                  'rewrite_triggered':log['rewrite_triggered'],
                  'rewritten_query':log['rewritten_query'],
          'progress' : log['progress']
          }
          )

            trace.score(name="query_size_chars",value=len(log['query']))
            trace.score(name='latency_total',value=log['latency']['total'])
            trace.score(name='latency_retrieval',value=log['latency']['retrieval'])
            trace.score(name='latency_reranking',value=log['latency']['reranking'])
            trace.score(name='latency_rewrite',value=log['latency']['rewrite'])
            trace.score(name='latency_generation',value=log['latency']['generation'])
            for i,score in enumerate(log['retrieval_scores']):
                trace.score(name=f"retrieval_score_{i}",value=score)
            for i,score in enumerate(log['reranker_scores']):
                trace.score(name=f"reranker_score_{i}",value=score)
            try:
                client.flush()
                print(f"Flush completed successfully")
            except Exception as e:
                print(f"Flush error:{e}")

    @staticmethod    
    def emit_langfuse_trace(doc: dict[str,Any],language:str,translation_required: bool,hinglish_detected: bool,success: bool,failure_reason:str | None,)->None :
        client = LangfuseTracer.get_client()
        if (client is None) or  (not client.auth_check()):
            print(f"Authentication Error.Flush not completed.")
            return
        with client.start_as_current_observation(as_type="span",name="adv_rag_language_processor",
        input={
			      "source_id": doc.get("source_id",""),
				    "raw_text_snippet": doc.get("raw_text","")[:200]
			       },) as trace:
            trace.update(
            output = {"translated",success},
            metadata ={
			          "source_type": doc.get("source_type",""),
				        "language_detected": language,
				        "translation_required":translation_required,
				        "hinglish_detected": hinglish_detected,
				        "translated": success,
				        "failure_reason":failure_reason or "",
			        }
            )
            try:
                client.flush()
                logger.debug("langfue trace emitted for source_id = %s",doc.get("source_id"))
                print(f"Flush completed successfully")
            except Exception as e:
                logger.warning("langfus trace failed:%s",e)
                print(f"Flush error:{e}")

    @staticmethod
    def lanfuse_trace_cleaning(source_id,source_type,char_before,char_after,reduction_ratio)->None:
        client = LangfuseTracer.get_client()
        if (client is None) or (not client.auth_check()):
          print(f"[Langfuse]Authentication Error-Flush not completed.")
          return
        with client.start_as_current_observation(as_type="span",name="adv_rag_cleaning",input={"source_id":source_id},) as trace:
            trace.update(
    	      output={"cleaning",success},
    	      metadata ={
    			  		"source_id":source_id,
    			  		"source_type":source_type,
    			  		"char_before":char_before,
    			  		"char_after":char_after,
    			  		"reduction_ratio":round(reduction_ratio,4),
    			  		"reduction_warning":reduction_ratio>REDUCTION_WARNING_THRESHOLD,					
    			  	   },
    			  	)    					 
        try:
          client.flush()
          logger.debug("Langfuse Trace emitted phase cleaning source_id = %s",source_id)
        except Exception as e:
          logger.warning("Langfuse Trace for Phase Cleaning failed:%s",e)
          print(f"[Cleaning]Flush Error:{e}")
    
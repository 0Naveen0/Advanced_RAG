from preprocess.registry import is_ingested,_mark_ingested
from preprocess.persistence import save_docs,is_saved,load_doc
from preprocess.run_translation import run_translation_one
# from preprocess.schema import _derive_source_id
from typing import Optional,Callable
import logging

logger = logging.getLogger(__name__)

def ingest_with_registry(ingest_fn:Callable,source_id:str,*args,**kwargs)->Optional[dict]:
    if is_ingested(source_id):
        print(f"[Registry]Already ingested : {source_id}-Skipping")
        # return None
    else:
        if is_saved(source_id):
            print(f"[Registry]Doc available but missing in registry-recovering")
            doc = load_doc(source_id) 
        else:
            try :
                doc = ingest_fn(*args,**kwargs)
            except Exception as e:
               logger.error("source_id = %s , Connector failed - %s",source_id,e)
               return None
        
            if doc is None:
                logger.error("source_id=%s, Connector returned none - skipping",source_id )
                return None
        
            doc_source_id = doc.get("source_id")
            if doc_source_id != source_id :
                logger.error("source_id mismatch caller -'%s' , doc - '%s' "
                    "skipping to prevent registry/persistance divergance.",source_id,doc_source_id)
                return None  
            try :
                file_path = save_docs(doc)
                logger.info("source_id = %s , persistance to %s",source_id,file_path)
            except Exception as e :
                logger.error("source_id = %s , persistance failed - %s -"
                    "registry not updated to force retry.",source_id,e
                    )
                return None
    
    
        try :
            print(f"_mark_ingested(doc) :{doc}")
            _mark_ingested(doc)
            print(f"[Registry]Saved and registered:{source_id}")
        except Exception as e :
            logger.error(
              "source_id = %s, mark ingested failed: %s-"
              "doc is persistance but not in registry.manual recovery required."
              ,source_id,e
              )
            return None

    enriched = run_translation_one(source_id)
    if enriched is None :
        logger.warning(
            "source_id-%s, translation incomplete -"
            "doc is ingested but not available to cleaning.",
            source_id
        )
        return None
    return enriched
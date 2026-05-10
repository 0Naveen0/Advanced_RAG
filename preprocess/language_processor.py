import json
import logging
import os
import time
from datetime import datetime,timezone
# from pathlib import Path
from typing import Any
from langdetect import detect, LangDetectException
from config.config import MAX_RETRIES,GROQ_MODEL,LANG_HINGLISH,LANG_ENGLISH,LANG_HINDI,_HINDI_MARKERS
from config.path import PENDING_LOG_PATH
from rag.generator import Generator
from observability.langfuse_tracer import LangfuseTracer

logger = logging.getLogger(__name__)

gene = Generator(GROQ_MODEL)

def is_hinglish(text:str)->bool:
    tokens = set(text.lower().split())
    overlap = tokens & _HINDI_MARKERS
    density = len(overlap) / max(len(tokens),1)
    return density >= 0.08

def detect_language(raw_text:str)->tuple[str,bool]:
    try:
        lang = detect(raw_text)
    except LangDetectException:
        logger.warning("Langdetect error marking as -unknown")
        return "unknown",False
        
    if lang ==LANG_HINDI:
        return LANG_HINDI,False
        
    if lang == LANG_ENGLISH:
        if is_hinglish(raw_text):
              return LANG_HINGLISH,True
        return LANG_ENGLISH,False
        
    return "unknown",False

def log_pending_translation(doc:dict[str,Any],language_detected:str,failure_reason:str)->None:
    record : dict[str,str]={
        "source_id": doc.get("source_id",""),
        "source_url": doc.get("source_url",""),
        "source_type": doc.get("source_type",""),
        "raw_text": doc.get("raw_text",""),
        "language_detected": doc.get("language_detected",""),
        "failure_reason": doc.get("failure_reason",""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
       }
    try :
        with PENDING_LOG_PATH.open("a",encoding="utf-8") as f :
            f.write(json.dumps(record,ensure_ascii=False )+"\n")
        logger.info("logged failed translation to %s",PENDING_LOG_PATH)
        
    except OSError as e :
        logger.error("Could not write to pending_translation.json : %s",e)


def build_metadata(doc: dict[str,Any],language:str,translation_required:bool,hinglish_detected:bool,translated_text:str,translated:bool,)->dict[str,Any]:
    meta: dict[str,Any] = dict(doc.get("metadata",{}))
    meta["language"] =    language
    meta["translation_required"] =    translation_required
    meta["hinglish_detected"] =    hinglish_detected
    meta["translated_text"] =translated_text    
    meta["translated"] =    translated
    meta["raw_text"] =    doc.get("raw_text","")
    return meta

def process_document(doc:dict[str,Any])->dict[str,Any] | None:    
    raw_text = doc.get("raw_text","").strip()
    source_id = doc.get("","<unknown>")
    
    if not raw_text    :
        logger.warning("source_id %s has empty raw_text - skipping",source_id)
        return None
    language,hinglish_detected = detect_language(raw_text)
    logger.info("source_id = %s , detected language = %s, hinglish = %s",source_id,language,hinglish_detected)

    translated_text = ""
    translated = False
    translation_required = language != LANG_ENGLISH
    failure_reason: str | None  = None    
    
    if language == LANG_ENGLISH :
        translated_text = raw_text
        translated = True
        logger.info("source_id = %s :is English- pass",source_id)
    else:
        if language == LANG_HINGLISH :
            logger.info("source_id: %s is Hinglish -translating",source_id)
        elif language =="unknown":
            logger.warning("source_id = %s : unknown language- attempting translation",source_id)
            
        translated_text,failure_reason = gene.translate_with_retry(raw_text)
        
        if failure_reason is None:
           translated = True
           logger.info("source_id = %s,translation success. ",source_id)
        else :
            translated =False
            logger.error("source_id = %s, translation failed after %d retries: %s",source_id,MAX_RETRIES,failure_reason)
            log_pending_translation(doc,language,failure_reason)
            
    LangfuseTracer.emit_langfuse_trace(doc=doc,language=language,translation_required=translation_required,hinglish_detected=hinglish_detected,success=translated,failure_reason=failure_reason)
    
    if not translated:
        return None
    enriched = dict(doc)
    enriched["metadata"]    = build_metadata(doc=doc,language=language,translation_required=translation_required,hinglish_detected=hinglish_detected,translated_text=translated_text,translated=translated,)
    return enriched
    
def process_batch(docs:list[dict[str,Any]])->list[dict[str,Any]]:
    results = []
    for doc in docs :
        enriched = process_document(doc)
        if enriched is not None:
            results.append(enriched)
            
    logger.info("Batch complete: %d/%d documents passed language processing.",len(results),len(docs))
    return results



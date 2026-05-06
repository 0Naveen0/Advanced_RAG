import json
import os
from datetime import datetime,timezone
from typing import Optional,Literal
from config.path import REGISTRY_PATH
import logging

logger = logging.getLogger(__name__)
TranslationState = Literal[
    "translation_pending",
    "translation_complete",
    "translation_failed",
]

def _load()->dict:
    if not os.path.exists(REGISTRY_PATH):
        os.makedirs(os.path.dirname(REGISTRY_PATH),exist_ok = True)
        return {}

    with open(REGISTRY_PATH,"r",encoding="utf-8") as f:
        return json.load(f)

def _save(registry:dict)->None:
    with open(REGISTRY_PATH,"w",encoding="utf-8") as f:
        json.dump(registry,f,ensure_ascii=False,indent=2)

def _mark_ingested(doc:dict)->None:
    registry=_load()
    registry[doc["source_id"]]={
      "source_url" : doc["source_url"],
      "source_type":doc["source_type"],
      "published_at":doc["published_at"],
      "ingested_at": datetime.now(timezone.utc).isoformat(),
      "char_count":len(doc["raw_text"]),
    }
    _save(registry)

def is_ingested(source_id: str) -> bool:
    return source_id in _load()

def get_record(source_id:str)->Optional[dict]:
    return _load().get(source_id)

def set_translation_state(source_id:str,state:TranslationState,*,language:str | None=None,hinglish_detected:bool=False,)->None:
    registry = _load()
    if source_id not in registry:
        raise KeyError(
            f"[registry] source_id:{source_id} not found"
            f"mark_ingested must run before set_translation_state."
        )
    registry[source_id]["translation_status"] = state
    registry[source_id]["translation_updated_at"] = datetime.now(timezone.utc).isoformat()

    if language is not None:
        registry[source_id]["language_detected"] = language
    if hinglish_detected:
        registry[source_id]["hinglish_detected"] = True

    _save(registry)
    logger.info("Registry: source_id %s -> %s",source_id,state)


def get_translation_state(source_id:str) -> TranslationState | None:
    record = _load().get(source_id)
    if record is None:
        return None
    return record.get("translation_status")

def is_translation_complete(source_id:str)->bool:
    return get_translation_state(source_id)=="translation_complete"

def list_pending_translation(all_source_ids:list[str])->list[str]:
    registry = _load()
    pending_list = [id for id in all_source_ids if registry.get(id,{}).get("translation_status")!="translation_complete"]
    return pending_list
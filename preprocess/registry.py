import json
import os
from datetime import datetime,timezone
from typing import Optional
from config.path import REGISTRY_PATH

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

def get_record(source_id:str)->Optional[dict]:
    return _load().get(source_id)

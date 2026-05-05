from __future__ import annotations
import hashlib
import re
from datetime import datetime,timezone
from typing import Optional
from preprocess.schema import blank_metadata,validate_connector_output,SchemaValidationError

def _get_trafilatura():
    try:
        import trafilatura
        return trafilatura
    except ImportError:
        raise ImportError("Please install trafilatura:pip install trafilatura")    
        
def _get_traf_config():
    try:
        from trafilatura.settings import use_config
        cfg = use_config()
        cfg.set("DEFAULT","EXTRACTION_TIMEOUT","30")
        return cfg
    except ImportError:
        return None
        
def _derive_source_id(url:str)->str:
    digest = hashlib.sha256(url.encode()).hexdigest()[:12]
    return f"news_{digest}"
    
def _parse_published_at(meta_obj)->str:
    if meta_obj and meta_obj.date:
        raw_date = meta_obj.date.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$",raw_date):
            return f"{raw_date} T00:00:00+00:00"
        return raw_date
    return datetime.now(timezone.utc).isoformat()
    
def ingest_newspaper(url:str,published_at:Optional[str]=None,include_comments:bool=False,favor_precision:bool=True,)->dict:
    if not url or not url.startswith(("http://","https://")):
        raise ValueError(f"Invalid URL:{url!r}. Must start with http:// or https:// ")
    trafilatura = _get_trafilatura()
    config = _get_traf_config()
    print(f"[NewspaperConnector] Fetching:{url}")
    
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Failed to fetch URL:{url}")
    raw_text = trafilatura.extract(downloaded,config=config,include_comments=include_comments,favor_precision=favor_precision,include_tables=True,no_fallback=False,output_format="txt",)
    
    if not raw_text or not raw_text.strip():
        raise ValueError(f"Trafilatura could not extract article from {url}\n May require authenticaton,payment or javascript rendering.")
    print(f"[NewspaperConnector] Extracted:{len(raw_text)}characters")
    traf_meta = trafilatura.extract_metadata(downloaded)
    resolved_published_at =  published_at or _parse_published_at(traf_meta)
    meta = blank_metadata()
    meta["source_type"]="newspaper"
    meta["source_id"]=_derive_source_id(url)
    meta["source_url"]=url
    meta["published_at"]=resolved_published_at
    validated = validate_connector_output(raw_text.strip(),meta)
    print(f"[NewspaperConnector]Schema Validation passed.source_id = {validated['source_id']}")
    return validated
    
def ingest_newspaper_batch(urls:list[str])->list[dict]:
    results = []
    for i,url in enumerate(urls,1):
        print(f"[NewspaperConnector]Batch {i} / {len(urls)}:{url}")
        try:
            doc= ingest_newspaper(url)
            results.append(doc)
        except Exception as e:
            print(f"[NewspaperConnector]Skipped {type(e).__name__}:{e}")
        print(f"[NewspaperConnector]Batch Complete {len(results)}/{len(urls)} succeeded.")
    return results
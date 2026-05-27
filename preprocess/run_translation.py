import logging
import os
from dataclasses import dataclass,field
from typing import Optional
from config.path import DOCS_PATH
from preprocess.persistence import load_doc,save_docs
from preprocess.registry import (is_translation_complete,list_pending_translation,set_translation_state)
from preprocess.language_processor import process_document

logger = logging.getLogger(__name__)



def _list_all_source_ids() -> list[str]:
    if not os.path.exists(DOCS_PATH):
        raise RuntimeError(f"ingested doc directory not found at {DOCS_PATH}\n")

    return[fname[:-5] for fname in os.listdir(DOCS_PATH) if fname.endswith(".json")]


@dataclass
class TranslationRunSummary:
    total :int = 0
    skipped : int = 0
    succeeded: int = 0
    failed : int = 0
    errors : list[str] = field(default_factory=list)
    def log(self) -> None:
        logger.info("Translation run complete | total=%d skipped=%d,succeeded=%d failed=%d,self.total,self.skipped,self.succeeded,self.failed")
        if self.errors:
            logger.warning("Failed source_id = %s",self.errors)

def _process_one(source_id: str, summary: TranslationRunSummary) -> None:
    summary.total+=1
    if is_translation_complete(source_id):
        logger.info("source-id=%s| Already translation_complete-skipping",source_id)
        summary.skipped+=1
        return
    try:
        doc = load_doc(source_id)
    except FileNotFoundError:
        logger.error("source_id =%s | JSON not found in memory-skipping",source_id)
        summary.failed+=1
        summary.errors.append(source_id)
        return
    except Exception as e:
        logger.error("source-id =%s |Load failed = %s",source_id,e)
        summary.errors.append(source_id)
        return
    try:
        set_translation_state(source_id,"translation_pending")
    except KeyError as e:
        logger.error(str(e))
        summary.failed+=1
        summary.errors.append(source_id)
        return

    enriched = process_document(doc)
    if enriched is None:
        set_translation_state(source_id,"translation_failed")
        logger.error("source_id=%s | Mark translation failed in registry",source_id)
        summary.failed+=1
        summary.errors.append(source_id)
        return

    try:
        save_docs(enriched)
    except Exception as e:
        logger.error("source_id=%s | Memory write back failed - %s.",source_id,e)
        summary.failed+=1
        summary.errors.append(source_id)
        return

    meta = enriched.get("metadata",{})
    set_translation_state(
        source_id,"Translation Complete",
        language=meta.get("language"),
        hinglish_detected=meta.get("hinglish_detected",False),
        )
    summary.succeeded+=1
    logger.info("source_id=%s | Translation Complete.",source_id)



def run_translation_one(source_id:str)->Optional[dict]:
    summary = TranslationRunSummary()
    _process_one(source_id,summary)
    if summary.succeeded==1:
        return load_doc(source_id)
    return None

def run_translation() -> TranslationRunSummary:
    logger.info("Translation run starting.......")
    all_ids = _list_all_source_ids()
    logger.info("Corpus size: %d documents found on disk",len(all_ids))
    pending_ids = list_pending_translation(all_ids)
    logger.info("Pending Translation:%d|Complete:%d",len(pending_ids),len(all_ids)-len(pending_ids))
    summary = TranslationRunSummary()
    for source_id in pending_ids:
        _process_one(source_id,summary)
    summary.log()
    return summary

if __name__ == "__main__":
    logging.basicConfig(level= logging.INFO,format="%(asctime)s | %(levelname)s | (%name)s | %(message)s,")
    summary= run_translation()
    print(f"\nRun complete:{summary.succeeded} succeeded," f"{summary.failed} failed,{summary.skipped} skipped" f"of {summary.total} total")
    
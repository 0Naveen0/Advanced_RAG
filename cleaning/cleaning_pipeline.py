import logging
import os
from copy import deepcopy
from typing import Optional

from observability.langfuse_tracer import LangfuseTracer
from config.constants import REDUCTION_WARNING_THRESHOLD

from cleaning.cleaner import assert_raw_text_unchanged,compute_reduction_ratio
from cleaning.cleaner_video import clean_video
from cleaning.cleaner_news import clean_news
from cleaning.cleaner_social import clean_social

logger = logging.getLogger(__name__)

#REDUCTION_WARNING_THRESHOLD = 0.6 # 60% REDUCTION NOTIFICATION default 
SUPPORTED_SOURCE_TYPES = {"youtube","interview","newspaper","social"}

_CLEANER_MAP = {"youtube":clean_video,"interview":clean_video,"newspaper":clean_news,"social":clean_social}

def _route_cleaner(source_type:str):
    cleaner = _CLEANER_MAP.get(source_type)
    if cleaner is None:
        raise ValueError(f"Unknown source type '{source_type}'. " f"Supported Types:{sorted(SUPPORTED_SOURCE_TYPES)}")
    return cleaner
    
def run_cleaning_pipeline(metadata:dict)->dict:
    required_fields = ["source_type","source_id","translated_text","raw_text"]
    missing = [f for f in required_fields if f not in metadata]
    if missing:
        raise KeyError(f"Metadata missing required fields:{missing}. " f"Cannot complete process without proper schema.")
    source_type = metadata["source_type"]
    source_id = metadata["source_id"]
    original_text = metadata["translated_text"]
    if not isinstance(original_text,str):
        raise TypeError(f"translated_text must be a string ,got {type(original_text).__name__}" f"for source_id='{source_id}'. ")
        
    cleaned_metadata = deepcopy(metadata)
    cleaner_fn = _route_cleaner(source_type)
    cleaned_text = cleaner_fn(original_text)
    cleaned_metadata["translated_text"]= cleaned_text
    assert_raw_text_unchanged(metadata,cleaned_metadata,context=source_id)
    char_before = len(original_text)
    char_after = len(cleaned_text)
    reduction_ratio = compute_reduction_ratio(original_text,cleaned_text)
    
    LangfuseTracer.lanfuse_trace_cleaning(source_id,source_type,char_before,char_after,reduction_ratio)

    if reduction_ratio > REDUCTION_WARNING_THRESHOLD:
        logger.warning(
                 "HIGH REDUCTION WARNING | source_id=%s |"
                 "char_before=%d | char_after=%d | reduction_ratio=%.4f | "
                 "Inspect this document - content may have been over-cleaned.",
                 source_id,char_before,char_after,reduction_ratio,
                 )
    else:
        logger.info(
                "Cleaned | source_id=%s |"
                "char_before=%d | char_after=%d | reduction_ratio=%.4f | "
                "Inspect this document - content may have been over-cleaned.",
                source_id,char_before,char_after,reduction_ratio,
                )
        
    return cleaned_metadata
    
def run_cleaning_pipeline_batch(metadata_list:list[dict])->list[dict]:
    results = []
    failures = []
    for i,metadata in enumerate(metadata_list):
        source_id=metadata.get("source_id",f"index_{i}")
        try:
            cleaned = run_cleaning_pipeline(metadata)
            results.append(cleaned)
        except Exception as e:
            logger.error("Cleaning Failed | source_id=%s | error=%s",source_id,str(e),e_info=True,)
            failures.append((source_id,str(e)))
            results.append(metadata)
    if failures:
        failure_summary = "; ".join(f"{sid}:{err} for sid,err in failures")
        raise RuntimeError(
                f"Cleaning pipeline batch completed with {len(failures)} failure(s): "
                f"{failure_summary}"
                )
    return results
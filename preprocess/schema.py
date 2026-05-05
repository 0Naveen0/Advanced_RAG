from __future__ import annotations
from typing import Any
import copy

REQUIRED_FIELDS:dict[str,Any] ={
    "source_type":    str, #yt|newspaper|interview | social
    "source_id":      str, #connector assigned
    "source_url":     str,
    "published_at":   str, #datetime
    "chunk_index":    int, #default 0
    "chunk_total":    int, #default 0
    "language":       str, #default ""
    "hinglish_detected":bool,
    "global_id":      str, #default ""
    "translation_required": bool, #default False
    "translated":      bool,#default False
    "raw_text":        str,
    "translated_text": str,
}
VALID_SOURCE_TYPES = {"youtube","newspaper","interview","social"}

def blank_metadata()->dict[str,Any]:
    """Return fresh metadata dict with all placeholder values"""
    return {
    "source_type":    "",
    "source_id":      "", 
    "source_url":     "",
    "published_at":   "", 
    "chunk_index":    0, 
    "chunk_total":    0,
    "language":       "",
    "hinglish_detected":False,
    "global_id":      "", 
    "translation_required": False,
    "translated":      False,
    "raw_text":        "",
    "translated_text": "",
    }
class SchemaValidationError(Exception):
    """Raised when connector output fails schema validation."""

def validate_metadata(meta:dict[str,Any])->None:
    """All fields should be present with proper type
       Source type must be in VALID_SOURCE_TYPES,raw_text must be filled
    """
    errors:list[str]=[]
    expected = set(REQUIRED_FIELDS.keys())
    actual = set(meta.keys())
    missing = expected - actual
    extra = actual - expected
    if missing :
        errors.append(f"Missing Fields:{sorted(missing)}")
    if extra :
        errors.append(f"Unexpected Fields:{sorted(extra)}")
        
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in meta:
            continue
        value = meta[field]
        if not isinstance(value,expected_type):
            errors.append(
                f"Field '{field}': expected {expected_type.__name__}",
                f"got {type(value).__name__} {value !r}"
            )
            continue
            
    if "source_type" in meta and meta["source_type"] not in VALID_SOURCE_TYPES:
        errors.append(
         f"Source Type must be one of {VALID_SOURCE_TYPES}",
         f"got {meta["source_type"] !r}"
         )
        
            
    if "raw_text" in meta and isinstance(meta["source_type"],str) and not meta["raw_text"].strip():
        errors.append("raw_text must not be empty")
            
    deferred_checks = {
        "chunk_index":   (0,int), 
           "chunk_total":    (0,int),
           "language":       ("",str),
           "global_id":      ("",str), 
           "translation_required": (False,bool),
           "translated":      (False,bool),    
           "translated_text": ("",str),
          }
    for field,(expected_value,_) in deferred_checks.items():
     if field in meta and isinstance(meta[field],type(expected_value)):
       if meta[field] != expected_value:
        errors.append(
            f"Deferred Field {field} must be placeholder {expected_value !r}",
            f"at connector stage ,got {meta[field]!r}"
        )
    if errors:
        raise SchemaValidationError("Schema validation failed:\n"+ "\n".join(f". {e}" for e in errors))
                
def validate_connector_output(raw_text:str,meta:dict[str,Any])->dict[str,Any]:
    meta_ = copy.deepcopy(meta)
    meta_["raw_text"] = raw_text
    validate_metadata(meta_)
    return meta_
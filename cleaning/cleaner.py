import re
import unicodedata
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_NON_PRINTABLE = re.compile(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]")
_HTML_TAGS = re.compile(r"<[^>]{0,200}>",re.IGNORECASE)
_HTML_ENTITIES = re.compile(r"&[a-zA-Z]{2,10};|&#\d{1,6};")
_EXCESSIVE_PUNCTUATION = re.compile(r"([.!?,\-_=*#])\1{3,}")
_MULTIPLE_BLANK_LINES=re.compile(r"\n{3,}")
_TRAILING_WHITESPACE = re.compile(r"[\t]+$",re.MULTILINE)
_LEADING_WHITESPACE = re.compile(r"^[\t]+",re.MULTILINE)
_ZERO_WIDTH = re.compile(r"[\u200B-\u200F\u202A-\u202E\uFEFF\uFFFD]")

def clean_base(text:str)->str:
    if not isinstance(text,str):
      raise TypeError(f"clean_base expected string but got {type(text).__name__}")
    
    if not text.strip():
        return text
      
    text = _ZERO_WIDTH.sub("",text)
    text = unicodedata.normalize("NFC",text)
    text = _HTML_TAGS.sub(" ",text)
    text = _HTML_ENTITIES.sub(" ",text)
    text = _NON_PRINTABLE.sub("",text)
    text= _EXCESSIVE_PUNCTUATION.sub(r"\1\1\1",text)
    text= text.replace("\r\n","\n").replace("\r","\n")
    text = _TRAILING_WHITESPACE.sub("",text)
    text = _LEADING_WHITESPACE.sub("",text)
    text = _MULTIPLE_BLANK_LINES.sub("\n\n",text)
    text = text.strip()
    return text
  
  
def compute_reduction_ratio(original:str,cleaned:str)->float:
    if not original:
      return 0.0
    
    original_len = len(original)
    cleaned_len = len(cleaned)
    return max(0.0,(original_len-cleaned_len)/original_len)
  
def assert_raw_text_unchanged(original_meta:dict,cleaned_meta:dict,context:Optional[str]=None,)->None:
    label = f"[{context}]" if context else ""
    assert original_meta.get("raw_text")==cleaned_meta.get("raw_text"),(f"INTEGRITY VIOLATION {label}:raw_text modified during cleaning.""raw_text is read-only after Phase 2B.")
import re
import logging
from cleaning.cleaner import clean_base

logger = logging.getLogger(__name__)

#[00:xx] (0:xx) 00:xx:xx [xx:xx:xx] (xx:xx)
_TIMESTAMPS = re.compile(r"[\[\(]?\b\d{1,2}:\d{2}(?::\d{2})?\b[\]\)]?",re.IGNORECASE,)

#"Speaker 1 :" "Interviewer:" "HOST:" "Guest x:" "Q:" "A:"
# _SPEAKER_LABELS = re.compile(r"^(?:speaker\s*\d*|interviewer|host|guest\s*\d*|moderator|narrator|q|a)\s*:\s*",re.IGNORECASE | re.MULTILINE,)
_SPEAKER_LABELS = re.compile(r"(?:^|\.\s*)(?:speaker\s*\d*|interviewer|host|guest\s*\d*|moderator|narrator|q|a)\s*:\s*",re.IGNORECASE | re.MULTILINE,)

_FILLERS = re.compile(r"\b(?:"   r"um+|uh+|umm+|uhh+" r"|you\s+know" r"you\s+know\s+what" r"|i\s+mean" r"|like,\s+you\s+know" r"|basically" r"|actually,\s+actually" r"|right\?\s+right" r"|okay\s+so,?\s+okay" r")\b",re.IGNORECASE,)

# _WHISHPER_ARTIFACTS = re.compile(r"\[(?:music|applause|laughter|inaudible|crosstalk|noise|silence|audio\s+only|background\s+noise|indistinct)\]")
_WHISHPER_ARTIFACTS = re.compile(r"\[\s*(?:music|applause|laughter|inaudible|crosstalk|noise|silence|audio\s+only|background\s+noise|indistinct)\s*\]")

_MULTI_SPACE = re.compile(r" {2,}")

_DANGLING_PUNCTUATION = re.compile(r"([,.])\s*\1")

def clean_video(text:str)->str:
    if not isinstance(text,str):
        raise TypeError(f"clean_video expected str but got {type(text).__name__}")
        
    if not text.strip():
        return text
        
    text = _WHISHPER_ARTIFACTS.sub("",text) #Remve whishper tokens
    text = _TIMESTAMPS.sub("",text) #Remove Timestamp
    text = _SPEAKER_LABELS.sub("",text) # Remove speaker labels at line start
    text = _FILLERS.sub("",text) #Remove filler words
    text = _MULTI_SPACE.sub(" ",text) # Remove multi spaces created by removals
    text = _DANGLING_PUNCTUATION.sub(r"\1",text)
    text = clean_base(text)
    return text
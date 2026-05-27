from __future__ import annotations
import os
import hashlib
import tempfile
import subprocess
from datetime import datetime,timezone
# from indic_transliteration import sanscript
# from indic_transliteration.detect import detect as detect_script
from config.path import AUDIO_VIDEO_DOWNLOADS,AUDIO_VIDEO_LOCAL
from typing import Literal
import whisper

from preprocess.schema import blank_metadata,validate_connector_output,SchemaValidationError
_WHISHPER_MODEL = None

def _get_whishper_model(size:str="medium"):
    global _WHISHPER_MODEL
    if _WHISHPER_MODEL is None:
        _WHISHPER_MODEL=whisper.load_model(size)
    return _WHISHPER_MODEL

def _derive_source_id(url:str)->str:
    digest = hashlib.sha256(url.encode()).hexdigest()[:12]
    return f"yt_{digest}"
  
def _download_audio(url:str,output_dir:str=AUDIO_VIDEO_DOWNLOADS)->str:
    # output_template = os.path.join(output_dir,"audio.%(ext)s")
    output_template = os.path.join(output_dir,f"{_derive_source_id(url)}.%(ext)s")
    cmd = [
      "yt-dlp",
    "--quiet",
    "--no-warnings",
    "--extract-audio",
    "--audio-format","wav",
    "--audio-quality","0",
    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "--output",output_template,
    url,
  
  ]
    result = subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode !=0:
        raise RuntimeError(f"yt-dlp failed (exit {result.returncode}):\n{result.stderr.strip()}")
    for fname in os.listdir(output_dir):
      if fname.endswith(".wav"):
        return os.path.join(output_dir,fname)
    raise RuntimeError("yt-dlp completed but no .wav file was found in output directory.")
  
def _transcribe(audio_path:str,model_size="medium",language:str="hi")->str:
    print(f"[YouTube connector]Audio Transcribing with whisper path: '{audio_path}'|model_size:{model_size}| language:{language}")
    # model = whisper.load_model(model_size)
    model = _get_whishper_model(size=model_size)
    result = model.transcribe(audio_path,fp16=False,language=language,task="transcribe")
    return result["text"].strip()
  
def ingest_youtube(url:str,source_type:Literal["youtube","interview"]="youtube",published_at:str|None=None,whisper_model:str="medium",language="hi")->dict:
    if source_type not in ("youtube","interview"):
      raise ValueError(f"source_type must be 'youtube' or 'interview',got {source_type!r} ")
    
    published_at = published_at or datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"[YouTube connector]Downloading audio from :{url}")
        # audio_path = _download_audio(url,tmpdir)
        audio_path=""
        target_audio_path = os.path.join(AUDIO_VIDEO_DOWNLOADS, f"{_derive_source_id(url)}.wav")
        
        if not os.path.exists(target_audio_path):
            os.makedirs(AUDIO_VIDEO_DOWNLOADS, exist_ok=True)
            audio_path = _download_audio(url,AUDIO_VIDEO_DOWNLOADS)
            print(f"[YouTube connector]Audio Saved: {audio_path}")
        else:
            audio_path = target_audio_path  
            print(f"[YouTube connector]Audio Already Saved at: {audio_path}")
                  

        print(f"[YouTube connector]Audio Transcribing with whisper: '{whisper_model}'.....")
        print(f"[YouTube connector]Audio Transcribing with whisper target_audio_path: '{target_audio_path}'| audio_path:{audio_path}.....")
        raw_text = _transcribe(audio_path,model_size=whisper_model,language=language)
        # raw_text = normalize_to_devanagari(raw_text)
        print(f"[YouTube connector]Audio Transcription complete.Lengths: {len(raw_text)}")
    
    meta = blank_metadata()
    meta["source_type"]=source_type
    meta["source_id"]=_derive_source_id(url)
    meta["source_url"]=url
    meta["published_at"]=published_at
    validated = validate_connector_output(raw_text,meta)
    print(f"[YouTube connector]Schema Validation passed.source_id = {validated['source_id']}")
    return validated
  
def ingest_local_video(filepath:str=AUDIO_VIDEO_LOCAL,source_type:Literal["youtube","interview"]="interview",published_at:str|None=None,whisper_model:str="medium",language="hi")->dict:
    if not os.path.exists(filepath):
      raise FileNotFoundError(f"Media file not found {filepath} ")
    
    published_at = published_at or datetime.now(timezone.utc).isoformat()

    print(f"[Video connector]Audio Transcribing Local File: '{filepath}'.....")
    raw_text = _transcribe(filepath,model_size=whisper_model,language=language)
    # raw_text = normalize_to_devanagari(raw_text)
    print(f"[Video connector]Audio Transcription complete.Lengths: {len(raw_text)}")
    digest = hashlib.sha256(filepath.encode()).hexdigest()[:12]  
    source_id = f"vid_{digest}"
    
    meta = blank_metadata()
    meta["source_type"]=source_type
    meta["source_id"]= source_id
    meta["source_url"]=os.path.abspath(filepath)
    meta["published_at"]=published_at
    validated = validate_connector_output(raw_text,meta)
    print(f"[Video connector]Schema Validation passed.source_id = {validated['source_id']}")
    return validated

def normalize_script(text:str)->tuple[str,bool]:
    arabic_chars=sum(1 for c in text if '\u0600'<= c <='\u06FF')
    ratio = arabic_chars/max(len(text),1)
    if ratio > 0.4:
        return text,True
    return text,False
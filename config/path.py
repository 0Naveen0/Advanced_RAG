import os
import shutil
# Configuration File

BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DB = os.path.join(BASE_URL,"db/chroma_db")
RUNTIME_DB = "/tmp/chroma_db"
AUDIO_VIDEO_DOWNLOADS = os.path.join(BASE_URL,"data/downloads/audio_video")
REGISTRY_PATH = os.path.join(BASE_URL,"data/registry/ingestion_registry.json")
DOCS_PATH = os.path.join(BASE_URL,"data/ingested")
if not os.path.exists(RUNTIME_DB):
  try:
    shutil.copytree(REPO_DB,RUNTIME_DB)
    repo_files = sum(len(files) for _, _, files in os.walk(REPO_DB))
    runtime_files = sum(len(files) for _, _, files in os.walk(RUNTIME_DB))
    print(f"Copied {repo_files} files from {REPO_DB} to {RUNTIME_DB}.")
    if repo_files != runtime_files:
      raise RuntimeError(f"Copied {repo_files} files from {REPO_DB} to {RUNTIME_DB}.") 
  except FileExistsError:
    # print(f"[Debug]FileExistsError")
    pass

CHROMA_DB_PATH = RUNTIME_DB


RAW_DOCS_PATH         = f"{BASE_URL}/data/raw_docs/text"

LOG_PATH                = f"{BASE_URL}/observability/logs/requests.json"

PENDING_LOG_PATH    =os.path.join(BASE_URL,"preprocess/logs/pending_translation.json")
# Path(os.getenv("PENDING_TRANSLATION_PATH", "pending_translation.json"))


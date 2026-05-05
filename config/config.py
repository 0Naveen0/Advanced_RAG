import os
import shutil
#Configuration File
# BASE_URL = "/content/drive/MyDrive/ColabNotebooks/EKA_RAG_Project_v2/" # in colab
# BASE_URL = "https://rag-architecture-v2.onrender.com/" # in production

BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DB = os.path.join(BASE_URL,"db/chroma_db")
RUNTIME_DB = "/tmp/chroma_db"
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

EMBEDDING_MODEL_NAME  ="sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL_NAME        = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

#CHROMA_DB_PATH         = f"{BASE_URL}/db/chroma_db"

# BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# EMBEDDING_MODEL_NAME  ="sentence-transformers/all-MiniLM-L6-v2"
# LLM_MODEL_NAME        = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# CHROMA_DB_PATH         = f"{BASE_URL}/db/chroma_db"
TOP_K				           = 7	
RERANKER_MODEL_NAME    = "cross-encoder/ms-marco-MiniLM-L6-v2"
RERANKER_TOP_K         = 3
RERANKER_GAP_POSITIVE = 0.5
RERANKER_GAP_NEGATIVE = 2.0
SIMILARITY_THRESHOLD   = 0.12  #0.08
SIMILARITY_THRESHOLD_ACCEPTED = 0.45

GAP                    =0.05   #0.02
MAX_CONTEXT_TOKENS	   = 1500	
MAX_NEW_TOKENS 		     = 350
TEMPERATURE			       = 0.2
DO_SAMPLE			         = False
TOP_P                  = 0.9
REPETITION_PENALTY    = 1.1
MAX_TIME              = 180.0
GUARD_ACTIVE          = True
CHUNK_SIZE            = 400
CHUNK_OVERLAP         = 50
MAX_ALLOWED_CHUNKS    = 2
# RAW_DOCS_PATH         = "/content/drive/MyDrive/ColabNotebooks/EKA_RAG_Project/data/raw_docs/text"
RAW_DOCS_PATH         = f"{BASE_URL}/data/raw_docs/text"
# RAW_DOCS_PATH         = "/data/raw_docs/text"
# RAW_DOCS_PATH         = "/content/drive/MyDrive/Colab Notebooks/rag-docs"
REFUSAL_MESSAGE = "I do not have sufficient information in the knowledge base to answer this question."
MAX_TOTAL_LATENCY = 45.0
MAX_GENERATION_LATENCY = 30.0
# LOG_PATH                = "/content/drive/MyDrive/ColabNotebooks/EKA_RAG_Project_v2/observability/logs/requests.json"
LOG_PATH                = f"{BASE_URL}/observability/logs/requests.json"

###RATE LIMITER
LIMITER_MAX_REQUESTS  = 10
LIMITER_WINDOW_SECOND = 60

MAX_RETRIES = 3
GROQ_MODEL = "llama-3.3-70b-versatile"


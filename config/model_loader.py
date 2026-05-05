llm_model =None
tokenizer = None
embed_model = None

from transformers import AutoModelForCausalLM,AutoTokenizer
from config.config import EMBEDDING_MODEL_NAME,LLM_MODEL_NAME
from sentence_transformers import SentenceTransformer
import torch

def get_llm():
    global llm_model,tokenizer
    if llm_model is None:
        # model_name = EMBEDDING_MODEL_NAME
        tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
        llm_model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME,dtype=torch.float32)
    return llm_model,tokenizer

def get_embedder():
    global embed_model
    if embed_model is None:
        embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return embed_model

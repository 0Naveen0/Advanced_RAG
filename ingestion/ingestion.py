from models.embedding_model import EmbeddingModel
from rag.retriever import Retriever
from ingestion.chunker import Chunker
from config.config import RAW_DOCS_PATH
import os
import uuid


DOCS_PATH = RAW_DOCS_PATH

def clean_text(text):
  text = text.replace("\r","")
  cleaned_lines = []
  for line in text.split("\n"):
    stripped_line = line.strip()
    if stripped_line: # Only add non-empty lines
      cleaned_lines.append(stripped_line)
  text = "\n".join(cleaned_lines)
  return text


def ingest_documents():
  
  # embedding_model = EmbeddingModel()
  # retriever = Retriever(create_if_missing=True)
  chunker = Chunker()  
  for filename in os.listdir(DOCS_PATH):
    filepath = os.path.join(DOCS_PATH,filename)
    if not os.path.isfile(filepath):
      continue
      with open(filepath,"r",encoding="utf-8") as f:
        text =f.read()
        text = clean_text(text)
        # print(text)
        chunks = chunker.chunk_text(text)
        total_chunks = len(chunks)
        print(chunks)
        print(total_chunks)
        # for idx,chunk in enumerate(chunks):
        #   embedding = embedding_model.embed([chunk])[0]
        #   metadata = {"source":filename,"chunk_id":idx,"total_chunks":total_chunks}
        #   retriever.collection.add(ids=[str(uuid.uuid4())],documents=[chunk],embeddings=[embedding],metadatas=[metadata])
  print("Ingestion Complete.")
	
from flask import Flask,request,jsonify,render_template
from flask_cors import CORS
import importlib
import os
import psutil
import sys
# from rag.orchestrator import RAGOrchestrator
from rag.retriever import Retriever
from rag.generator import Generator
from models.groq_model import GroqGenerator
from models.hf_embedding import HFEmbeddingModel
from rag.pipeline import Pipeline,get_mem
from utils.rate_limiter import RateLimiter
from config.validate_query import validate_query
from config.config import LIMITER_MAX_REQUESTS,LIMITER_WINDOW_SECOND

print("STARTING APP...")
print("PORT:", os.environ.get("PORT"))


app= Flask(__name__)
IS_RENDER = os.environ.get('RENDER') == 'true'
CORS(app)

def log_chroma_files():
  total =0
  for root,dirs,files in os.walk("/tmp/chroma_db"):
    for f in files:
      fp = os.path.join(root,f)
      size_mb = os.path.getsize(fp)/1024/1024
      total+=size_mb
      print(f"[Chromadb]{fp}:{size_mb:.3f}MB")
  print(f"[Chromadb]Total Size:{total:.3f}MB")
# orchestrator = RAGOrchestrator()
print(f"[MEM]before retriever init:{get_mem():.3f}MB")
retriever = Retriever(create_if_missing=False)
log_chroma_files()
chroma_count =0
try:
  chroma_count = retriever.collection.count()
  print(f"Chroma initialized->{retriever.collection.count()}")
  print(f"[MEM]after retriever init:{get_mem():.3f}MB")
except Exception as e:
  print("Chroma init failed",e)
print(f"[MEM]before groqq init:{get_mem():.3f}MB")
groqq = GroqGenerator()
print(f"[MEM]before gene init:{get_mem():.3f}MB")
gene = Generator(groqq)
print(f"[MEM]before hf_embedding_model init:{get_mem():.3f}MB")
hf_embedding_model = HFEmbeddingModel()
print(f"[MEM]before pipeline init:{get_mem():.3f}MB")
try:
  orchestrator = Pipeline(retriever=retriever,generator=gene,embedding_model=hf_embedding_model,groqq=groqq)
except Exception as e:
  raise RuntimeError(f"Error init orchestrator:{e}|[MEM]{get_mem():.3f}MB")
print(f"[MEM]after pipeline init:{get_mem():.3f}MB")
limiter = RateLimiter(max_requests=LIMITER_MAX_REQUESTS,window_seconds=LIMITER_WINDOW_SECOND)

@app.route("/",methods=["GET"])
def index():
  return render_template('index.html')

@app.route("/ask",methods=["POST"])
def ask():
    client_ip = request.remote_addr
    if not limiter.is_allowed(client_ip):
      return jsonify({"answer":"Too many requests.Please wait before trying again","cofidence":"low","source":None,"chunk_id":None}),429
    data = request.json
    query= data.get("query")
    is_valid,result = validate_query(query)
    if not is_valid:
        return jsonify({"error":result}),400
    query =result
   
    # query_embeddings = embeddingModel.embed(query)
    
    # orchestrator = RAGOrchestrator()
    # result = orchestrator.run_v1(query)
    # result = orchestrator.run_groq(query)
    answer = orchestrator.run_production(query)
    # answer = orchestrator.run(query)
    return answer


@app.route("/test",methods=["POST"])
def test():
    data = request.json
    query= data.get("query")
    is_valid,result = validate_query(query)
    if not is_valid:
        return jsonify({"error":result}),400
    query =result
#    answer = f"Test ok........{query}"
    answer = {"message":"Running Tests","Chroma":"Trying","Generator":"Trying","Groq":"Trying","hf_embedding_model":"Trying","QueryRewriter":"Trying","query":query}
    print(f"[MEM]start:{get_mem():.3f}MB \n[Debug]Status:{answer}")
	
    try:
      answer["Chroma"]= "Loaded" if retriever.collection.count()>0 else "Loading Failed"
    except Exception as e:
      raise RuntimeError(f"Error getting chroma:{e}\n[Debug]Status:{answer}")
    print(f"[MEM]Chroma start:{get_mem():.3f}MB\n[Debug]Status:{answer}")
    try:
      query_embeddings = hf_embedding_model.embed([query])[0]
      print(f"[MEM]query_embeddings:{get_mem():.3f}MB")
      print(f"[Debug]query_embeddings->{len(query_embeddings)}")
    except Exception as e:
      raise RuntimeError(f"Error getting query_embeddings:{e}\n[Debug]Status:{answer}")
    try:
      results = retriever.retrieve(query_embeddings)
      print(f"[MEM]retriever:{get_mem():.3f}MB")			
      print(f"[Debug]Retrieval Count->{len(results)}")
    except Exception as e:
      raise RuntimeError(f"Error getting retriever:{e}\n[Debug]Status:{answer}")    
    
    # answer = orchestrator.run(query)
    return answer

@app.route("/health",methods=["GET"])
def health():
  suspicious =["torch","transformers","sentence_transformers","tensorflow","sklearn","scipy","pandas","numpy"]
  loaded = {m:(m in sys.modules) for m in suspicious}
  process = psutil.Process(os.getpid())
  mem_mb = process.memory_info().rss/1024/1024
  return jsonify({"message":"Server Running","Chroma":f"Init({chroma_count})","port":os.environ.get("PORT"),"host_render":IS_RENDER,"memory_mb":mem_mb,"modules":loaded})


if __name__ == "__main__":
    if IS_RENDER :
       app.run(debug=True)# In production
    else:
       app.run(host="0.0.0.0",port=5001) #In colab 

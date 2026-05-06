import json
import os
from config.path import DOCS_PATH

def save_docs(doc:dict)->str:
    os.makedirs(DOCS_PATH,exist_ok=True)
    file_path= os.path.join(DOCS_PATH,f"{doc['source_id']}.json")
    with open(file_path,"w",encoding="utf-8") as f :
        json.dump(doc,f,ensure_ascii=False,indent=2)
    return file_path

def load_doc(source_id:str)->dict:
    file_path= os.path.join(DOCS_PATH,f"{source_id}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No persisted doc for source id:{source_id}")
    with open(file_path,"r",encoding="utf-8") as f:
        return json.load(f)

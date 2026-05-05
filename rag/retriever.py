#Initialize Chroma with persistant path

import chromadb 
from chromadb.config  import Settings
from config.config import CHROMA_DB_PATH,TOP_K

# Use this class if you want to handle embeddings automatically by chroma db for more control and manual embeddings use next version
# class Retriever:
	# def __init__(self,embedding_function):
		# self.client = chromadb.Client(Settings(persist_directory=CHROMA_DB_PATH,is_persistent=True))
		# self.collection = self.client.get_or_create_collection(name = "enterprise_knowledge",embedding_function = embedding_function)
		
	# def retrieve(self,query):
		# results = self.collection.query(query_texts=[query],n_results=TOP_K)
		# return results

# retrive function returns cosine distance not similarity relation is similarity = 1- distance		
class Retriever:
    def __init__(self,create_if_missing=False):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        if create_if_missing:
          self.collection = self.client.get_or_create_collection(name="enterprise_knowledge",metadata={"hnsw:space":"cosine"})
        else:
          try:
            self.collection = self.client.get_collection(name="enterprise_knowledge")
            print(f"[Retriever]Chroma loaded:{self.collection.count()}")
          except Exception as e:
            raise RuntimeError(f"[Debug]Chroma Collection not found at :{CHROMA_DB_PATH}")


    def retrieve(self, query_embeddings):
        try:
          print(f"[Debug]Retrieve from chroma Entered with len :{len(query_embeddings)}")
          results = self.collection.query(query_embeddings=[query_embeddings], n_results=TOP_K, include=["documents", "metadatas", "distances"])
          print(f"[Debug]Retrieve from chroma complete with len :{len(results)}")
          return results
        except Exception as e:
          raise RuntimeError(f"[Debug]Chroma Query Failed :{e}")
  
    def empty_db(self):
        # Correctly call delete_collection on the client, passing the collection name
        self.client.delete_collection(name=self.collection.name)
        print("ChromaDB collection 'enterprise_knowledge' cleared successfully.")
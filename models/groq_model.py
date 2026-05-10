import os
import time
import random
from groq import Groq
from dotenv import load_dotenv
from config.config import GROQ_TEMPERATURE,MAX_RETRIES,REFUSAL_MESSAGE,GROQ_MODEL

load_dotenv()
_groq_client: Groq | None = None
class GroqGenerator:

    def __init__(self):
        global _groq_client
        if _groq_client is None:
            api_key = os.getenv("GROQ_TOKEN")
            if not api_key :
                raise EnvironmentError("GROQ_TOKEN not set")
            _groq_client = Groq(api_key=api_key)
        self.client = _groq_client
        self.model = GROQ_MODEL
        self.temperature = GROQ_TEMPERATURE
        
    def call_groq_translate(self,raw_text: str)->str:
        TRANSLATION_SYSTEM_PROMPT = (
    "You are a professional translator. "
    "The user will provide text that may be in Hindi, Hinglish (mixed Hindi-English), "
    "or another language. "
    "Translate the text into fluent, contextually accurate English. "
    "Preserve the original meaning precisely — do NOT paraphrase or summarise. "
    "Return ONLY the translated English text, with no explanations or commentary."
)
        response = self.client.chat.completions.create(
            model = self.model,
            temperature = self.temperature,
            messages=[
                {"role":"system","content":TRANSLATION_SYSTEM_PROMPT},
                {"role": "user","content":raw_text},
            ],
        )
        translated = response.choices[0].message.content
        if not translated or not translated.strip():
            raise ValueError("Groq returned an empty translation.")
        return translated.strip()
        
        
    def generate_with_groq(self,messages:list[dict])->str:
        # if self.model != model:
        #     self.model = model
        max_retries = MAX_RETRIES
        retry_delay = 2
        backoff_factor = 2
        for attempt in range(max_retries):
            try:
                chat_completion = self.client.chat.completions.create(messages=messages,model=self.model,temperature=self.temperature,)
                return chat_completion.choices[0].message.content    
            
            except Exception as e:
                if attempt == max_retries-1:
                    print(f"[GroqError]Final attempt failed:{e}")
                    return "Sorry, we are unable to process request at this moment."
            sleep_time = (retry_delay * (backoff_factor ** attempt )) + random.uniform(0,1)
            print(f"[Generation]Attempt {attempt+1} failed.Retrying in {sleep_time:.2f}s....")
            time.sleep(sleep_time)
            
        return "[Generation][Total Attempt:{attempt+1}]Sorry, we are unable to process request at this moment."
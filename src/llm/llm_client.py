
from config.setting import settings

class LLMclient:
    def __init__(self):
        from openai import OpenAI
        if not settings.LLM_API_KEY:
            raise ValueError("LLM_API_KEY is not set. Please check your .env file")
        if not settings.LLM_BASE_URL:
            raise ValueError("LLM_BASE_URL is not set. Please check your .env file")
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model = settings.LLM_MODEL

    def generate(self, prompt:str, system_prompt:str|None=None):
        if not prompt or not prompt.strip() :
            return ""
        
        messages = []

        if system_prompt:
            messages.append({
                "role":"system",
                "content":system_prompt
            })
        
        messages.append({
            "role":"user",
            "content":prompt
        })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            content = response.choices[0].message.content

            if content is None:
                return ""

            return content.strip()

        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}") from e
        
_llm_client = None

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMclient()
    
    return _llm_client

def call_llm(prompt:str)->str:
    return get_llm_client().generate(prompt)
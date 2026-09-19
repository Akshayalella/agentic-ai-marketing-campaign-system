from app.core.config import settings
class LLMProvider:
    def generate(self,prompt:str)->str: raise NotImplementedError
class DemoLLMProvider(LLMProvider):
    def generate(self,prompt:str)->str: return "Demo LLM output generated from the structured campaign context."
class OpenAIProvider(LLMProvider):
    def __init__(self): self.key=settings.openai_api_key
    def generate(self,prompt:str)->str:
        if not self.key: return DemoLLMProvider().generate(prompt)
        try:
            from openai import OpenAI
            client=OpenAI(api_key=self.key)
            r=client.chat.completions.create(model=settings.openai_model,messages=[{"role":"system","content":"You are a careful marketing copywriter. Never invent facts or unsupported claims."},{"role":"user","content":prompt}],temperature=.6)
            return r.choices[0].message.content or ""
        except Exception:
            return DemoLLMProvider().generate(prompt)
def get_llm(): return OpenAIProvider() if settings.llm_provider.lower()=="openai" else DemoLLMProvider()

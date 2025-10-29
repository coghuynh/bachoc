from dotenv import load_dotenv
from KG_builder.llm.base.base_model import BaseLLM
from KG_builder.llm.cost.cost_model import GeminiModel, GPTModel
from KG_builder.llm.free.free_model import QwenModel
from KG_builder.llm.cost.async_cost_model import AsyncBaseLLM, AsyncGeminiModel, AsyncGPTModel

FREE_MODELS = {
    "qwen": QwenModel
}
COST_MODELS = {
    "gpt": GPTModel,
    "gemini": GeminiModel
}

ASYNC_COST_MODELS = {
    "gpt": AsyncGPTModel,
    "gemini": AsyncGeminiModel
}

def load_model(model_name: str) -> BaseLLM:
    lower_name = model_name.lower()
    for key, cls in COST_MODELS.items():
        if key in lower_name:
            return cls(model_name=model_name)
    for key, cls in FREE_MODELS.items():
        if key in lower_name:
            return cls(model_name=model_name)
    raise ValueError(f"Unknown model: {model_name}")

def load_async_model(model_name: str) -> AsyncBaseLLM:
    lower_name = model_name.lower()
    for key, cls in ASYNC_COST_MODELS.items():
        if key in lower_name:
            return cls(model_name=model_name)
    raise ValueError(f"Unknown model: {model_name}")    


if __name__ == "__main__":
    
    llm = load_model("gemini-2.0-flash")
    
    # Test 3
    config = {
        "system": "You are my assistance. Just return JSON format by my context I give you",
        "context_template": "{context}"
    }
    
    print(llm.chat(
        "My name is Dang. My hobby is playing games.", json_return=True, **config
    ))
               
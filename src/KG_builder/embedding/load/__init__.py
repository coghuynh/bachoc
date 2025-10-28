from KG_builder.embedding.load.cost import GeminiEmbedModel
from KG_builder.embedding.load.free import QwenEmbedding

gemini: GeminiEmbedModel = GeminiEmbedModel()
qwen: QwenEmbedding = QwenEmbedding(model_name="Qwen/Qwen2.5-0.5B-Instruct")
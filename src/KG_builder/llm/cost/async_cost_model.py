class GeminiModel(CostModel):
    def __init__(self, **args):
        super().__init__(**args)
        self.instance = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        
        
    async def generate_response(self, context: str, **args):
        config = GenerateContentConfig(
            system_instruction=args["system"],
        )
        
        event_loop = asyncio.get_event_loop()
        
        response = await event_loop.run_in_executor(
            None,
            lambda: self.instance.models.generate_content(
                    model=self.name,
                    contents=context, 
                    config=config
                )
        )
        
        return response.text
    
    
class GPTModel(CostModel):
    def __init__(self, **args):
        super().__init__(**args)
        self.client = OpenAI(api_key=os.environ["OPENAI"])
        
    async def generate_response(self, context: str, **args):
        event_loop = asyncio.get_event_loop()
        response = await event_loop.run_in_executor(
            None, 
            lambda: self.client.responses.create(
                model=self.name,
                messages=[
                    {"role": "system", "content" : args["system"]},
                    {"role": "user", "content" : context}
                ]
            )
        )
        response = response.output_text
        
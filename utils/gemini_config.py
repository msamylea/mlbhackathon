import os
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Union
from ratelimit import limits
from google import genai
from PIL import Image

class LLMConfig:
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None, **kwargs):
        self.provider = provider.lower()
        self.model = model
        self.params = kwargs
        self.api_key = self._get_api_key(api_key)

    def _get_api_key(self, provided_key: Optional[str]) -> str:
        if provided_key:
            return provided_key
        env_var_map = {            
            "gemini": "GEMINI_API_KEY",
                    }
        env_var = env_var_map.get(self.provider)
        api_key = os.environ.get(env_var) if env_var else None
     
        return api_key


class BaseLLM(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = self._create_client()

    @abstractmethod
    def _create_client(self):
        pass

    @abstractmethod
    def get_response(self, prompt: str) -> Any:
        pass

    @abstractmethod
    async def get_aresponse(self, prompt: str) -> Any:
        pass

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "parameters": self.config.params
        }
 

class GeminiLLM(BaseLLM):
    def _create_client(self):
        client = genai.Client(
            api_key=self.config.api_key,  
            http_options={"api_version": "v1alpha"}
        )
        return client

    def _prepare_content(self, prompt: Union[str, List[Union[str, Image.Image]]]) -> Union[str, List[Union[str, Image.Image]]]:
        if isinstance(prompt, str):
            return prompt
        elif isinstance(prompt, list):
            return [item if isinstance(item, (str, Image.Image)) else str(item) for item in prompt]
        else:
            return str(prompt)

    @limits(calls=9, period=60)
    def get_response(self, prompt: Union[str, List[Union[str, Image.Image]]]) -> str:
        content = self._prepare_content(prompt)
        response = self.client.models.generate_content(model = self.config.model, contents = content)
        return response.text
    
    @limits(calls=8, period=60)
    async def get_aresponse(self, prompt: Union[str, List[Union[str, Image.Image]]]):
        generation_config = genai.GenerationConfig(**{k: v for k, v in self.config.params.items() if k in ['temperature', 'max_output_tokens', 'top_p', 'top_k']})
        content = self._prepare_content(prompt)
        response = self.client.generate_content(content, generation_config=generation_config, stream=True)
        for chunk in response:
            yield chunk.text
            await asyncio.sleep(0.01)
class LLMFactory:
    @staticmethod
    def create_llm(config: LLMConfig) -> BaseLLM:
        llm_classes = {            
            "google": GeminiLLM,          
      
        }
        if config.provider not in llm_classes:
            raise ValueError(f"Unsupported provider: {config.provider}")
        return llm_classes[config.provider](config)

def get_llm(provider: str, model: str, **kwargs) -> BaseLLM:
    config = LLMConfig(provider, model, **kwargs)
    return LLMFactory.create_llm(config)
# Utility functions

def batch_process(llm: BaseLLM, prompts: List[str]) -> List[str]:
    """Process a batch of prompts and return their responses."""
    return [llm.get_response(prompt) for prompt in prompts]

async def batch_process_async(llm: BaseLLM, prompts: List[str]) -> List[str]:
    """Process a batch of prompts asynchronously and return their responses."""
    async def process_prompt(prompt):
        result = ""
        async for chunk in llm.get_aresponse(prompt):
            result += chunk
        return result
    
    return await asyncio.gather(*[process_prompt(prompt) for prompt in prompts])

def compare_responses(llms: List[BaseLLM], prompt: str) -> Dict[str, str]:
    """Compare responses from multiple LLMs for the same prompt."""
    return {llm.get_model_info()['model']: llm.get_response(prompt) for llm in llms}

async def stream_to_file(llm: BaseLLM, prompt: str, filename: str):
    """Stream the LLM response to a file."""
    with open(filename, 'w') as f:
        async for chunk in llm.get_aresponse(prompt):
            f.write(chunk)
            f.flush()


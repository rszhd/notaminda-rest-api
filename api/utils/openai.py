import os
from typing import List, Callable, Dict, Any
from openai import OpenAI
import tiktoken

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
AI_MODEL = os.environ.get('AI_MODEL')

class OpenaiUtil:
    @staticmethod
    def chat_stream(
        api_key: str = None,
        buffer_size: int = 3,
        messages: List[Dict[str, str]] = [],
        on_stream: Callable[[str], None] = lambda _: None,
        openai_config: Dict[str, Any] = {},
        model: str = None
    ) -> Dict[str, Any]:
        
        model = model if api_key else AI_MODEL
        api_key = api_key or OPENAI_API_KEY
        
        client = OpenAI(api_key=os.environ.get('OPENAI_KEY'))
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.4,
            stream=True,
            **openai_config
        )

        buffer = ""
        chunk_count = 0
        result = ""
        result_total_token_count = 0

        for chunk in stream:
            if chunk.choices[0].finish_reason == "stop":
                if buffer:
                    result += buffer
                    on_stream(result)

                prompt_tokens = OpenaiUtil.count_tokens(model, messages)
                completion_tokens = result_total_token_count

                return {
                    "response": result,
                    "token_usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                }
            else:
                token = chunk.choices[0].delta.content
                if token:
                    buffer += token
                    chunk_count += 1
                    result_total_token_count += 1

                    if chunk_count == buffer_size:
                        result += buffer
                        buffer = ""
                        chunk_count = 0
                        on_stream(result)

        return {
            "response": result + buffer,
            "token_usage": {
                "prompt_tokens": OpenaiUtil.count_tokens(model, messages),
                "completion_tokens": result_total_token_count,
                "total_tokens": OpenaiUtil.count_tokens(model, messages) + result_total_token_count
            }
        }

    @staticmethod
    def count_tokens(model, messages: List[Dict[str, str]]) -> int:
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = 0
        for message in messages:
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens -= 1
        num_tokens += 2
        return num_tokens


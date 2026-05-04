#!/usr/bin/env python3
"""
deepseek_adapter.py — DeepSeek-V4 Integration

Provides seamless access to DeepSeek-V4-Pro (Reasoning) and 
DeepSeek-V4-Flash (Speed) for the Sovereign Research Stack.
Supports both local (Ollama) and API modes.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class DeepSeekV4:
    """
    Unified client for DeepSeek-V4 models.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        local_url: str = "http://localhost:11434",
        use_local: bool = True
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.local_url = local_url
        self.use_local = use_local
        self.api_base = "https://api.deepseek.com/v1"

    def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "deepseek-v4-pro",
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Any]:
        """
        Perform a chat completion.
        """
        if self.use_local:
            return self._chat_local(messages, model, stream, **kwargs)
        else:
            return self._chat_api(messages, model, stream, **kwargs)

    def _chat_api(self, messages, model, stream, **kwargs):
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment or constructor")
            
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def _chat_local(self, messages, model, stream, **kwargs):
        url = f"{self.local_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": kwargs
        }
        
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        if stream:
            return resp # User handles generator
        return resp.json()

# ═══════════════════════════════════════════════════════════════════════════
# Formalization Specialist
# ═══════════════════════════════════════════════════════════════════════════

class DeepSeekProver:
    """
    Specialized agent for Lean 4 formalization using DeepSeek-V4-Pro.
    """
    def __init__(self, client: DeepSeekV4):
        self.client = client

    def formalize(self, mathematical_statement: str) -> str:
        prompt = f"""
You are a Lean 4 formalization expert. 
Convert the following mathematical statement into valid Lean 4 code.
Provide only the code in a fenced code block.

Statement:
{mathematical_statement}
"""
        messages = [{"role": "user", "content": prompt}]
        # Using Qwen 2.5 Coder for local speed and Lean proficiency
        model = "qwen2.5-coder:14b" if self.client.use_local else "deepseek-v4-pro"
        res = self.client.chat(messages, model=model)
        
        if self.client.use_local:
            return res["message"]["content"]
        else:
            return res["choices"][0]["message"]["content"]

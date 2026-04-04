"""
Simple LLM Client for Agricultural Document Processing

This client provides a simple interface to transformer-based models
for generating AI analysis and insights.
"""

import json
from typing import Optional
from transformers import pipeline, AutoTokenizer
import torch


class LLMClient:
    """Simple LLM client using transformers library"""

    def __init__(self, model_name: str = "microsoft/DialoGPT-small"):
        """
        Initialize LLM client

        Args:
            model_name: Name of the model to use
        """
        self.model_name = model_name
        self.generator = None
        self.tokenizer = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the model and tokenizer"""
        try:
            model_name = self.model_name or "microsoft/DialoGPT-small"

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            device = 0 if torch.cuda.is_available() else -1

            self.generator = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=self.tokenizer,
                device=device,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        except Exception as e:
            print(f"Warning: Could not initialize LLM model: {e}")
            self.generator = None

    def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        """
        Generate a response from the LLM

        Args:
            system_prompt: System prompt for context
            user_prompt: User prompt/question
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        if not self.generator:
            return self._generate_fallback_response(user_prompt)

        try:
            full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"

            response = self.generator(
                full_prompt,
                max_new_tokens=256,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )

            if response and len(response) > 0:
                generated_text = response[0]["generated_text"].strip()

                if "{" in generated_text and "}" in generated_text:
                    start = generated_text.find("{")
                    end = generated_text.rfind("}") + 1
                    json_str = generated_text[start:end]

                    try:
                        json.loads(json_str)
                        return json_str
                    except json.JSONDecodeError:
                        pass

                return generated_text

            return self._generate_fallback_response(user_prompt)

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return self._generate_fallback_response(user_prompt)

    def _generate_fallback_response(self, user_prompt: str) -> str:
        """
        Generate a fallback response based on simple rules

        Args:
            user_prompt: Original user prompt

        Returns:
            Fallback JSON response
        """
        fallback_response = {
            "ai_summary": "Application processed with standard extraction methods",
            "risk_flags": [
                {
                    "level": "low",
                    "reason": "Standard processing completed"
                }
            ],
            "missing_insights": [
                "AI analysis temporarily unavailable - using standard processing"
            ],
            "decision_hint": "review"
        }

        return json.dumps(fallback_response, indent=2)
import os
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_aws import ChatBedrockConverse

def get_llm_instance(model_preference: Optional[str] = None) -> Optional[Any]:
    """
    Returns an LLM instance based on available API keys and preference.
    Default preference order: OpenAI -> Google Gemini -> AWS Bedrock.
    """
    try:
        if model_preference == "openai" and os.getenv("OPENAI_API_KEY"):
            print("[LLM Utility] Using OpenAI for LLM.")
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        elif model_preference == "google" and os.getenv("GOOGLE_API_KEY"):
            print("[LLM Utility] Using Google Generative AI for LLM.")
            # gemini-2.5-flash supports system instructions natively, so no conversion needed
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        elif model_preference == "aws" and os.getenv("AWS_ACCESS_KEY_ID"):
            print("[LLM Utility] Using AWS Bedrock for LLM.")
            return ChatBedrockConverse(
                model="anthropic.claude-haiku-4-5-20251001-v1:0",
                temperature=0,
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )

        # Fallback to general check if no specific preference or if preferred not available
        if os.getenv("OPENAI_API_KEY"):
            print("[LLM Utility] Using OpenAI for LLM.")
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        elif os.getenv("GOOGLE_API_KEY"):
            print("[LLM Utility] Using Google Generative AI for LLM.")
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        elif os.getenv("AWS_ACCESS_KEY_ID"):
            print("[LLM Utility] Using AWS Bedrock for LLM.")
            return ChatBedrockConverse(
                model="anthropic.claude-haiku-4-5-20251001-v1:0",
                temperature=0,
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )
        else:
            print("[LLM Utility] No LLM API key found.")
            return None
    except Exception as e:
        print(f"[LLM Utility] LLM initialization failed: {e}")
        return None

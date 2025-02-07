"""OpenAI client utilities"""
from openai import AsyncOpenAI
import json
import asyncio
from typing import Dict, Any
import hashlib
import os
import logging
import shutil
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def clear_cache(self):
        """Remove all cache files"""
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
            logger.info("Cache cleared")
    
    def clear_old_cache(self, days=7):
        """Remove cache files older than specified days"""
        now = datetime.now()
        count = 0
        for file in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, file)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if now - file_time > timedelta(days=days):
                    os.remove(file_path)
                    count += 1
        logger.info(f"Removed {count} old cache files")

# Initialize cache manager
cache_manager = CacheManager()

def init_client():
    """Initialize OpenAI client"""
    return AsyncOpenAI(
        api_key="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"
    )

def get_cache_key(text: str) -> str:
    """Generate cache key from text"""
    return hashlib.md5(text.encode()).hexdigest()

def estimate_tokens(text: str) -> int:
    """Rough token estimate"""
    return len(text.split()) * 1.3

async def get_ai_response_async(prompt: str, client, cache_dir='cache', max_retries: int = 3) -> Dict[str, Any]:
    """Get cached response or call API with retries"""
    # Estimate tokens and cost
    input_tokens = estimate_tokens(prompt)
    logger.info(f"Estimated input tokens: {input_tokens}")
    
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    cache_file = f"{cache_dir}/{cache_key}.json"
    
    # Check cache
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            logger.info("Using cached response (no API cost)")
            return json.load(f)
    
    # Call API if not cached
    for attempt in range(max_retries):
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a JSON generator that only outputs valid JSON objects with the exact structure specified."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = await client.chat.completions.create(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0
            )
            
            # Extract and parse JSON from response
            response_text = response.choices[0].message.content.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]
            result = json.loads(response_text)
            
            # Estimate output tokens and total cost
            output_tokens = estimate_tokens(response_text)
            cost = (input_tokens * 0.03 + output_tokens * 0.06) / 1000
            logger.info(f"Estimated cost: ${cost:.3f}")
            
            # Cache response
            with open(cache_file, 'w') as f:
                json.dump(result, f)
            
            return result
                
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Error in AI response: {str(e)}")
                raise
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(1) 
from openai import OpenAI
from datetime import datetime, timezone
import time

def check_quota():
    # Initialize OpenAI client with API key
    client = OpenAI(api_key='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')
    
    try:
        # Test regular GPT
        print("\nTesting regular GPT-4...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1
        )
        print("Regular GPT-4 is accessible")
        
        # Test fine-tuned model
        print("\nTesting fine-tuned model...")
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:ywx::AsZlkCbv",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1
        )
        print("Fine-tuned model is accessible")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        if "quota" in str(e).lower():
            print("\nIt appears you've hit your quota limit for this model.")

if __name__ == "__main__":
    check_quota() 
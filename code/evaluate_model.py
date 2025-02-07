from openai import OpenAI
import json
import numpy as np

def evaluate_model(model_id, val_file):
    client = OpenAI()
    correct = 0
    total = 0
    
    with open(val_file, 'r') as f:
        for line in f:
            example = json.loads(line)
            
            # Get ground truth
            ground_truth = example['messages'][-1]['content']
            
            # Get model prediction
            response = client.chat.completions.create(
                model=model_id,
                messages=example['messages'][:-1],  # Exclude the assistant's response
                temperature=0
            )
            prediction = response.choices[0].message.content.strip().lower()
            
            # Compare
            if prediction == ground_truth:
                correct += 1
            total += 1
            
    accuracy = correct / total
    print(f"Validation Accuracy: {accuracy:.2%}")
    return accuracy

if __name__ == "__main__":
    model_id = "ft:gpt-4-XXXXX"  # Replace with your fine-tuned model ID
    val_file = "lit/Boosted lit search/Jan2025/finetune_val.jsonl"
    evaluate_model(model_id, val_file) 
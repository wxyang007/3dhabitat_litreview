import pandas as pd
import json
import os

def create_finetune_dataset(excel_file, rootpath):
    # Read the Excel file
    df = pd.read_excel(excel_file)
    
    # Create training examples
    training_data = []
    
    for _, row in df.iterrows():
        # Create the chat format
        messages = [
            {"role": "system", "content": "You are an AI trained to evaluate research papers for relevance. Respond with either 'keep' or 'remove'."},
            {"role": "user", "content": f"""Please evaluate the following research paper for relevance:

Title: {row['Article Title']}
Abstract: {row['Abstract']}
Source: {row['Source Title']}
Research Areas: {row['Research Areas']}

Should this paper be kept or removed? Please respond with either 'keep' or 'remove'."""},
            {"role": "assistant", "content": "keep" if int(row['ifKeep']) == 1 else "remove"}
        ]
        
        # Create the training example
        example = {
            "messages": messages
        }
        
        training_data.append(example)
    
    # Save to JSONL file
    output_file = os.path.join(rootpath, "finetune_dataset.jsonl")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in training_data:
            f.write(json.dumps(item) + '\n')
    
    print(f"Created fine-tuning dataset with {len(training_data)} examples")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    rootpath = '/Users/wenxinyang/Desktop/GitHub/3dhabitat_litreview/lit/Boosted lit search/Jan2025'
    excel_file = os.path.join(rootpath, "newfiles5_train.xlsx")
    create_finetune_dataset(excel_file, rootpath)
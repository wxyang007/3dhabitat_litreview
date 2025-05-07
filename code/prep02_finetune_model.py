from openai import OpenAI
import os

def finetune_model(training_file_path):
    # Initialize the client
    client = OpenAI(api_key='YOUR-KEY')
    
    # Upload the training file
    print("Uploading training file...")
    with open(training_file_path, "rb") as file:
        training_file = client.files.create(
            file=file,
            purpose='fine-tune'
        )
    
    # Create fine-tuning job
    print("Creating fine-tuning job...")
    fine_tuning_job = client.fine_tuning.jobs.create(
        training_file=training_file.id,
        model="gpt-4o-mini-2024-07-18"
    )
    
    print(f"Fine-tuning job created with ID: {fine_tuning_job.id}")
    print("You can monitor the status of your fine-tuning job using the list_models.py script")

if __name__ == "__main__":
    rootpath = '/Users/wenxinyang/Desktop/GitHub/3dhabitat_litreview/lit/Boosted lit search/Jan2025'
    training_file = os.path.join(rootpath, "finetune_dataset.jsonl")
    finetune_model(training_file) 
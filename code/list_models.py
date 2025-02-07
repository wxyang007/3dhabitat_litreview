from openai import OpenAI

# Initialize the client
client = OpenAI()

# List all fine-tuning jobs
jobs = client.fine_tuning.jobs.list()
for job in jobs.data:
    print(f"Job ID: {job.id}")
    print(f"Status: {job.status}")
    print(f"Created at: {job.created_at}")
    print(f"Training files: {job.training_file}")
    print(f"Trained tokens: {job.trained_tokens}")
    if job.finished_at:
        print(f"Finished at: {job.finished_at}")
        print(f"Fine-tuned model: {job.fine_tuned_model}")
    print("---") 
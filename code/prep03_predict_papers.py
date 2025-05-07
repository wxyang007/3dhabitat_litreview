from openai import OpenAI
import pandas as pd
import json
import os
import time

def predict_papers(excel_file, model_name, batch_size=20):
    # Initialize OpenAI client with API key
    client = OpenAI(api_key='YOUR-KEY')

    while True:  # Keep running until all papers are processed
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Define output file
        output_file = os.path.join(os.path.dirname(excel_file), "newfiles5_pred_predictions.xlsx")
        
        # Load existing predictions if file exists
        existing_predictions = {}
        if os.path.exists(output_file):
            existing_df = pd.read_excel(output_file)
            existing_predictions = dict(zip(existing_df['Title'], existing_df['Prediction']))
            print(f"Loaded {len(existing_predictions)} existing predictions")
        
        # Filter out already processed papers
        df = df[~df['Article Title'].isin(existing_predictions.keys())]
        
        # Take only the specified number of remaining papers
        df = df.head(batch_size)
        total_papers = len(df)
        
        if total_papers == 0:
            print("All papers have been processed!")
            break
        
        print(f"\nProcessing batch of {total_papers} new papers...")
        print(f"({len(existing_predictions)} already processed)")
        
        for idx, row in df.iterrows():
            print(f"\nProcessing paper {idx + 1} of {total_papers}")
            print(f"Title: {row['Article Title']}")
            
            # Create the messages format
            messages = [
                {"role": "system", "content": "You are an AI trained to evaluate research papers for relevance. Respond with either 'keep' or 'remove'."},
                {"role": "user", "content": f"""Please evaluate the following research paper for relevance:

Title: {row['Article Title']}
Abstract: {row['Abstract']}
Source: {row['Source Title']}
Research Areas: {row['Research Areas']}

Should this paper be kept or removed? Please respond with either 'keep' or 'remove'."""}
            ]

            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0,
                    max_tokens=10
                )
                prediction = response.choices[0].message.content.strip()
                print(f"Prediction: {prediction}")
                
                # Save single prediction - CHANGED THIS PART
                if os.path.exists(output_file):
                    existing_df = pd.read_excel(output_file)
                else:
                    existing_df = pd.DataFrame(columns=['Title', 'Prediction'])
                
                # Add new prediction, replacing any existing one
                new_row = pd.DataFrame([{'Title': row['Article Title'], 'Prediction': prediction}])
                existing_df = existing_df[existing_df['Title'] != row['Article Title']]  # Remove if exists
                existing_df = pd.concat([existing_df, new_row], ignore_index=True)
                existing_df.to_excel(output_file, index=False)
                
                # Add delay between requests
                if idx < total_papers - 1:  # Don't wait after the last paper
                    wait_time = 30
                    print(f"Waiting {wait_time} seconds before next request...")
                    time.sleep(wait_time)
                
            except Exception as e:
                print(f"Error: {str(e)}")
                
                # Save error prediction - CHANGED THIS PART TOO
                if os.path.exists(output_file):
                    existing_df = pd.read_excel(output_file)
                else:
                    existing_df = pd.DataFrame(columns=['Title', 'Prediction'])
                
                new_row = pd.DataFrame([{'Title': row['Article Title'], 'Prediction': 'ERROR'}])
                existing_df = existing_df[existing_df['Title'] != row['Article Title']]  # Remove if exists
                existing_df = pd.concat([existing_df, new_row], ignore_index=True)
                existing_df.to_excel(output_file, index=False)
                
                # If we hit a quota/rate limit, wait longer and continue
                if "429" in str(e) or "quota" in str(e).lower():
                    wait_time = 300  # Wait 5 minutes on rate limit
                    print(f"Rate limit/quota hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
        
        print(f"\nProcessed batch of {total_papers} papers")
        print(f"Results saved to {output_file}")
        
        # Add delay between batches
        if total_papers == batch_size:  # If we processed a full batch, there might be more
            wait_time = 60
            print(f"\nWaiting {wait_time} seconds before next batch...")
            time.sleep(wait_time)

if __name__ == "__main__":
    # Set path to your prediction file
    rootpath = '/Users/wenxinyang/Desktop/GitHub/3dhabitat_litreview/lit/Boosted lit search/Jan2025'
    excel_file = os.path.join(rootpath, "newfiles5_pred.xlsx")
    
    # Replace with your fine-tuned model name
    model_name = "ft:gpt-4o-mini-2024-07-18:ywx::AsZlkCbv"
    
    # Process papers in batches until complete
    predict_papers(excel_file, model_name, batch_size=20) 
import os
import time
import openai
import pickle
import logging
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from notion_client import Client as NotionClient
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get credentials from .env file
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('DATABASE_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize Notion client
notion = NotionClient(auth=NOTION_API_KEY)

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

def get_notion_entries():
    """Retrieve entries from Notion that are marked 'Ready for Analysis'."""
    try:
        response = notion.databases.query(
            **{
                "database_id": DATABASE_ID,
                "filter": {
                    "property": "Status",
                    "select": {
                        "equals": "Ready for Analysis"
                    }
                }
            }
        )
        return response["results"]
    except Exception as e:
        logging.error(f"Error retrieving Notion entries: {e}")
        return []

def get_youtube_transcription(video_id, retries=3):
    """Retrieve the transcription from a YouTube video with retry logic."""
    for attempt in range(retries):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript])
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} - Error retrieving transcription: {e}")
            time.sleep(5)  # Short delay before retrying
    return None

def load_prompt():
    """Load the prompt template from the 'prompts/analyze_general.txt' file."""
    try:
        with open(os.path.join("prompts", "analyze_general.txt"), "r") as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error loading prompt file: {e}")
        return None

def generate_summary(transcription_text):
    """Generate a summary of the transcription using OpenAI."""
    prompt_template = load_prompt()
    if not prompt_template:
        return None
    
    prompt = prompt_template.replace("{{transcript}}", transcription_text)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16000,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return None

def create_google_doc(title, summary):
    """Create a Google Doc with the summary."""
    try:
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        service = build('docs', 'v1', credentials=creds)
        document = service.documents().create(body={'title': title}).execute()
        document_id = document.get('documentId')
        text = f"### Summary ###\n{summary}"
        requests = [{'insertText': {'location': {'index': 1}, 'text': text}}]
        service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        return f"https://docs.google.com/document/d/{document_id}/edit"
    except Exception as e:
        logging.error(f"Error creating Google Doc: {e}")
        return None

def process_notion_entries():
    """Continuously processes entries in Notion."""
    while True:
        entries = get_notion_entries()
        if not entries:
            logging.info("No new entries found. Sleeping for 5 minutes...")
            time.sleep(300)  # Wait 5 minutes before checking again
            continue
        
        for entry in entries:
            try:
                logging.info(f"Processing entry: {entry['id']}")
                video_url = entry['properties']['Recording']['url']
                video_id = video_url.split('v=')[1] if "v=" in video_url else None
                if not video_id:
                    logging.warning("Invalid YouTube URL format. Skipping entry.")
                    continue
                
                transcription = get_youtube_transcription(video_id)
                if not transcription:
                    logging.warning("Failed to retrieve transcription. Skipping entry.")
                    continue
                
                summary = generate_summary(transcription)
                if not summary:
                    logging.warning("Failed to generate summary. Skipping entry.")
                    continue
                
                title = entry['properties']['Name']['title'][0]['text']['content']
                google_doc_url = create_google_doc(title, summary)
                if not google_doc_url:
                    logging.warning("Failed to create Google Doc. Skipping entry.")
                    continue
                
                logging.info(f"Successfully created Google Doc: {google_doc_url}")
                notion.pages.update(
                    page_id=entry['id'],
                    properties={
                        'Status': {'select': {'name': 'Processed'}},
                        'Auto-Outputs': {'url': google_doc_url}
                    }
                )
            except Exception as e:
                logging.error(f"Error processing entry {entry['id']}: {e}")
            
            logging.info("Waiting 30 seconds before processing next entry...")
            time.sleep(30)  # Avoid rate limits

if __name__ == "__main__":
    process_notion_entries()

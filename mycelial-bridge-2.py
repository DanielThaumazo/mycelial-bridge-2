import os
import openai
import pickle
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from notion_client import Client as NotionClient
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

def get_youtube_transcription(video_id):
    """Retrieve the transcription from a YouTube video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry['text'] for entry in transcript])
        return text
    except Exception as e:
        print(f"Error retrieving transcription: {e}")
        return None

def load_prompt():
    """Load the prompt template from the 'prompts/analyze_general.txt' file."""
    prompt_file_path = os.path.join("prompts", "analyze_general.txt")
    with open(prompt_file_path, "r") as file:
        prompt_template = file.read()
    return prompt_template

def generate_summary(transcription_text):
    """Generate a summary of the transcription using OpenAI."""
    prompt_template = load_prompt()
    prompt = prompt_template.replace("{{transcript}}", transcription_text)

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
    )
    return response['choices'][0]['message']['content'].strip()

def create_google_doc(title, transcription, summary):
    """Create a Google Doc with the transcription and summary."""
    # Load credentials from token.pickle
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    
    service = build('docs', 'v1', credentials=creds)

    # Create a new Google Doc
    document = service.documents().create(body={
        'title': title
    }).execute()

    document_id = document.get('documentId')

    # Insert the transcription and summary into the document
    #text = f"### Transcription ###\n{transcription}\n\n### Summary ###\n{summary}"
    text = f"### Summary ###\n{summary}"
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1,
                },
                'text': text
            }
        }
    ]

    # Update the document with the transcription and summary
    service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
    
    return f"https://docs.google.com/document/d/{document_id}/edit"

def process_notion_entries():
    """Process each entry in the Notion database."""
    entries = get_notion_entries()
    for entry in entries:
        # Print all keys to debug if needed
        print(entry['properties'].keys())
        
        # Get the YouTube URL from the 'Recording' field
        video_url = entry['properties']['Recording']['url']
        video_id = video_url.split('v=')[1]  # Assuming typical YouTube URL format
        transcription = get_youtube_transcription(video_id)

        if transcription:
            summary = generate_summary(transcription)

            # Get the title of the document from the 'Name' field
            title = entry['properties']['Name']['title'][0]['text']['content']  
            google_doc_url = create_google_doc(title, transcription, summary)
            print(f"Created Google Doc: {google_doc_url}")

            # Update the Notion entry with the generated Google Doc URL
            notion.pages.update(
                page_id=entry['id'],
                properties={
                    'Status': {
                        'select': {
                            'name': 'Processed'
                        }
                    },
                    'Auto-Outputs': {
                        'url': google_doc_url
                    }
                }
            )

if __name__ == "__main__":
    process_notion_entries()

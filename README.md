Here’s a detailed `README.md` file for your project, which includes information on how to set up each required application and necessary steps for running the script.

### README.md

```markdown
# Mycelial Bridge - Automated YouTube Transcription and Google Docs Summary

This Python script automates the process of retrieving YouTube video transcriptions from Notion, generating summaries using OpenAI's GPT models, and creating Google Docs with the summary. It updates the Notion entry with the generated Google Doc link for easy reference.

## Prerequisites

1. **Python 3.7+**: Ensure you have Python installed. You can download it from [here](https://www.python.org/downloads/).

2. **Google API Client Library**: This is required for interacting with Google Docs.

3. **OpenAI API**: To generate summaries using OpenAI's GPT models.

4. **Notion API**: To retrieve and update entries in your Notion database.

## Setup Instructions

### 1. Clone the Repository

Clone the project to your local machine:

```bash
git clone https://github.com/your-repo/mycelial-bridge.git
cd mycelial-bridge
```

### 2. Install Required Packages

Create a virtual environment and install the required Python libraries:

```bash
# Create a virtual environment
python -m venv env

# Activate the virtual environment
# For Windows:
env\Scripts\activate
# For MacOS/Linux:
source env/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Set Up Notion API

1. Go to [Notion Integrations](https://www.notion.so/my-integrations) and create a new integration.
2. Copy your Notion API key and share your database with the integration.

3. Update the `.env` file with your Notion API key and database ID:

```bash
NOTION_API_KEY=your_notion_integration_key
DATABASE_ID=your_notion_database_id
```

### 4. Set Up OpenAI API

1. Go to [OpenAI API Keys](https://beta.openai.com/account/api-keys) and generate an API key.
2. Update the `.env` file with your OpenAI API key:

```bash
OPENAI_API_KEY=your_openai_api_key
```

### 5. Set Up Google API for Docs

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2. Enable the **Google Docs API** and **Google Drive API** for this project.
3. Create OAuth 2.0 credentials for the application by selecting **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**.
4. Download the `credentials.json` file.
5. Run the `getOAuthToken.py` script to authenticate and generate the `token.pickle` file:

```bash
python getOAuthToken.py
```

The script will guide you through logging in via your browser. The `token.pickle` file will be created, which stores your access token for future interactions with Google Docs.

### 6. Set Up YouTube Transcript API

No additional setup is required, but make sure the `youtube-transcript-api` package is installed (included in `requirements.txt`).

## Running the Script

To run the script and process entries from Notion, simply execute:

```bash
python mycelial-bridge-2.py
```

The script will:

1. Retrieve entries marked as "Ready for Analysis" from your Notion database.
2. Extract the YouTube video ID from the "Recording" field.
3. Fetch the transcription from YouTube.
4. Generate a summary using OpenAI GPT.
5. Create a Google Doc with the summary.
6. Update the Notion entry with the link to the created Google Doc and mark it as "Processed."

## Folder Structure

```bash
.
├── prompts/
│   └── analyze_general.txt      # Template for generating the summary
├── mycelial-bridge-2.py         # Main Python script
├── getOAuthToken.py             # Script to generate Google OAuth token
├── token.pickle                 # Generated Google OAuth credentials
├── .env                         # Environment variables for API keys
└── README.md                    # This file
```

## Required Environment Variables

The `.env` file should contain the following variables:

```bash
NOTION_API_KEY=your_notion_integration_key
DATABASE_ID=your_notion_database_id
OPENAI_API_KEY=your_openai_api_key
```

## Additional Information

- **Google OAuth Refresh**: If your Google OAuth token expires, you can refresh it by re-running the `getOAuthToken.py` script.
- **Notion Field Requirements**: Ensure your Notion database includes the following fields:
  - `Recording` (URL) - The YouTube video URL.
  - `Name` (Title) - The title of the entry.
  - `Auto-Outputs` (URL) - Where the generated Google Doc link will be stored.
  - `Status` (Select) - Used to track the processing status.

## License

This project is licensed under the MIT License.
```

### Explanation:
- **Prerequisites**: Lists the required applications and Python libraries.
- **Setup Instructions**: Step-by-step instructions to set up Notion, OpenAI, Google Docs, and YouTube Transcript API.
- **Running the Script**: Shows how to run the script to automate the workflow.
- **Folder Structure**: Provides an overview of the project’s folder and file structure.
- **Environment Variables**: Lists the variables required for the `.env` file.

Let me know if you need further adjustments or additions!
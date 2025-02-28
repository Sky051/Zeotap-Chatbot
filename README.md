# CDP Assistant Chatbot

A web-based chatbot that answers "how-to" questions about Customer Data Platforms (CDPs) including Segment, mParticle, Lytics, and Zeotap. The chatbot extracts relevant information from official documentation to provide accurate and helpful responses.

## Features

- Answers questions about four major CDPs:
  - Segment
  - mParticle
  - Lytics
  - Zeotap
- Handles various types of "how-to" questions
- Extracts relevant information from official documentation
- Provides code examples and API details when available
- Clean and modern web interface
- Real-time responses

## Technical Stack

- **Backend**: Python/Flask
- **Frontend**: HTML/CSS/JavaScript
- **Documentation Processing**: BeautifulSoup4
- **Caching**: File-based caching system

## Project Structure

```
.
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── templates/             
│   └── index.html         # Web interface template
├── chatbot/
│   ├── __init__.py
│   ├── chatbot.py         # Main chatbot logic
│   ├── question_handler.py # Question processing
│   ├── docs_extractor.py  # Documentation extraction
│   └── platform_extractors/
│       ├── __init__.py
│       ├── base_extractor.py
│       ├── segment_extractor.py
│       ├── mparticle_extractor.py
│       ├── lytics_extractor.py
│       └── zeotap_extractor.py
```

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cdp-assistant-chatbot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Open the web interface in your browser
2. Type your question in the input field
3. Press Enter or click "Ask" button
4. Wait for the chatbot's response

Example questions:
- "How do I set up a new source in Segment?"
- "How can I create a user profile in mParticle?"
- "How do I build an audience segment in Lytics?"
- "How can I integrate my data with Zeotap?"

## Features in Detail

### Question Processing
- Handles variations in question phrasing
- Identifies the relevant CDP platform
- Extracts specific tasks or actions being asked about

### Documentation Extraction
- Fetches content from official documentation
- Processes and cleans HTML content
- Caches results for improved performance
- Extracts code examples and API details

### Response Formatting
- Provides clear, structured answers
- Includes relevant code examples when available
- Links to official documentation
- Shows API details when applicable

## Caching System

The chatbot implements a file-based caching system to:
- Reduce load on documentation servers
- Improve response times
- Store frequently accessed content
- Cache duration: 24 hours

## Error Handling

The system includes comprehensive error handling for:
- Invalid questions
- Failed documentation fetches
- Processing errors
- API failures

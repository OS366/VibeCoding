# VibeCoding - Text Analysis Application

A simple web-based application that analyzes text for grammatical errors, tone, and provides improvement suggestions using OpenAI's API.

## Features

- Text input via a user-friendly interface
- Analysis of grammatical errors
- Tone detection
- Formality level assessment
- Suggestions for text improvement
- Beautiful, responsive UI

## Requirements

- Python 3.7+
- Flask
- OpenAI API key

## Installation

1. Clone this repository

```bash
git clone https://github.com/yourusername/VibeCoding.git
cd VibeCoding
```

2. Create and activate a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages

```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key

```bash
# Create a .env file in the project root
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

## Usage

1. Start the Flask server

```bash
python app.py
```

2. Open your web browser and navigate to `http://127.0.0.1:5003`

3. Enter text in the input box and click the "Analyze" button

4. View the results of the text analysis

## License

This project is licensed under the terms of the license included in the repository.

## Note

Remember to keep your OpenAI API key confidential and never commit it to a public repository.

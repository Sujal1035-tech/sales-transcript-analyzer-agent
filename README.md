# Sales Transcript Analyzer Agent

This project is a specialized tool designed to process and analyze sales call transcripts. It focuses on conversations in Hindi and Hinglish, providing automated insights into customer intent, key takeaways, and call quality.

The analyzer uses Google Gemini to interpret the transcript, automatically identifying the roles of the agent and the customer without requiring manual speaker labels.

## Key Features

- **Automated Preprocessing**: Cleans raw transcripts by removing stuttered words and merging consecutive segments from the same speaker.
- **Role Inference**: Intelligently determines who is the agent and who is the customer based on conversational context.
- **Comprehensive Analysis**: Provides a structured summary, identifies customer objections, captures agent resolutions, and rates the call on a scale of 1-5.
- **Multilingual Support**: Specifically optimized to handle the nuances of Hindi and Hinglish sales dialogues.


## Project Structure

- `src/preprocessor.py`: Handles data cleaning and dialogue formatting.
- `src/analyzer.py`: Manages communication with the Gemini API.
- `src/config.py`: Contains API configurations and system prompts.
- `src/logger.py`: Handles logging.
- `src/processor.py`: Handles processing.
- `test_one.py`: A demonstration script for individual transcript testing.

### Prerequisites

- Python 3.11 or higher.
- [uv](https://github.com/astral-sh/uv) installed on your system.
- A Google Gemini API Key (available via [Google AI Studio](https://aistudio.google.com/app/apikey)).

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Sujal1035-tech/sales-transcript-analyzer-agent.git
   cd sales-transcript-analyzer-agent
   ```

2. Initialize the environment and install dependencies:
   ```bash
   uv sync
   ```

3. Configure your environment:
   - Create a `.env` file in the root directory.
   - Add your Gemini API key:
     ```env
     GEMINI_API_KEY=your_actual_key_here
     ```

## Usage

You can run the built-in test script to see the analyzer in action with a sample transcript:

```bash
uv run test_one.py
```

The script will output a formatted analysis, including the summary, takeaways, and the calculated intent/rating.


## License

This project is for internal and educational purposes.

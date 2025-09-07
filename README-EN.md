# Benchmark Calculator Bot

Telegram bot for processing and analyzing benchmark data from various sources.

## Overview

This bot is designed to receive benchmark files from users, automatically detect their format, parse the data, and generate detailed reports in XLSX and CSV formats. It supports multiple benchmark formats including CapFrameX, MSI Afterburner, and custom formats.

## Features

- Automatic format detection
- Support for multiple benchmark formats:
  - CapFrameX benchmark files (with automatic merging of multiple files)
  - MSI Afterburner + RivaTuner Statistics Server
  - Custom format (CSV, TSV, JSON)
- Detailed statistical analysis
- Report generation in XLSX and CSV formats
- Support for both standard Telegram API and custom/local API servers
- Webhook and polling modes

## Getting Started

### Prerequisites

- Python 3.10+
- Telegram Bot Token (obtain from [@BotFather](https://t.me/BotFather))

### Installation

1. Clone the repository:
```
bash git clone <repository-url>   
cd BenchmarkCalculatorBot
```
2. Install dependencies:
```
bash   
pip install -r requirements.txt
```
3. Create a `.env` file based on `.env.example` and configure your bot token:
```
env   
BOT_TOKEN=your_actual_bot_token_here
```
### Usage

1. Start the bot:
```
bash   
python main.py   
```
2. In Telegram, find your bot and send it a benchmark file.

3. The bot will automatically detect the format, process the data, and return detailed reports.

### Supported File Formats

1. **CapFrameX**: JSON files from CapFrameX benchmarking tool
   - Multiple files are automatically merged into a single report
   - Detailed frame time analysis

2. **MSI Afterburner**: Text files from MSI Afterburner + RivaTuner Statistics Server
   - Frame rate data extraction
   - Statistical analysis

3. **Custom Format**: Generic parser for various CSV, TSV, and JSON formats
   - Flexible data processing

## Project Structure
```
BenchmarkCalculatorBot/   
├── config/ # Configuration files   
├── handlers/ # Telegram message handlers   
├── parsers/ # Benchmark file parsers   
├── services/ # Processing services   
├── utils/ # Utility functions   
├── main.py # Main application entry point   
├── webhook_server.py # Webhook server implementation   
└── ssl_generator.py # SSL certificate generator for webhook   
```
## License

This project is licensed under the MIT License - see the LICENSE file for details.

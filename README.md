# MangaLibParser

MangaLibParser is a Python-based manga scraper for downloading manga from [mangalib.me](https://mangalib.me). The tool saves manga chapters locally as images and offers PDF conversion functionality (Work in Progress).

## Features

- Download manga chapters with all pages
- CLI interface for easy usage
- PDF export capability (WIP)
- Supports both Windows and Linux environments
- Lightweight and easy to configure

## Requirements

- Python 3.12 or higher
- pip package manager
- Internet connection

## Installation

### Windows

1. Clone the repository:
```powershell
git clone https://github.com/wandderq/MangaLibParser
cd MangaLibParser
```

2. Install Python 3.12+ if not alreday installed:
- Download from [python.org](https://python.org)
- Make sure to check "Add Python to PATH" during installation

3. (Optional) Create a virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

4. Install dependencies:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux

You can just use [install.sh script](install.sh) or install step-by-step:
1. Clone the repository:
```bash
git clone https://github.com/wandderq/MangaLibParser
cd MangaLibParser
```

2. Install Python 3.12+:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

3. (Optional) Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

4. Install dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Usage
After installation, you can run the parser with:
```bash
python mlibparser.py --help
```

## License
This project is licensed under the [MIT License](LICENSE)
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
```bash
python mlibparser.py --help
```
```
    usage: mlibparser.py [-h] [-v] [-q] [-c CHAPTERS] [-i] [-o OUTPUT_DIR] [--pdf] [-s] url

    Simple mangalib.me manga parser

    positional arguments:
    url                   Url to mnga page. Ex: https://mangalib.me/ru/manga/7965--chainsaw-man

    options:
    -h, --help            show this help message and exit
    -v, --verbose         Verbose mode. Shows debug logs
    -q, --quiet           Quiet mode. Shows only warn/err/crit logs
    -c CHAPTERS, --chapters CHAPTERS
                            Chapters to download (number or from-to range). Ex: 1-100
    -i, --info            Shows manga info
    -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Output directory, defaults setted to 'Manga'. Downloading like this: /output/path/manga-name/chapters...
    --pdf                 Save manga chapters in .pdf format
    -s, --simple-names    Use simple names for chapters

    For example: 'python mlibparser.py https://mangalib.me/ru/manga/3595--kimetsu-no-yaiba -c 2-13 -iv' downloads 'Kimetsu no Yaiba' chapters from 2 to 13, shows
    manga info and debug logs
```

## License
This project is licensed under the [MIT License](LICENSE)
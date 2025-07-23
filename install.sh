#!/usr/bin/bash

echo "Updating & Upgrading packages"
sudo apt update -y
sudo apt upgrade -y

echo "Installing Python 3.12+ and git"
sudo apt install python3 python3-pip git -y

echo "Cloning repository"
git clone https://github.com/wandderq/MangaLibParser
cd MangaLibParser
chmod +x mlibparser.py

echo "Creating python virtual env"
python -m venv .venv
source .venv/bin/activate

echo "Installing dependencies"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Done!"
./mlibparser.py --help
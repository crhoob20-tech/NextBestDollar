#!/bin/bash
# Double-click this file to start the NextBestDollar web experience.
set -e

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from python.org, then open this file again."
  read -r -p "Press Return to close. "
  exit 1
fi

if [ ! -x ".web-venv/bin/python" ]; then
  echo "Preparing NextBestDollar for the first time..."
  python3 -m venv .web-venv
fi

if ! .web-venv/bin/python -c "import streamlit, pandas" >/dev/null 2>&1; then
  echo "Installing the web app requirements..."
  .web-venv/bin/python -m pip install --upgrade pip
  .web-venv/bin/python -m pip install -r requirements.txt
fi

echo "Starting NextBestDollar..."
echo "Your browser should open shortly. Keep this window open while using the app."
.web-venv/bin/python -m streamlit run web_app.py --server.headless true

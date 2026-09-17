#!/bin/bash
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install the macOS Python installer from python.org, then launch again."
  read -r -p "Press Return to close. "
  exit 1
fi
if ! python3 -c 'import tkinter' 2>/dev/null; then
  echo "This Python installation is missing Tkinter. Install Python with Tk support, then try again."
  read -r -p "Press Return to close. "
  exit 1
fi
python3 main.py
result=$?
if [ "$result" -ne 0 ]; then
  echo "The app could not start. Please share the error above."
  read -r -p "Press Return to close. "
fi
exit "$result"

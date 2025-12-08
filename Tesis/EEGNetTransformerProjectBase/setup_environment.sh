#!/bin/bash
python3 -m venv eeg-env
source eeg-env/bin/activate
pip install -r requirements.txt
echo "Environment ready."

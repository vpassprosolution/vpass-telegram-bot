#!/bin/sh
exec uvicorn bot:app --host 0.0.0.0 --port 8080

#!/bin/bash
pip install -r requirements.txt
python bot.py

#!/bin/sh
uvicorn bot:app --host 0.0.0.0 --port 8080 & python bot.py


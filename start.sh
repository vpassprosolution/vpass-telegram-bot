#!/bin/sh
/opt/venv/bin/uvicorn bot:app --host 0.0.0.0 --port 8080 & /opt/venv/bin/python bot.py

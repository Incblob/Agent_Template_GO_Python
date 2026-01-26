#!/bin/bash

fastapi run server_agents.py --port 8000&
exec python server_rag.py
#
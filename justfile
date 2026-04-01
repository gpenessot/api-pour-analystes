set shell := ["powershell.exe", "-NoProfile", "-Command"]

default: setup

setup:
    uv sync

data:
    uv run python data/generate_data.py

api:
    uv run fastapi dev src/api/main.py

dashboard:
    uv run streamlit run src/dashboard/app.py

test:
    uv run pytest tests/ -v

all: setup data
    Write-Host "Setup termine. Lancez 'just api' puis 'just dashboard' dans deux terminaux."

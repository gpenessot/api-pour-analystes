.PHONY: setup data api dashboard test all

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
	@echo "✅ Setup terminé. Lancez 'make api' puis 'make dashboard' dans deux terminaux."

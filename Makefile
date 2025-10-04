.PHONY: setup etl app test clean

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

etl:
	python -m etl.fetch_all --ers --awdb --b120 --dwr

app:
	streamlit run app/Main.py

test:
	pytest -q

clean:
	rm -rf data/stage/* data/mart/* data/manifest.csv

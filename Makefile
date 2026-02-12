.PHONY: install test lint format clean

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest tests

lint:
	black --check .

format:
	black .

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]"
	python -c "import shutil; shutil.rmtree('data_quality_and_orchestration/dbt_modeling/target', ignore_errors=True)"
	python -c "import shutil; shutil.rmtree('etl_&_data_modeling/dbt_modeling/target', ignore_errors=True)"

# Makefile

ifneq (,$(wildcard .env))
    include .env
    export
endif

.PHONY: setup clean data-consolidate train-baseline train-v2 eval-v2 start-mlflow

setup:
	pip install -r requirements.txt
	yolo settings tensorboard=True

data-consolidate:
	python src/data/consolidate.py --config configs/data/consolidate.yaml

train:
	export MLFLOW_TRACKING_URI=$(MLFLOW_URI) && \
	python src/train/train.py --config $(CONFIG_PATH)

eval:
	export MLFLOW_TRACKING_URI=$(MLFLOW_URI) && \
	python src/eval/validate.py \
		--project $(PROJECT_NAME) \
		--run-name $(RUN_NAME) \
		--yolo-dir $(PROJECT_NAME)/$(RUN_NAME)

export:
	python src/deploy/export.py --config configs/quant/export_config.yaml

start-mlflow:
	mlflow server --backend-store-uri sqlite:///$(shell pwd)/mlflow.db \
		--default-artifact-root $(shell pwd)/mlruns \
		--host 0.0.0.0 --port 5000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

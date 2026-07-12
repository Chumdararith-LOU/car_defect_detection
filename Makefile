# Makefile

ifneq (,$(wildcard .env))
    include .env
    export
endif

.PHONY: setup clean data-consolidate train-baseline train-v2 eval-v2 start-mlflow

setup:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	yolo settings tensorboard=True

data-consolidate:
	python src/data/consolidate.py --config configs/data/Experiment_v1.yaml

train:
	export MLFLOW_TRACKING_URI=$(MLFLOW_URI) && \
	python src/train/train.py --config $(CONFIG_PATH)

eval:
	export MLFLOW_TRACKING_URI=$(MLFLOW_URI) && \
	python src/eval/validate.py \
		--project $(PROJECT_NAME) \
		--run-name $(RUN_NAME) \
		--yolo-dir runs/segment/$(PROJECT_NAME)/$(RUN_NAME)

export:
	python src/deploy/export.py --config configs/quant/export_config.yaml

start-mlflow:
	docker compose up -d mlflow_tracker

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

train-sod:
	python src/train/train_sod.py --train_config configs/train/stage1-sod.yaml --data_config data/processed/sod/sod_data.yaml

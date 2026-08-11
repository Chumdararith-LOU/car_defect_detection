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

# -----------------------------------------------------------------
# Stage 3: Panel Segmenter — local smoke simulation + server one-shot
# -----------------------------------------------------------------

STAGE3_RAW_ROOT ?= data/raw/archive/Car damages dataset
STAGE3_FULL_DATA ?= data/processed/stage3/car_damages_panel
STAGE3_SMOKE_DATA ?= data/processed/stage3/car_damages_panel_smoke
STAGE3_SMOKE_LIMIT ?= 20
STAGE3_TRAIN_SCRIPT ?= src/stage3/train/train.py
STAGE3_CONVERT_SCRIPT ?= src/stage3/data/convert_car_damages_to_yolo.py
STAGE3_RESOLVE_SCRIPT ?= src/stage3/data/resolve_dataset_yaml.py
STAGE3_SMOKE_CONFIG ?= configs/train/stage3/panel_segmenter_local_smoke.yaml
STAGE3_FULL_CONFIG ?= configs/train/stage3/panel_segmenter_baseline.yaml
STAGE3_MLFLOW_URI ?= $(or $(MLFLOW_URI),sqlite:///$(CURDIR)/mlflow_local.db)

.PHONY: stage3-convert-full stage3-convert-smoke stage3-check-smoke \
	stage3-smoke-train stage3-local-smoke stage3-resolve-dataset \
	stage3-preflight stage3-train-full stage3-server-one-shot

stage3-convert-full:
	python "$(STAGE3_CONVERT_SCRIPT)" \
		--raw-root "$(STAGE3_RAW_ROOT)" \
		--out-dir "$(STAGE3_FULL_DATA)" \
		--train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1 \
		--seed 42 --limit 0 --overwrite

stage3-convert-smoke:
	python "$(STAGE3_CONVERT_SCRIPT)" \
		--raw-root "$(STAGE3_RAW_ROOT)" \
		--out-dir "$(STAGE3_SMOKE_DATA)" \
		--train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1 \
		--seed 42 --limit $(STAGE3_SMOKE_LIMIT) --overwrite

stage3-check-smoke:
	@echo "== Smoke dataset counts ($(STAGE3_SMOKE_DATA)) =="
	@echo "images total: $$(find "$(STAGE3_SMOKE_DATA)/images" -type f | wc -l | tr -d ' ')"
	@echo "labels total: $$(find "$(STAGE3_SMOKE_DATA)/labels" -type f | wc -l | tr -d ' ')"
	@for s in train val test; do \
		echo "$$s images: $$(ls "$(STAGE3_SMOKE_DATA)/images/$$s" | wc -l | tr -d ' ')"; \
	done

stage3-smoke-train:
	export MLFLOW_TRACKING_URI="$(STAGE3_MLFLOW_URI)" && \
	export PYTHONPATH="$(CURDIR)/src" && \
	python "$(STAGE3_TRAIN_SCRIPT)" \
		--config "$(STAGE3_SMOKE_CONFIG)" \
		--data "$(CURDIR)/$(STAGE3_SMOKE_DATA)/car_damages_panel.yaml"

stage3-local-smoke: stage3-convert-smoke stage3-check-smoke stage3-smoke-train

stage3-resolve-dataset:
	python "$(STAGE3_RESOLVE_SCRIPT)" --dataset-dir "$(STAGE3_FULL_DATA)"

stage3-preflight:
	@test -f "$(STAGE3_TRAIN_SCRIPT)" || { echo "ERROR: trainer missing: $(STAGE3_TRAIN_SCRIPT)"; exit 1; }
	@test -f "$(STAGE3_FULL_CONFIG)" || { echo "ERROR: config missing: $(STAGE3_FULL_CONFIG)"; exit 1; }
	@test -f "$(STAGE3_FULL_DATA)/car_damages_panel.yaml" || { echo "ERROR: dataset YAML missing: $(STAGE3_FULL_DATA)/car_damages_panel.yaml"; exit 1; }
	@echo "== Full dataset counts ($(STAGE3_FULL_DATA)) =="
	@echo "images total: $$(find "$(STAGE3_FULL_DATA)/images" -type f | wc -l | tr -d ' ')"
	@echo "labels total: $$(find "$(STAGE3_FULL_DATA)/labels" -type f | wc -l | tr -d ' ')"
	@for s in train val test; do \
		echo "$$s images: $$(ls "$(STAGE3_FULL_DATA)/images/$$s" | wc -l | tr -d ' ')"; \
	done
	@test -f yolo26m-seg.pt || { echo "WARNING: yolo26m-seg.pt not found in repo root. Place it there before training."; exit 1; }

stage3-train-full: stage3-resolve-dataset
	export MLFLOW_TRACKING_URI="$(STAGE3_MLFLOW_URI)" && \
	export PYTHONPATH="$(CURDIR)/src" && \
	python "$(STAGE3_TRAIN_SCRIPT)" \
		--config "$(STAGE3_FULL_CONFIG)" \
		--data "$(CURDIR)/$(STAGE3_FULL_DATA)/car_damages_panel.yaml"

stage3-server-one-shot: stage3-preflight stage3-train-full

# Makefile

.PHONY: setup clean data-consolidate train-baseline start-mlflow

setup:
	pip install -r requirements.txt
	yolo settings tensorboard=True

data-consolidate:
	python src/data/consolidate.py

train-baseline:
	export MLFLOW_TRACKING_URI="http://localhost:5000" && \
	export MLFLOW_EXPERIMENT_NAME="Car_Defect_Segmentation" && \
	python src/train/train.py --config configs/train/yolo26n-seg.yaml

start-mlflow:
	mlflow server --backend-store-uri sqlite:///$(shell pwd)/mlflow.db \
		--default-artifact-root $(shell pwd)/mlruns \
		--host 0.0.0.0 --port 5000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
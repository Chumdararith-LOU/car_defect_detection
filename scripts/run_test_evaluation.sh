set -e

export MLFLOW_TRACKING_URI="http://127.0.0.1:5001"

echo "========================================================================"
echo "🚀 RUNNING UNSEEN TEST SET EVALUATION ON RTX 3090 (MLFLOW LOGGED)"
echo "========================================================================"

# Define the dataset YAMLs (Ensure these YAMLs contain the 'test:' path definition)
DATA_TILED="data/processed/sod_tiled/dataset.yaml"
DATA_UNTILED="data/processed/sod/dataset.yaml"
PROJECT_NAME="Automated_Car_Defect_Stage1_SOD"

# MODEL 1: yolo26n-sem (Tiled, 1024 imgsz, Focal Loss)
echo -e "\n=== [Model 1/6] yolo26n Tiled 1024 (Focal Loss) ==="
PYTHONPATH=. python src/eval/evaluate_test.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/122e3f76a2ee4d6abbcc94698b217266/artifacts/weights/best.pt" \
    --data "$DATA_TILED" \
    --project "$PROJECT_NAME" \
    --run_name "TEST_yolo26n_Tiled_1024_Focal"

# MODEL 2: yolo26n-sem (Tiled, 640 imgsz, Focal Loss)
echo -e "\n=== [Model 2/6] yolo26n Tiled 640 (Focal Loss) ==="
PYTHONPATH=. python src/eval/evaluate_test.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/403d6b3100d24013ad035979df412e97/artifacts/weights/best.pt" \
    --data "$DATA_TILED" \
    --project "$PROJECT_NAME" \
    --run_name "TEST_yolo26n_Tiled_640_Focal"

# MODEL 3: yolo26m-sem (Tiled, 640 imgsz, Focal Loss)
echo -e "\n=== [Model 3/6] yolo26m Tiled 640 (Focal Loss) ==="
PYTHONPATH=. python src/eval/evaluate_test.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt" \
    --data "$DATA_TILED" \
    --project "$PROJECT_NAME" \
    --run_name "TEST_yolo26m_Tiled_640_Focal"

# MODEL 4: yolo26m-sem (Untiled, 640 imgsz, CE Batch 32)
echo -e "\n=== [Model 4/6] yolo26m Untiled 640 CE B32 ==="
PYTHONPATH=. python src/eval/evaluate_test.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt" \
    --data "$DATA_UNTILED" \
    --project "$PROJECT_NAME" \
    --run_name "TEST_yolo26m_Untiled_640_CE_B32"

# MODEL 5: yolo26m-sem (Untiled, 640 imgsz, CE Batch 16)
echo -e "\n=== [Model 5/6] yolo26m Untiled 640 CE B16 ==="
PYTHONPATH=. python src/eval/evaluate_test.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/fa5389756f3e4704af9f25c56bb4cccb/artifacts/weights/best.pt" \
    --data "$DATA_UNTILED" \
    --project "$PROJECT_NAME" \
    --run_name "TEST_yolo26m_Untiled_640_CE_B16"

# MODEL 6: yolo26n-sem (Untiled, 640 imgsz, CE)
echo -e "\n=== [Model 6/6] yolo26n Untiled 640 CE ==="
PYTHONPATH=. python src/eval/evaluate_test.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/0b8ace4baec142448ce7e06434938ac2/artifacts/weights/best.pt" \
    --data "$DATA_UNTILED" \
    --project "$PROJECT_NAME" \
    --run_name "TEST_yolo26n_Untiled_640_CE"

echo -e "\n✅ All 6 models have been evaluated on the Test dataset!"

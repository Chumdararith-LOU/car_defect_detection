set -e

echo "========================================================================"
echo "🚀 STARTING AUTOMATED HIERARCHICAL MODEL MATRIX EVALUATION ON RTX 3090"
echo "========================================================================"

# MODEL 1: yolo26n-sem (Tiled, 1024 imgsz, Focal Loss)
echo "=== [Model 1/6] yolo26n Tiled 1024 (Focal Loss) ==="
PYTHONPATH=. python src/eval/validate.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/122e3f76a2ee4d6abbcc94698b217266/artifacts/weights/best.pt" \
    --imgsz 1024 --high 0.47 --low 0.35 --device cuda:0

# MODEL 2: yolo26n-sem (Tiled, 640 imgsz, Focal Loss)
echo "=== [Model 2/6] yolo26n Tiled 640 (Focal Loss) ==="
PYTHONPATH=. python src/eval/validate.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/403d6b3100d24013ad035979df412e97/artifacts/weights/best.pt" \
    --imgsz 640 --high 0.47 --low 0.35 --device cuda:0

# MODEL 3: yolo26m-sem (Tiled, 640 imgsz, Focal Loss)
echo "=== [Model 3/6] yolo26m Tiled 640 (Focal Loss) ==="
PYTHONPATH=. python src/eval/validate.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt" \
    --imgsz 640 --high 0.28 --low 0.18 --device cuda:0

# MODEL 4: yolo26m-sem (Untiled, 640 imgsz, CE Batch 32)
echo "=== [Model 4/6] yolo26m Untiled 640 CE B32 ==="
PYTHONPATH=. python src/eval/validate.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt" \
    --imgsz 640 --high 0.70 --low 0.70 --device cuda:0

# MODEL 5: yolo26m-sem (Untiled, 640 imgsz, CE Batch 16)
echo "=== [Model 5/6] yolo26m Untiled 640 CE B16 ==="
PYTHONPATH=. python src/eval/validate.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/fa5389756f3e4704af9f25c56bb4cccb/artifacts/weights/best.pt" \
    --imgsz 640 --high 0.70 --low 0.70 --device cuda:0

# MODEL 6: yolo26n-sem (Untiled, 640 imgsz, CE)
echo "=== [Model 6/6] yolo26n Untiled 640 CE ==="
PYTHONPATH=. python src/eval/validate.py \
    --model "/home/rith/secure_workspace/car_defect_detection/mlruns/1/0b8ace4baec142448ce7e06434938ac2/artifacts/weights/best.pt" \
    --imgsz 640 --high 0.70 --low 0.70 --device cuda:0

echo "✅ Matrix evaluation complete."

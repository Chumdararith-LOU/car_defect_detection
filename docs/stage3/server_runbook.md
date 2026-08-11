# Stage 3 Panel Segmenter Baseline — Server Runbook

## 1. Purpose

Train the Stage 3 panel/component segmenter baseline (M_panel) on the Ubuntu
server (RTX 4090). This runbook is meant to be executed **manually by you** on
the server. OpenCode has no server access; all commands below are for you to
copy and run yourself.

## 2. Local state summary

- Branch pushed: `stage_3`
- Latest local commit at runbook authoring time: `8856e4a` (`chore: ignore local agent rules files`)
  - The runbook commit itself lands on top of this hash. Run `git log --oneline -3`
    on the server after pulling to see the final hash.
- Config file used: `configs/train/stage3/panel_segmenter_baseline.yaml`
  - task: `segment`, model_preset: `yolo26m-seg.pt`, differential_lr: `false`,
    freeze: `0`, optimizer: `AdamW`, epochs: 100, imgsz: 640, batch: 8,
    multi_scale: `false`, mosaic/mixup/erasing: 0.0
- Dataset path expected on server:
  `/home/lamacpp/Documents/car_defect_detection/data/processed/stage3/car_damages_panel`
- Expected dataset counts:
  - 998 images / 998 labels total
  - train: 798, val: 100, test: 100
  - 21 panel classes (see dataset YAML)

## 3. Server login reminder

SSH into the server yourself — OpenCode cannot do this for you:

```bash
ssh USER@SERVER
```

Replace `USER@SERVER` with your actual username/host (e.g. `lamacpp@<server-ip>`).

## 4. Repository location checks

Likely repo path: `/home/lamacpp/Documents/car_defect_detection`

```bash
ls -d /home/lamacpp/Documents/car_defect_detection
ls /home/lamacpp/Documents/car_defect_detection/.git >/dev/null && echo "git repo OK"
```

If that path does not exist, search for the repo:

```bash
find /home -maxdepth 4 -name "car_defect_detection" -type d 2>/dev/null
```

If the repo is elsewhere, use that path for every command below and paste the
`find` output back before proceeding.

## 5. Pull latest code

```bash
cd /home/lamacpp/Documents/car_defect_detection
git status
git branch --show-current   # expect: stage_3
git pull origin stage_3
```

If `git status` shows local conflicting changes or `git pull` fails,
**stop and paste the output back** — do not force-reset without approval.

## 6. Verify Stage 3 files exist on server

```bash
ls -l src/stage3/train/train.py \
      configs/train/stage3/panel_segmenter_baseline.yaml
```

## 7. Verify yolo26m-seg.pt location

The config expects: `/home/lamacpp/Documents/car_defect_detection/yolo26m-seg.pt`

```bash
ls -lh /home/lamacpp/Documents/car_defect_detection/yolo26m-seg.pt
```

If missing, search more broadly:

```bash
find /home/lamacpp -maxdepth 4 -name "yolo26m-seg.pt" 2>/dev/null
```

If the actual path differs from `model_preset` in the config, **paste the
output back before training** so the config can be corrected (pinpoint edit
only — do not rewrite the whole config).

## 8. Verify dataset on server

Dataset root:
`/home/lamacpp/Documents/car_defect_detection/data/processed/stage3/car_damages_panel`

```bash
DATA=/home/lamacpp/Documents/car_defect_detection/data/processed/stage3/car_damages_panel

# total images / labels
find "$DATA/images" -type f | wc -l   # expect 998
find "$DATA/labels" -type f | wc -l   # expect 998

# per-split image counts
for s in train val test; do
  echo "$s: $(ls "$DATA/images/$s" | wc -l)"
done
# expect: train 798, val 100, test 100

# inspect the dataset YAML
cat "$DATA/car_damages_panel.yaml"
```

Expected YAML: `nc: 21`, 21 named panel classes, `path` pointing to the
dataset root above, `train/val/test` = `images/train|images/val|images/test`.

## 9. Dataset transfer command (from the MacBook, only if dataset is missing on server)

Run this **locally on the MacBook**, not on the server:

```bash
rsync -avz --progress \
  "data/processed/stage3/car_damages_panel/" \
  USER@SERVER:/home/lamacpp/Documents/car_defect_detection/data/processed/stage3/car_damages_panel/
```

(Run from the repo root:
`/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection`)

## 10. GPU check

```bash
nvidia-smi
```

Confirm an RTX 4090 is visible and largely idle before launching.

## 11. Training command verification

Verified CLI (from `src/stage3/train/train.py` argparse):
`--config` (required) and optional `--data` (overrides `dataset_config`).

```bash
cd /home/lamacpp/Documents/car_defect_detection
python src/stage3/train/train.py --help
```

If `--help` fails (missing dependency, import error, etc.), do **not** guess —
inspect the source and paste the error back:

```bash
sed -n '1,40p' src/stage3/train/train.py
```

Also confirm the interpreter environment actually has `ultralytics`, `torch`,
and `mlflow` before launching:

```bash
python -c "import torch, ultralytics, mlflow; print(torch.__version__, torch.cuda.is_available())"
```

## 12. Training launch options

Config: `configs/train/stage3/panel_segmenter_baseline.yaml`
Log: `logs/stage3_panel_segmenter_baseline.log`

Option A — tmux (recommended):

```bash
cd /home/lamacpp/Documents/car_defect_detection
mkdir -p logs
tmux new -s stage3
python src/stage3/train/train.py \
  --config configs/train/stage3/panel_segmenter_baseline.yaml \
  2>&1 | tee logs/stage3_panel_segmenter_baseline.log
# detach: Ctrl-b then d   |   reattach later: tmux attach -t stage3
```

Option B — nohup:

```bash
cd /home/lamacpp/Documents/car_defect_detection
mkdir -p logs
nohup python src/stage3/train/train.py \
  --config configs/train/stage3/panel_segmenter_baseline.yaml \
  > logs/stage3_panel_segmenter_baseline.log 2>&1 &
echo $! > logs/stage3_panel_segmenter_baseline.pid
```

Note: `runs/`, `logs/`, and MLflow artifacts are git-ignored; do not commit them.

## 13. Monitoring commands

```bash
# tail the log
tail -f logs/stage3_panel_segmenter_baseline.log

# GPU usage
watch -n 2 nvidia-smi

# process status (nohup option)
ps -p "$(cat logs/stage3_panel_segmenter_baseline.pid)" -o pid,etime,stat,cmd
# or broadly
ps aux | grep "stage3/train/train.py" | grep -v grep

# tmux option
tmux ls
```

## 14. Stop conditions — do NOT train if any of these hold

- Dataset counts are wrong (must be 998 images / 998 labels; 798/100/100 split).
- `yolo26m-seg.pt` is missing or its path differs from the config.
- The config path `configs/train/stage3/panel_segmenter_baseline.yaml` is wrong or missing.
- `git pull` fails or the server branch is not `stage_3`.
- GPU is not visible in `nvidia-smi` (or CUDA unavailable).
- The repo path on the server differs from the expected one and has not been confirmed.

Also per project rules: use fresh pretrained `yolo26m-seg.pt` only — never
Stage 2 defect checkpoints or Model 1 remapped checkpoints for Stage 3.

## 15. Failure reporting

If anything fails, paste back:
1. the exact command you ran, and
2. the full terminal output (error + a few lines of context).

Do not improvise fixes to configs, dataset paths, or weights without checking first.

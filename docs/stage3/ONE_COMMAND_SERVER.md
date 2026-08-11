# Stage 3 Server One-Shot

1. One-time dataset transfer (run from the MacBook repo root):

```bash
rsync -avz --progress \
  "data/processed/stage3/car_damages_panel/" \
  USER@SERVER:/home/lamacpp/Documents/car_defect_detection/data/processed/stage3/car_damages_panel/
```

2. On the server, after `ssh USER@SERVER` and `cd` into the repo:

```bash
git pull origin stage_3
make stage3-server-one-shot
```

Note: `yolo26m-seg.pt` must be placed in the repo root before running.
The target runs preflight checks (trainer/config/dataset counts/weights),
rewrites the dataset YAML `path:` to the server location, then trains.

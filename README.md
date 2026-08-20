# Car Defect Detection

Automated car defect detection pipeline using computer vision and deep learning.

## 🚀 Quickstart (Clone & Run)

### Prerequisites

* Python 3.10 (Conda recommended)
* Git LFS — champion weights are stored via LFS: `git lfs install` (one-time)
* Bun (frontend): [bun.sh](https://bun.sh?utm_source=chatgpt.com)

### 1. Clone & Create Environment

```bash
git clone https://github.com/Chumdararith-LOU/car_defect_detection.git
cd car_defect_detection

conda create -n car_defect python=3.10
conda activate car_defect
```

### 2. Install Dependencies

```bash
# Ubuntu + NVIDIA GPU: install the CUDA build of torch/torchvision
# matching your NVIDIA driver before installing requirements.
pip install -r requirements.txt
```

### 3. Model Weights (~132 MB)

Best weights are tracked with Git LFS. If they were not downloaded automatically:

```bash
git lfs install
git lfs pull
```

Then verify checksums and create deployment symlinks:

```bash
python scripts/setup_models.py
```

### 4. Run the Backend

The backend runs on port `8010`:

```bash
cd backend
uvicorn main:app --reload --port 8010
```

### 5. Run the Frontend

Open a **new terminal**:

```bash
cd frontend
bun install
bun run dev
```

Open:

```text
http://localhost:8080
```

The frontend expects the backend at:

```text
http://localhost:8010
```

---

## Architecture Overview

The project is organized into separate components for model inference, backend services, frontend development, and supporting scripts.

### Backend

The backend provides the API and inference services used by the frontend.

### Frontend

The frontend provides the user interface for interacting with the defect detection pipeline.

### Models

Champion model weights are managed through Git LFS and prepared for deployment using:

```bash
python scripts/setup_models.py
```

### Development

Development dependencies are listed separately in:

```text
requirements-dev.txt
```

Install them with:

```bash
pip install -r requirements-dev.txt
```

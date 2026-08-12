# File 2: `docs/host_detection_spec.md`

# Host Detection Specification

Version: 0.1
Date: 2026-08-12
Status: Draft for approval

## 1. Purpose

The host detection module automatically detects the machine where the app is running and decides what operations are safe or recommended.

It must answer:

```text
Is this machine capable of local inference?
Is this machine capable of local training?
Is a CUDA GPU available?
How much VRAM is available?
Are required models available?
Are required datasets available?
Is a remote server configured?
Is the remote server reachable?
Should the system run locally, remotely, or in hybrid mode?
```

---

## 2. Design Principles

### 2.1 Automatic detection, manual override

The system should detect the host automatically on startup.

But the user must be able to override:

```text
runtime mode
inference device
training device
remote server selection
```

### 2.2 Fast detection

Basic host detection should be fast.

It should not load full models by default.

Target:

```text
basic detection < 2 seconds
deep model smoke test optional
```

### 2.3 Safe fallback

If local GPU is unavailable:

```text
recommend remote training
allow CPU inference only if configured
disable heavy local training unless overridden
```

If remote server is unavailable:

```text
show warning
fall back to local if possible
disable remote training
```

### 2.4 No secrets in UI

API tokens and passwords must not be displayed in the frontend.

Only status should be shown:

```text
remote token configured: yes/no
```

---

## 3. Host Detection Scope

The host detection module detects:

## 3.1 Operating system

```text
OS name
OS version
platform
architecture
hostname
```

## 3.2 CPU and memory

```text
CPU count
CPU physical cores
total RAM
available RAM
```

## 3.3 Disk

```text
workspace disk total
workspace disk free
model directory free space
data directory free space
```

## 3.4 Python / ML environment

```text
Python version
PyTorch version
CUDA available
CUDA version if available
cuDNN available
Ultralytics available
MLflow available
```

## 3.5 GPU

For each GPU:

```text
index
name
total VRAM
free VRAM if available
CUDA capability
```

## 3.6 Model availability

For each stage:

```text
model file exists
model metadata exists
config exists
version known
checksum valid optional
```

Stages:

```text
stage1
stage2
stage3
stage4 config
```

## 3.7 Dataset availability

For each dataset:

```text
dataset manifest exists
images directory exists
labels directory exists
class map exists
split file exists
dataset status
```

## 3.8 Remote server

```text
remote configured
remote URL
remote reachable
remote auth ok
remote host profile
remote GPU availability
remote model availability
```

---

## 4. Runtime Modes

The system supports:

```text
auto
local
remote
hybrid
```

### 4.1 Auto

System decides based on detected capabilities.

Example:

```text
If local GPU is available and models exist:
    use local inference.

If local GPU is strong and datasets exist:
    allow local training.

If remote server is configured and reachable:
    allow remote training or remote inference.
```

### 4.2 Local

All operations run locally if possible.

### 4.3 Remote

Operations run on remote server.

Desktop app is only a client.

### 4.4 Hybrid

Separate choices for inference and training.

Example:

```text
inference: local
training: remote
```

---

## 5. Capability Flags

The host profile should produce capability flags.

```text
can_infer_stage1
can_infer_stage2
can_infer_stage3
can_run_stage4
can_train_stage1
can_train_stage2
can_train_stage3
can_use_local_gpu
can_use_remote
can_run_sahi
can_export_report
```

It should also produce warnings:

```text
no_gpu
low_vram
low_disk
missing_models
missing_datasets
remote_unreachable
unsupported_os
cuda_version_mismatch
```

---

## 6. Recommended Host Profile Schema

Example JSON:

```json
{
  "schema_version": "0.1",
  "generated_at": "2026-08-12T10:00:00Z",
  "machine": {
    "hostname": "company-desktop",
    "os": "Windows 11",
    "platform": "win32",
    "architecture": "x86_64",
    "python_version": "3.10.14"
  },
  "cpu": {
    "logical_cores": 16,
    "physical_cores": 8
  },
  "memory": {
    "total_gb": 32.0,
    "available_gb": 21.5
  },
  "disk": {
    "workspace_path": "C:/car_defect_detection",
    "free_gb": 850.0,
    "total_gb": 1000.0
  },
  "gpu": {
    "cuda_available": true,
    "cuda_version": "12.4",
    "device_count": 1,
    "devices": [
      {
        "index": 0,
        "name": "NVIDIA GeForce RTX 4090",
        "total_vram_gb": 24.0,
        "free_vram_gb": 22.0
      }
    ]
  },
  "models": {
    "stage1": {
      "available": true,
      "version": "sod_v1.0.0",
      "path_status": "found"
    },
    "stage2": {
      "available": true,
      "version": "stage2_head_warmup_7cls_extended_v1.0.0",
      "path_status": "found"
    },
    "stage3": {
      "available": true,
      "version": "panel_segmenter_baseline_v1.0.0",
      "path_status": "found"
    },
    "stage4": {
      "available": true,
      "config_status": "found"
    }
  },
  "datasets": {
    "stage1_binary": "released",
    "stage2_7cls": "released",
    "stage3_panel": "released"
  },
  "remote": {
    "configured": false,
    "reachable": false,
    "auth_ok": false,
    "base_url": null,
    "host_profile": null
  },
  "capabilities": {
    "can_infer_stage1": true,
    "can_infer_stage2": true,
    "can_infer_stage3": true,
    "can_run_stage4": true,
    "can_train_stage1": true,
    "can_train_stage2": true,
    "can_train_stage3": true,
    "can_use_local_gpu": true,
    "can_use_remote": false
  },
  "recommendations": {
    "runtime_mode": "local",
    "inference_device": "cuda",
    "training_device": "cuda",
    "reason": "Local CUDA GPU detected with sufficient VRAM and models are available."
  },
  "warnings": []
}
```

---

## 7. Detection Timing

Host detection should run:

1. On app startup.
2. When the user opens the Host/System page.
3. When runtime settings change.
4. Before starting a training job.
5. Before running a heavy inference job.
6. When the user clicks `Redetect`.

---

## 8. Detection Algorithm

Basic algorithm:

```text
1. Read runtime settings.
2. Detect local OS, CPU, RAM, disk.
3. Detect Python environment.
4. Detect CUDA/GPU.
5. Check local model availability.
6. Check local dataset availability.
7. If remote is configured:
       test remote health endpoint
       fetch remote host profile
8. Produce capability flags.
9. Produce recommendations.
10. Return host profile.
```

---

## 9. Recommendation Logic

### 9.1 Inference recommendation

```text
If local GPU is available and Stage models exist:
    recommend local CUDA inference.

Else if remote server is reachable:
    recommend remote inference.

Else if CPU fallback is enabled:
    recommend local CPU inference with warning.

Else:
    system unavailable.
```

### 9.2 Training recommendation

```text
If local GPU is available:
    if VRAM >= required training VRAM:
        recommend local training.
    else:
        warn low VRAM and suggest remote training.

Else if remote server is configured and reachable:
    recommend remote training.

Else:
    disable training unless user overrides.
```

### 9.3 Hybrid recommendation

```text
If local GPU is good for inference but not training:
    inference = local
    training = remote

If local GPU is strong and datasets are local:
    inference = local
    training = local

If remote is strongly preferred:
    inference = remote
    training = remote
```

---

## 10. Configuration Schema

Proposed runtime config:

```yaml
runtime:
  mode: auto

local:
  inference_device: auto
  training_device: auto
  allow_cpu_inference: true
  allow_cpu_training: false

remote:
  enabled: false
  base_url: ""
  api_token_env: CARDEFECT_REMOTE_TOKEN
  timeout_seconds: 10

thresholds:
  min_training_vram_gb: 8
  min_inference_vram_gb: 4
  min_free_disk_gb: 20

paths:
  model_registry: model_registry
  datasets: data/released
  mlflow: mlruns
  logs: experiments/logs
```

Values should be editable in the UI, but protected by validation.

---

## 11. API Endpoints

### 11.1 Health

```text
GET /api/health
```

Returns:

```json
{
  "status": "ok",
  "service": "cardefect-backend",
  "version": "0.1.0"
}
```

---

### 11.2 Host profile

```text
GET /api/host/profile
```

Returns full host profile JSON.

---

### 11.3 Redetect host

```text
POST /api/host/detect
```

Body optional:

```json
{
  "deep": false
}
```

If:

```json
{
  "deep": true
}
```

then the backend may run optional model smoke checks.

---

### 11.4 Runtime config

```text
GET /api/runtime/config
PUT /api/runtime/config
```

Example PUT:

```json
{
  "runtime": {
    "mode": "hybrid"
  },
  "local": {
    "inference_device": "cuda",
    "training_device": "remote"
  },
  "remote": {
    "enabled": true,
    "base_url": "http://192.168.1.20:8000"
  }
}
```

---

### 11.5 Test remote connection

```text
POST /api/remote/test-connection
```

Body:

```json
{
  "base_url": "http://192.168.1.20:8000",
  "timeout_seconds": 10
}
```

Returns:

```json
{
  "reachable": true,
  "auth_ok": true,
  "remote_host_profile": {
    "gpu": {
      "cuda_available": true,
      "device_count": 1
    }
  }
}
```

---

### 11.6 System metrics

```text
GET /api/system/metrics
```

Returns live usage:

```json
{
  "cpu_percent": 22.5,
  "ram_used_gb": 12.4,
  "gpu_used_percent": 40.0,
  "gpu_vram_used_gb": 6.2,
  "disk_free_gb": 850.0
}
```

---

## 12. UI Requirements

## 12.1 Host status card

The UI should show:

```text
Runtime mode
Local GPU
CUDA status
VRAM
Disk space
Model availability
Remote status
Recommendation
Warnings
```

Example:

```text
Runtime Mode: Auto
Local GPU: NVIDIA RTX 4090
CUDA: Available
VRAM: 24 GB
Free Disk: 850 GB
Models: Stage 1 ✓ Stage 2 ✓ Stage 3 ✓
Remote: Not configured
Recommendation: Local inference + local training
```

---

## 12.2 User actions

Buttons:

```text
Redetect
Use Local
Use Remote
Open Settings
Test Remote Connection
```

---

## 12.3 Warning examples

```text
No CUDA GPU detected. Local training is disabled.
Remote server is unreachable.
Stage 2 model file is missing.
Free disk space is low.
Remote API token is not configured.
```

---

## 13. Security Requirements

1. Local backend should bind to `127.0.0.1` by default.
2. Remote backend should use authentication.
3. API tokens should be stored in environment variables or secure settings.
4. Tokens must not be returned to the frontend.
5. Remote URLs should be validated.
6. Host detection must not upload images or private data.
7. Logs must not contain secrets.

---

## 14. Error Handling

Possible errors:

| Error | UI Behavior |
|---|---|
| No GPU detected | Show warning, recommend remote training |
| CUDA unavailable | Show warning, allow CPU inference if enabled |
| Remote unreachable | Show remote offline, fall back to local if possible |
| Missing Stage 2 model | Disable Stage 2 inspection and show setup warning |
| Low disk space | Show warning and block training if below threshold |
| Remote auth failure | Show authentication error, do not expose token |
| Invalid runtime config | Show validation error and keep previous valid config |

---

## 15. Testing Requirements

## 15.1 Unit tests

Test:

```text
GPU detection parsing
recommendation logic
config validation
remote connection timeout handling
missing model detection
low disk warning
```

## 15.2 Integration tests

Test:

```text
GET /api/health
GET /api/host/profile
PUT /api/runtime/config
POST /api/remote/test-connection
```

## 15.3 Manual checklist

Test on:

```text
local CUDA machine
CPU-only machine
machine with missing models
machine with remote configured
machine with remote offline
low disk machine
```

---

## 16. Acceptance Criteria

Host detection is complete when:

1. App automatically detects local OS, GPU, CUDA, VRAM, and disk.
2. App shows model availability for Stage 1, Stage 2, Stage 3, Stage 4.
3. App shows remote server status if configured.
4. App recommends local or remote execution.
5. User can override runtime mode.
6. Training is disabled or warned when GPU is insufficient.
7. Missing models produce clear warnings.
8. Remote connection test works.
9. No secrets are displayed in UI.
10. Host detection returns stable JSON schema.
```

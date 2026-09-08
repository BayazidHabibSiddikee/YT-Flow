# Face-Swap Model Recovery Guide

## What Was Lost
The face-swap pipeline models were stored locally and not tracked in git. They need to be recovered.

## Model Inventory

### 1. inswapper_128.onnx (Primary)
- **Purpose**: High-quality face swapping (used by Reactor, FaceFusion, roop)
- **Size**: ~500MB
- **Source**: `https://github.com/facefusion/facefusion-assets/releases`
- **Backup mirrors**: Check HuggingFace `ezioruan/inswapper_128.onnx`

### 2. simswap_224.onnx
- **Purpose**: Academic/research face swap model
- **Source**: `https://github.com/neuralchen/SimSwap`

### 3. buffalo_l (Face Detection)
- **Purpose**: Face detection & alignment
- **Auto-installed by**: `pip install insightface`
- **Default path**: `~/.insightface/models/buffalo_l/`

## Recovery Steps

### Step 1: Search Local Drives
```bash
find /home/sword -name "*.onnx" -o -name "inswapper*" -o -name "simswap*" -o -name "buffalo*" 2>/dev/null
```

### Step 2: Check Browser Downloads
```bash
find ~/Downloads -type f \( -name "*.onnx" -o -name "*.pth" -o -name "*.pt" \) 2>/dev/null | head -20
```

### Step 3: If Found
Copy to `YT-Flow/face-swap/models/` and commit.

### Step 4: If Not Found
Re-download:
```bash
mkdir -p face-swap/models
cd face-swap/models

# inswapper_128 (recommended)
wget "https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx"

# buffalo_l (auto-install)
pip install insightface
cp -r ~/.insightface/models/buffalo_l ./
```

## Tools That Use These Models
| Tool | Language | Repo |
|------|----------|------|
| FaceFusion | Python | `https://github.com/facefusion/facefusion` |
| roop | Python | `https://github.com/s0md3v/roop` |
| InsightFace | Python | `https://github.com/deepinsight/insightface` |
| DeepFaceLive | C++/Python | `https://github.com/iperov/DeepFaceLive` |

## Recommendation
Use **FaceFusion** — it's actively maintained and uses inswapper_128 directly:
```bash
pip install facefusion
facefusion --source reference.jpg --target video.mp4 --output output.mp4
```

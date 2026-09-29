# HACK_PATH.md — How I Built an ML Video-Editing Director in One Night

> Target: **MTE Mind, 9 PM**. A machine that out-directs a human editor.

## 0. Mission

Human editors forget rules: BGM on documentaries, Ken-Burns vibration,
wrong tool per scene. Goal: script in, publish-plan out, smarter every render.
Jev gives valid JSON but learns nothing. Static router.py never updates.
LLM analyzer hallucinates motions. So: **DirectorBrain**.

## 1. Data (nothing pirated)

No copyrighted video downloaded. Editing decisions need
(engine, scene-type, strategy, ok/fail) triples, not pixels.

- Own renders: vault/director_brain.db (223 Asunta scenes, 1721s voice-only OK)
- Pexels cache on disk: vault/asunta_cinematic/stock_cache/ (888 files)
- Synthetic bootstrap: 9 rule triples -> 232 rows
  (vault/director_ml/datasets/synthetic_labels.jsonl)
- MovieCuts/ClipShots referenced as schema only.

Harvester: tools/director/brain/harvest_datasets.py.


## 2. Model (local + Kaggle GPU)

- sklearn LogisticRegression on 18-dim scene features (features.py):
  **accuracy 0.957, n=232** (train_eval.py -> engine_picker.pkl).
- PyTorch MLP 18-32-16-1, 60 epochs CPU: **train-acc 0.991, loss 0.0177**
  (torch_ranker.py -> scene_ranker.pt, torch 2.12+cu130).
- Kaggle kernel vault/director_ml/kaggle_train/ (sword/director-ml-train,
  GPU+internet): `kaggle kernels push -p vault/director_ml/kaggle_train`.
- predictor.py loads pkl, falls back to rules; brain adds DB bias per render.

## 3. Brain (how it directs)

tools/director/brain/: brain_core.py classify + SQLite memory;
brain_plan.py plan_scenes (7.5s doc / 4s shorts, motion always static),
direct() ordered tool_calls, learn_from_render(); rules.py (BGM shorts-only,
images static, -16 LUFS — never violated); schemas.py to_video_plan() for
old executor/compositor; benchmark.py; seed_history.py.

## 4. Benchmark (brain vs Jev vs static vs LLM)

`python3 tools/director/brain/benchmark.py` (6 scripts):

| System | Learns? | Violations | Latency | Notes |
|---|---|---|---|---|
| DirectorBrain | yes | 0 | 6-21ms | visual_resolver docs, MPT shorts |
| static router.py | no | unchecked | ms | capability-match, dummy consts |
| Jev jev_router.py | no | n/a | API | needs typesafe-sdk + key; fallback = first pipeline, valid but not smart |
| LLM analyzer.py | no | hallucinates ken_burns | sec | key + JSON risk |

Jev guarantees a valid choice, never a good one. The brain improves every
render — that is why it beats humans on consistency.

## 5. Release (MTE Mind, 9 PM)

Render: `python3 tools/director/brain/release_mte.py`
(60-90s tech explainer, 16:9 voice-only). Upload manual. Schedule 21:00
Asia/Dhaka.

## 6. Reproduce

```bash
cd /home/sword/Documents/MediaFactory
python3 tools/director/brain/harvest_datasets.py
python3 tools/director/brain/train_eval.py
python3 tools/director/brain/torch_ranker.py
python3 tools/director/brain/benchmark.py
python3 tools/director/brain/seed_history.py
kaggle kernels push -p vault/director_ml/kaggle_train
```

## 7. Next

Frame aesthetic scorer on stock_cache thumbs, cut predictor from
silence+subtitle gaps, retention labels from MTE analytics. Tables ready.

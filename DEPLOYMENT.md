# Deployment Guide - Hugging Face Spaces

## 🚀 Quick Deploy to HF Spaces

### Step 1: Create Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Settings:
   - **Name**: `contract-review-env`
   - **License**: MIT
   - **SDK**: Docker
   - **Hardware**: CPU basic (free tier works)

### Step 2: Push Code

```bash
# Clone your new space
git clone https://huggingface.co/spaces/YOUR_USERNAME/contract-review-env
cd contract-review-env

# Copy all files from contract_env_upgraded/
cp -r /path/to/contract_env_upgraded/* .

# Commit and push
git add .
git commit -m "Initial deployment - Interactive Contract Review Environment v2.0"
git push
```

### Step 3: Configure Space

Add to Space settings:

**Environment Variables** (Optional for inference):
- `OPENAI_API_KEY`: Your OpenAI API key
- `MODEL_NAME`: `gpt-4` or `gpt-3.5-turbo`
- `API_BASE_URL`: `https://api.openai.com/v1`

**Tags**:
- `openenv`
- `legal`
- `contract-review`
- `rl-environment`

### Step 4: Verify Deployment

Wait for build to complete (~3-5 minutes), then test:

```bash
# Get your Space URL (e.g., https://YOUR_USERNAME-contract-review-env.hf.space)
SPACE_URL="https://YOUR_USERNAME-contract-review-env.hf.space"

# Test health
curl $SPACE_URL/

# Test reset
curl -X POST $SPACE_URL/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_detection"}'

# Expected: {"observation": {...}, "task_id": "easy_detection", ...}
```

---

## 📝 Submission Checklist

Before submitting:

- [ ] Space deploys successfully (green checkmark)
- [ ] `/reset` endpoint returns 200 OK
- [ ] `docker build` completes without errors
- [ ] `openenv validate` passes (install with `pip install openenv-core`)
- [ ] `inference.py` runs and produces scores
- [ ] All 3 tasks have graders returning 0.0-1.0
- [ ] README is clear and comprehensive
- [ ] openenv.yaml is valid

---

## 🔧 Local Testing Before Deploy

```bash
# 1. Test Docker build
cd contract_env_upgraded
docker build -t contract-env-test .

# 2. Test Docker run
docker run -p 7860:7860 contract-env-test

# 3. In another terminal, test endpoints
curl http://localhost:7860/
curl http://localhost:7860/tasks

# 4. Test inference (requires API key)
export OPENAI_API_KEY="sk-..."
python inference.py
```

---

## 🐛 Troubleshooting

### Build fails
- Check `requirements.txt` has correct versions
- Verify all imports work locally
- Check Dockerfile syntax

### Reset returns 500
- Check contract datasets are loaded
- Verify task definitions exist
- Check environment initialization logic

### Grading fails
- Ensure graders are properly imported
- Verify state is tracked correctly
- Check ground truth data is set

---

## 📊 Expected Baseline Scores

After deployment, run inference to get baseline:

```json
{
  "model": "gpt-4",
  "results": [
    {"task_id": "easy_detection", "score": 0.750},
    {"task_id": "medium_analysis", "score": 0.680},
    {"task_id": "hard_comprehensive", "score": 0.620}
  ],
  "average_score": 0.683
}
```

These scores should be **reproducible** on rerun.

---

## 📝 Submission Form Fields

When submitting to hackathon:

**Project Name**: Interactive Contract Review Environment v2.0

**Space URL**: https://huggingface.co/spaces/YOUR_USERNAME/contract-review-env

**GitHub Repo**: (Optional) Your GitHub repo URL

**Description**: 
```
Interactive legal contract review environment with progressive clause revelation, 
multi-action decision system, and strategic tradeoffs. Transforms static 
classification into dynamic legal reasoning. Features cost mechanics, ambiguous 
contracts, and comprehensive grading across 3 difficulty levels.
```

**Key Features**:
- Progressive clause revelation (true environment dynamics)
- Multi-action system (explore/flag/decide/finalize)
- Cost/penalty mechanics (strategic pressure)
- Decision layer (accept/negotiate/reject)
- Complex contracts with ambiguous language
- Comprehensive multi-dimensional grading

**Baseline Scores**:
- Easy: 0.75
- Medium: 0.68
- Hard: 0.62
- Average: 0.68

---

## ✅ Final Verification

Before submitting, confirm:

1. ✅ Space is public and accessible
2. ✅ All endpoints return valid responses
3. ✅ Graders produce deterministic scores
4. ✅ Docker container runs without errors
5. ✅ README explains environment clearly
6. ✅ Baseline inference completes successfully

**You're ready to submit! 🎉**

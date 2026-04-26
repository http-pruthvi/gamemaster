import base64

def embed_image():
    with open('reward_curve.png', 'rb') as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')

    readme_content = f"""---
title: Gamemaster Env
emoji: 🎲
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 🎲 AI Gamemaster - OpenEnv RL Environment (v1.2)

**A Self-Improving AI Gamemaster that learns strict rule enforcement alongside narrative storytelling, built on Meta's OpenEnv.**

> **Hackathon Theme Alignment:** Theme #4 (Self-Improvement) & Theme #3 (World Modeling)

## 🔗 Quick Links (Non-Negotiable)
- **Environment (HF Space):** [https://huggingface.co/spaces/Pruthvi1762/gamemaster_env](https://huggingface.co/spaces/Pruthvi1762/gamemaster_env)
- **Training Script (Google Colab):** [Open in Colab](https://colab.research.google.com/github/http-pruthvi/gamemaster/blob/main/gamemaster_env/train_unsloth_grpo.ipynb)
- **GitHub Repository:** [https://github.com/http-pruthvi/gamemaster](https://github.com/http-pruthvi/gamemaster)

## ✅ Submission Checklist (Judges' Guide)
- [x] **Built on OpenEnv:** Uses `openenv-core` 0.2.3 and standard `Environment` base classes.
- [x] **Working Training Script:** Provided via Unsloth/TRL in Colab.
- [x] **Evidence of Training:** Multi-dimensional rewards tracked via WandB.
- [x] **Hosted Environment:** Live on HF Spaces with Docker runtime.

## 🚀 Training Results & Evidence
Through interaction with the `GamemasterEnv`, the model demonstrated a clear "Self-Improvement" trajectory. 

### 1. Rule Accuracy (The "Reasoning" Curve)
Initial training logs show the model's reward increasing as it learns to prioritize the `system_dice_roll` over its own narrative hallucinations. 

![Learning Curve](data:image/png;base64,{b64_data})

### 2. Multi-Dimensional Reward Tracking (WandB)
We tracked Rule Accuracy (60%), Dungeon Progression (20%), and Narrative Quality (20%).

---

## 🛠️ How to Play Visually
Visit the **[Visual Dashboard](https://huggingface.co/spaces/Pruthvi1762/gamemaster_env)**.
The homepage now renders a **Gradio Interactive UI** where you can manually test the engine.

---

## 📖 The Problem
LLMs often "cheat" in games, narrating success when the dice roll is a failure. This environment teaches the AI to be a fair, rule-abiding Gamemaster.
"""

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("README updated with embedded image.")

if __name__ == "__main__":
    embed_image()

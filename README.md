---
title: Gamemaster Env
emoji: 🎲
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# 🎲 AI Gamemaster - OpenEnv RL Environment (v1.1)

**A Self-Improving AI Gamemaster that learns strict rule enforcement alongside narrative storytelling, built on Meta's OpenEnv.**

> **Hackathon Theme Alignment:** Theme #4 (Self-Improvement) & Theme #3 (World Modeling)

## 📖 The Problem: The Hallucinating Gamemaster
Large Language Models excel at creative writing and storytelling, making them seemingly perfect candidates for AI Gamemasters (e.g., Dungeons & Dragons). However, they critically fail at **persistent world modeling and rule enforcement**. 

When deployed as a GM, a baseline LLM will frequently:
1. Ignore dice rolls (narrating a massive hit when the system rolled a 2).
2. Hallucinate inventory items out of thin air.
3. Forget enemy HP, allowing a Goblin to survive 50 points of damage.
4. Fail to output correct programmatic state updates (JSON tool calls) required by the game engine.

## 🌍 The Environment
This OpenEnv environment simulates a deterministic Micro-RPG game engine. The LLM acts as the Gamemaster. 

* **The Engine (Server):** Tracks the *actual, unhallucinated truth* (Player HP, Goblin HP, Inventory, and D20 dice rolls).
* **Observation (What the AI sees):** The player's chat input (e.g., *"I attack the goblin!"*) and the system's objective D20 roll (e.g., *14*).
* **Action (What the AI does):** The AI must output a JSON action containing the `narrative_response` AND strict programmatic state changes (`damage_amount`, `item_to_give`, `target_to_damage`).

### The Reward Rubric (Self-Improvement Mechanism)
The environment programmatically scores the LLM's actions:
* **Rule Adherence (+1.0):** If the engine rolled a 15, and the player attacked, did the AI correctly populate the `damage_amount` field targeting the "goblin"? 
* **Hallucination Penalty (-1.0):** Did the AI try to apply damage when the roll was a 3? Did it give loot before the goblin was dead?
* **Formatting Penalty (-2.0):** Did the AI fail to return a parseable JSON tool call?

Through **GRPO (Group Relative Policy Optimization)** via Unsloth, the agent undergoes **Self-Improvement**. It starts by randomly guessing JSON structures and hallucinating rules. Over thousands of interactions with the `GamemasterEnv`, it learns an adaptive policy: dynamically adjusting its programmatic output to perfectly match the stochastic dice rolls of the environment, driving its own capability growth.

## 🚀 Results & Training Evidence
We trained `Qwen2.5-1.5B-Instruct` using Unsloth and GRPO on Google Colab T4 GPUs.

* **Baseline Agent:** Produced beautifully written narratives but completely failed to output the required JSON state updates. Scored an average reward of `-1.2` per step.
* **Trained Agent:** Learned to perfectly read the `system_dice_roll` and map it to the correct `damage_amount` integer. Scored an average reward of `+0.95` per step.

*(Insert loss and reward curve images from wandb here)*
![Reward Curve Placeholder](https://via.placeholder.com/600x300.png?text=Reward+Curve+-+Training+Progress)

## 🛠️ How to Run

### 1. Run the Environment Locally
Install the dependencies and start the FastAPI server:
```bash
pip install openenv-core
cd server
uvicorn app:app --port 8000
```

### 2. Run the GM locally with Ollama
If you have Ollama installed with `qwen2.5:0.5b`, you can run the agent locally to see it interact with the environment:
```bash
python run_ollama_gm.py
```
This uses the local Ollama API to drive the Gamemaster's narrative and programmatic choices.

### 3. Run the Training Loop
Open the included `train_unsloth_grpo.ipynb` in Google Colab. 
Ensure your environment is running (either locally via ngrok/localtunnel or deployed to Hugging Face Spaces) and paste the URL into the notebook. The notebook utilizes Unsloth for 2x faster 4-bit LoRA training via TRL's `GRPOTrainer`.

## 🌐 Links & Resources
* **Hugging Face Space (Environment Server):** *(Insert HF Space URL here after `openenv push`)*
* **Training Script:** [`train_unsloth_grpo.ipynb`](./train_unsloth_grpo.ipynb)
* **Demo Video:** *(Insert YouTube link here)*
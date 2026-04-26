import ollama
import json
import re
from server.gamemaster_env_environment import GamemasterEnvironment
from models import GamemasterAction

# Use the model you have installed
MODEL = "qwen2.5:0.5b"

SYSTEM_PROMPT = """
You are an AI Gamemaster. You must enforce the rules of the game while telling a good story.
You will receive an Observation containing the player's action, your previous engine feedback, and the system's dice roll (1-20).

RULES:
1. If the player attacks, a roll of >= 10 is a HIT. You MUST set damage_amount > 0 and target_to_damage to the monster name.
2. If the roll is < 10, it is a MISS. You MUST set damage_amount to 0 and target_to_damage to null.
3. If the monster HP is 0, you can give an item using item_to_give.

YOU MUST RESPOND ONLY WITH A VALID JSON OBJECT:
{
  "narrative_response": "The story text",
  "target_to_damage": "monster_name" or null,
  "damage_amount": integer,
  "item_to_give": "item_name" or null
}
"""

def run_ollama_game():
    # Update URL to match the new API mount point
    env_url = "http://localhost:7860/api"
    env = GamemasterEnvironment()
    obs = env.reset()
    
    print(f"--- Game Started: Level {env.dungeon_level} ---")
    
    for _ in range(10): # Run for 10 steps
        prompt = f"""
        OBSERVATION:
        Player Input: {obs.player_input}
        System Dice Roll: {obs.system_dice_roll}
        Engine Feedback: {obs.engine_feedback}
        Player HP: {obs.player_hp}
        Monster ({env.current_monster}) HP: {obs.goblin_hp}
        Inventory: {obs.inventory}
        """
        
        print(f"\n[Player]: {obs.player_input}")
        print(f"[Engine]: Roll was {obs.system_dice_roll}")

        response = ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt},
        ])
        
        content = response['message']['content']
        
        try:
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                action_data = json.loads(json_match.group(0))
                action = GamemasterAction(**action_data)
                
                print(f"[GM Narrative]: {action.narrative_response}")
                print(f"[GM Mechanics]: Damage {action.damage_amount} to {action.target_to_damage}")
                
                obs = env.step(action)
                
                print(f"[Reward]: {obs.reward}")
                print(f"[Feedback]: {obs.engine_feedback}")
                
                if obs.done:
                    print("\n--- Game Over ---")
                    break
            else:
                print(f"Error: Model failed to output JSON. Raw output: {content}")
                break
                
        except Exception as e:
            print(f"Error parsing model output: {e}")
            break

if __name__ == "__main__":
    run_ollama_game()

from server.gamemaster_env_environment import GamemasterEnvironment
from models import GamemasterAction

def run_test():
    env = GamemasterEnvironment()
    print("--- Reset ---")
    obs = env.reset()
    print(f"Player: {obs.player_input}")
    print(f"Dice Roll: {obs.system_dice_roll}")

    print("\n--- Step 1 ---")
    # Gamemaster action ignoring roll
    action = GamemasterAction(
        narrative_response="You stare at the cave walls.",
        target_to_damage=None,
        damage_amount=0,
        item_to_give=None
    )
    obs = env.step(action)
    print(f"Reward: {obs.reward}")
    print(f"Feedback: {obs.engine_feedback}")
    print(f"Next Player: {obs.player_input}")
    print(f"Dice Roll: {obs.system_dice_roll}")

if __name__ == '__main__':
    run_test()

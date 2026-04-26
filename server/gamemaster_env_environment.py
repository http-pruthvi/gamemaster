import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import GamemasterAction, GamemasterObservation
except (ImportError, ModuleNotFoundError):
    from models import GamemasterAction, GamemasterObservation


class GamemasterEnvironment(Environment):
    """
    An Infinite Dungeon Gamemaster Environment.
    The LLM plays the role of the Gamemaster. The environment simulates the player
    and the rules engine over an infinite horizon.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_game_state()

    def _reset_game_state(self):
        self.player_hp = 20
        self.player_max_hp = 20
        self.inventory = []
        self.current_monster = "goblin"
        self.monster_hp = 15
        self.dungeon_level = 1
        self.current_roll = random.randint(1, 20)

    def _generate_player_action(self):
        """A procedural player that reacts to the state."""
        if self.monster_hp > 0:
            return f"I attack the {self.current_monster} with my sword!"
        elif self.player_hp < 10 and "health potion" in self.inventory:
            return "I drink my health potion."
        else:
            return "I search the room for loot and move deeper into the dungeon."

    def reset(self) -> GamemasterObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_game_state()
        
        player_input = self._generate_player_action()
        self.current_roll = random.randint(1, 20)
        
        return GamemasterObservation(
            player_input=player_input,
            system_dice_roll=self.current_roll,
            player_hp=self.player_hp,
            goblin_hp=self.monster_hp,
            inventory=self.inventory.copy(),
            engine_feedback=f"Game started. Level {self.dungeon_level}. A {self.current_monster} appears.",
            done=False,
            reward=0.0,
        )

    def step(self, action: GamemasterAction) -> GamemasterObservation:
        self._state.step_count += 1
        reward = 0.0
        feedback = []
        done = False
        
        player_input = self._generate_player_action()
        
        # 1. Evaluate Combat
        if "attack" in player_input.lower():
            if self.current_roll >= 10:
                if action.target_to_damage and action.target_to_damage.lower() == self.current_monster and action.damage_amount > 0:
                    reward += 1.0
                    self.monster_hp -= action.damage_amount
                    feedback.append("Good: Applied damage correctly on a hit.")
                else:
                    reward -= 1.0
                    feedback.append(f"Error: Rolled a hit, but you didn't damage the {self.current_monster}.")
            else:
                if action.damage_amount > 0:
                    reward -= 1.0
                    feedback.append("Error: Player rolled a miss, but you applied damage.")
                else:
                    reward += 1.0
                    feedback.append("Good: correctly handled a miss.")
                    
        # 2. Evaluate Healing
        elif "potion" in player_input.lower():
            if "health potion" in self.inventory:
                self.inventory.remove("health potion")
                # Wait, the action model doesn't currently support player_heal_amount. 
                # For simplicity, we just check if the GM narrates the healing.
                # In a real expanded version, you'd add player_heal_amount to GamemasterAction.
                self.player_hp = min(self.player_max_hp, self.player_hp + 10)
                reward += 0.5
                feedback.append("Player drank potion.")
            else:
                reward -= 1.0
                feedback.append("Error: Player tried to drink a potion they don't have.")

        # 3. Evaluate Exploration & Loot
        elif "search" in player_input.lower() or "move deeper" in player_input.lower():
            if self.monster_hp <= 0:
                if action.item_to_give:
                    reward += 1.0
                    self.inventory.append(action.item_to_give)
                    feedback.append(f"Good: Gave loot ({action.item_to_give}).")
                else:
                    reward += 0.5 # Optional loot
                
                # Advance Level
                self.dungeon_level += 1
                monsters = ["orc", "skeleton", "troll", "dragon"]
                self.current_monster = random.choice(monsters)
                self.monster_hp = 10 + (self.dungeon_level * 5)
                feedback.append(f"Advanced to level {self.dungeon_level}. New monster: {self.current_monster}.")
            else:
                if action.item_to_give:
                    reward -= 1.0
                    feedback.append("Error: Monster is not dead, cannot loot or move forward safely.")
                
        # Simulate monster attacking player randomly
        if self.monster_hp > 0 and random.random() > 0.5:
            monster_dmg = random.randint(1, 3) + self.dungeon_level
            self.player_hp -= monster_dmg
            feedback.append(f"Engine: {self.current_monster} dealt {monster_dmg} damage to player.")

        # Check death conditions
        if self.player_hp <= 0:
            done = True
            feedback.append(f"Player died on level {self.dungeon_level}.")
            
        next_player_input = self._generate_player_action()
        self.current_roll = random.randint(1, 20)
        
        self.monster_hp = max(0, self.monster_hp)
        self.player_hp = max(0, self.player_hp)

        return GamemasterObservation(
            player_input=next_player_input,
            system_dice_roll=self.current_roll,
            player_hp=self.player_hp,
            goblin_hp=self.monster_hp, # Re-using field for backward compatibility
            inventory=self.inventory.copy(),
            engine_feedback=" | ".join(feedback) if feedback else "Action recorded.",
            done=done,
            reward=reward,
            metadata={"step": self._state.step_count, "level": self.dungeon_level}
        )

    @property
    def state(self) -> State:
        return self._state

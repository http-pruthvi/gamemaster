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
    An Advanced Infinite Dungeon Gamemaster Environment with Multi-Dimensional Rewards.
    Tracks Rule Accuracy, Progression, and Narrative Consistency for RL training.
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
        
        # Multi-dimensional reward tracking
        self.rule_accuracy_score = 0.0
        self.progression_score = 0.0
        self.narrative_score = 0.0

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
            engine_feedback=f"Level {self.dungeon_level}: A {self.current_monster} appears.",
            done=False,
            reward=0.0,
        )

    def step(self, action: GamemasterAction) -> GamemasterObservation:
        self._state.step_count += 1
        
        # Reset turn rewards
        turn_rule_reward = 0.0
        turn_progression_reward = 0.0
        turn_narrative_reward = 0.0
        
        feedback = []
        done = False
        
        player_input = self._generate_player_action()
        
        # 1. Evaluate Rule Accuracy (Theme #2: Instruction Following)
        if "attack" in player_input.lower():
            if self.current_roll >= 10:
                # HIT condition
                if action.target_to_damage and action.target_to_damage.lower() == self.current_monster and action.damage_amount > 0:
                    turn_rule_reward = 1.0
                    self.monster_hp -= action.damage_amount
                    feedback.append("CORRECT: Hit applied.")
                else:
                    turn_rule_reward = -1.0
                    feedback.append(f"FAIL: Roll was {self.current_roll} (HIT), but no damage applied.")
            else:
                # MISS condition
                if action.damage_amount > 0:
                    turn_rule_reward = -1.0
                    feedback.append(f"FAIL: Roll was {self.current_roll} (MISS), but damage was applied.")
                else:
                    turn_rule_reward = 1.0
                    feedback.append("CORRECT: Miss handled.")
                    
        # 2. Evaluate Progression (Theme #4: Self-Improvement)
        elif "search" in player_input.lower() or "move deeper" in player_input.lower():
            if self.monster_hp <= 0:
                turn_progression_reward = 1.0
                if action.item_to_give:
                    self.inventory.append(action.item_to_give)
                
                # Advance Level
                self.dungeon_level += 1
                monsters = ["orc", "skeleton", "troll", "dragon"]
                self.current_monster = random.choice(monsters)
                self.monster_hp = 10 + (self.dungeon_level * 5)
                feedback.append(f"PROGRESS: Level {self.dungeon_level}!")
            else:
                turn_progression_reward = -1.0
                feedback.append("FAIL: Cannot advance while monster is alive.")

        # 3. Evaluate Narrative Consistency (Theme #3: World Modeling)
        # Check if narrative mentions the monster or player state
        if action.narrative_response and len(action.narrative_response) > 10:
            if self.current_monster.lower() in action.narrative_response.lower():
                turn_narrative_reward += 0.5
            if action.damage_amount > 0 and ("hit" in action.narrative_response.lower() or "damage" in action.narrative_response.lower()):
                turn_narrative_reward += 0.5
        
        # Monster counter-attack
        if self.monster_hp > 0 and random.random() > 0.5:
            monster_dmg = random.randint(1, 3) + self.dungeon_level
            self.player_hp -= monster_dmg
            feedback.append(f"{self.current_monster} counter-attacks for {monster_dmg} dmg!")

        if self.player_hp <= 0:
            done = True
            feedback.append("GAME OVER: Player died.")
            
        # Update totals
        self.rule_accuracy_score += turn_rule_reward
        self.progression_score += turn_progression_reward
        self.narrative_score += turn_narrative_reward
        
        # Calculate final weighted reward for this turn
        total_turn_reward = (turn_rule_reward * 0.6) + (turn_progression_reward * 0.2) + (turn_narrative_reward * 0.2)
        
        next_player_input = self._generate_player_action()
        self.current_roll = random.randint(1, 20)
        
        self.monster_hp = max(0, self.monster_hp)
        self.player_hp = max(0, self.player_hp)

        return GamemasterObservation(
            player_input=next_player_input,
            system_dice_roll=self.current_roll,
            player_hp=self.player_hp,
            goblin_hp=self.monster_hp,
            inventory=self.inventory.copy(),
            engine_feedback=" | ".join(feedback),
            done=done,
            reward=total_turn_reward,
            metadata={
                "step": self._state.step_count,
                "level": self.dungeon_level,
                "rule_accuracy": turn_rule_reward,
                "progression": turn_progression_reward,
                "narrative_quality": turn_narrative_reward,
                "total_score": self.rule_accuracy_score + self.progression_score + self.narrative_score
            }
        )

    @property
    def state(self) -> State:
        return self._state

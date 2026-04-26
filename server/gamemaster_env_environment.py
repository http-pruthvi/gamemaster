import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import GamemasterAction, GamemasterObservation
except (ImportError, ModuleNotFoundError):
    from models import GamemasterAction, GamemasterObservation

def jaccard_similarity(s1, s2):
    set1 = set(s1.lower().split())
    set2 = set(s2.lower().split())
    if not set1 or not set2: return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

class GamemasterEnvironment(Environment):
    """
    An Advanced Infinite Dungeon Gamemaster Environment.
    Includes: 4-Player Party, System 2 Reasoning, Narrative Diversity, Pacing, and Durable Recall.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_game_state()

    def _reset_game_state(self):
        self.party_hp = {"Fighter": 20, "Rogue": 15, "Wizard": 10, "Cleric": 18}
        self.party_max_hp = {"Fighter": 20, "Rogue": 15, "Wizard": 10, "Cleric": 18}
        self.party_members = ["Fighter", "Rogue", "Wizard", "Cleric"]
        self.inventory = []
        self.current_monster = "goblin"
        self.monster_hp = 15
        self.monster_dmg = 2
        self.dungeon_level = 1
        self.current_roll = random.randint(1, 20)
        
        self.recent_narratives = []
        
        self.rule_accuracy_score = 0.0
        self.progression_score = 0.0
        self.narrative_score = 0.0
        self.pacing_score = 0.0

    def _get_active_player(self):
        alive_players = [p for p in self.party_members if self.party_hp[p] > 0]
        if not alive_players:
            return "None"
        return alive_players[self._state.step_count % len(alive_players)]

    def _generate_player_action(self, active_player):
        if self.monster_hp > 0:
            if active_player == "Wizard":
                return f"I cast Fireball at the {self.current_monster}!"
            elif active_player == "Rogue":
                return f"I sneak behind the {self.current_monster} and backstab it!"
            elif active_player == "Cleric":
                return f"I swing my mace at the {self.current_monster}!"
            else:
                return f"I attack the {self.current_monster} with my sword!"
        elif self.dungeon_level == 5 and "Rusty Key" not in self.inventory:
            return "I try to pick the lock on the Iron Door!"
        elif self.dungeon_level == 5 and "Rusty Key" in self.inventory:
            return "I use the Rusty Key to unlock the Iron Door!"
        else:
            return "I search the room for loot and move deeper into the dungeon."

    def reset(self) -> GamemasterObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_game_state()
        
        self.inventory.append("Rusty Key")
        
        active_player = self._get_active_player()
        player_input = self._generate_player_action(active_player)
        self.current_roll = random.randint(1, 20)
        
        return GamemasterObservation(
            active_player=active_player,
            player_input=player_input,
            system_dice_roll=self.current_roll,
            party_hp=self.party_hp.copy(),
            monster_name=self.current_monster,
            monster_hp=self.monster_hp,
            inventory=self.inventory.copy(),
            engine_feedback=f"Level {self.dungeon_level}: A {self.current_monster} appears.",
            done=False,
            reward=0.0,
        )

    def step(self, action: GamemasterAction) -> GamemasterObservation:
        active_player = self._get_active_player()
        player_input = self._generate_player_action(active_player)
        
        self._state.step_count += 1
        
        turn_rule_reward = 0.0
        turn_progression_reward = 0.0
        turn_narrative_reward = 0.0
        turn_pacing_reward = 0.0
        
        feedback = []
        done = False
        
        if action.gm_logic and len(action.gm_logic) > 10:
            turn_rule_reward += 0.5
        else:
            turn_rule_reward -= 0.5
            feedback.append("FAIL: Missing Chain-of-Thought gm_logic.")

        if "attack" in player_input.lower() or "fireball" in player_input.lower() or "backstab" in player_input.lower() or "swing" in player_input.lower():
            if self.current_roll >= 10:
                if action.target_to_damage and action.target_to_damage.lower() == self.current_monster.lower() and action.damage_amount > 0:
                    turn_rule_reward += 1.0
                    self.monster_hp -= action.damage_amount
                    feedback.append("CORRECT: Hit applied.")
                else:
                    turn_rule_reward -= 1.0
                    feedback.append(f"FAIL: Roll was {self.current_roll} (HIT), but no damage applied.")
            else:
                if action.damage_amount > 0:
                    turn_rule_reward -= 1.0
                    feedback.append(f"FAIL: Roll was {self.current_roll} (MISS), but damage was applied.")
                else:
                    turn_rule_reward += 1.0
                    feedback.append("CORRECT: Miss handled.")

        elif "pick" in player_input.lower() or "unlock" in player_input.lower():
            if "Rusty Key" in self.inventory:
                if "escape" in action.narrative_response.lower() or "unlock" in action.narrative_response.lower() or "open" in action.narrative_response.lower():
                    turn_progression_reward += 5.0
                    feedback.append("EPIC SUCCESS: AI Remembered the Rusty Key from Level 1!")
                    done = True
                else:
                    turn_progression_reward -= 2.0
                    feedback.append("FAIL: AI forgot the party has the Rusty Key and can escape.")

        elif "search" in player_input.lower() or "move deeper" in player_input.lower():
            if self.monster_hp <= 0:
                turn_progression_reward += 1.0
                if action.item_to_give:
                    self.inventory.append(action.item_to_give)
                
                self.dungeon_level += 1
                
                if action.next_monster_name and action.next_monster_hp and action.next_monster_dmg:
                    self.current_monster = action.next_monster_name
                    self.monster_hp = action.next_monster_hp
                    self.monster_dmg = action.next_monster_dmg
                    turn_progression_reward += 1.0
                    feedback.append(f"PROGRESS: AI Generated Level {self.dungeon_level} -> {self.current_monster}!")
                else:
                    self.current_monster = random.choice(["orc", "skeleton", "troll"])
                    self.monster_hp = 10 + (self.dungeon_level * 5)
                    self.monster_dmg = 2 + self.dungeon_level
                    feedback.append(f"PROGRESS: Level {self.dungeon_level} (Default monster used).")
            else:
                turn_progression_reward -= 1.0
                feedback.append("FAIL: Cannot advance while monster is alive.")

        if action.narrative_response:
            max_sim = max([jaccard_similarity(action.narrative_response, r) for r in self.recent_narratives] + [0])
            if max_sim > 0.7:
                turn_narrative_reward -= 0.5
                feedback.append("NARRATIVE PENALTY: Response too repetitive.")
            else:
                turn_narrative_reward += 0.5
            self.recent_narratives.append(action.narrative_response)
            if len(self.recent_narratives) > 5:
                self.recent_narratives.pop(0)

        alive_hp = sum([hp for hp in self.party_hp.values() if hp > 0])
        max_alive_hp = sum([self.party_max_hp[p] for p in self.party_members if self.party_hp[p] > 0])
        if max_alive_hp > 0:
            hp_pct = alive_hp / max_alive_hp
            if 0.1 <= hp_pct <= 0.4:
                turn_pacing_reward += 1.0  
            elif hp_pct < 0.1:
                turn_pacing_reward -= 0.5  
            else:
                turn_pacing_reward += 0.1  
            
        if self.monster_hp > 0 and random.random() > 0.4:
            alive_players = [p for p in self.party_members if self.party_hp[p] > 0]
            if alive_players:
                target_player = random.choice(alive_players)
                self.party_hp[target_player] -= self.monster_dmg
                feedback.append(f"{self.current_monster} attacks {target_player} for {self.monster_dmg} dmg!")

        alive_players_after = [p for p in self.party_members if self.party_hp[p] > 0]
        if not alive_players_after:
            done = True
            feedback.append("GAME OVER: Entire party died.")
            
        self.rule_accuracy_score += turn_rule_reward
        self.progression_score += turn_progression_reward
        self.narrative_score += turn_narrative_reward
        self.pacing_score += turn_pacing_reward
        
        total_turn_reward = (turn_rule_reward * 0.4) + (turn_progression_reward * 0.3) + (turn_narrative_reward * 0.15) + (turn_pacing_reward * 0.15)
        
        next_active_player = self._get_active_player()
        next_player_input = self._generate_player_action(next_active_player)
        self.current_roll = random.randint(1, 20)
        self.monster_hp = max(0, self.monster_hp)
        for p in self.party_members:
            self.party_hp[p] = max(0, self.party_hp[p])

        return GamemasterObservation(
            active_player=next_active_player,
            player_input=next_player_input,
            system_dice_roll=self.current_roll,
            party_hp=self.party_hp.copy(),
            monster_name=self.current_monster,
            monster_hp=self.monster_hp,
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
                "pacing": turn_pacing_reward,
                "total_score": self.rule_accuracy_score + self.progression_score + self.narrative_score + self.pacing_score
            }
        )

    @property
    def state(self) -> State:
        return self._state

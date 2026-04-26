from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import GamemasterAction, GamemasterObservation


class GamemasterEnv(
    EnvClient[GamemasterAction, GamemasterObservation, State]
):
    def _step_payload(self, action: GamemasterAction) -> Dict:
        return {
            "gm_logic": action.gm_logic,
            "narrative_response": action.narrative_response,
            "target_to_damage": action.target_to_damage,
            "damage_amount": action.damage_amount,
            "item_to_give": action.item_to_give,
            "next_monster_name": action.next_monster_name,
            "next_monster_hp": action.next_monster_hp,
            "next_monster_dmg": action.next_monster_dmg,
        }

    def _parse_result(self, payload: Dict) -> StepResult[GamemasterObservation]:
        obs_data = payload.get("observation", {})
        observation = GamemasterObservation(
            player_input=obs_data.get("player_input", ""),
            system_dice_roll=obs_data.get("system_dice_roll", 0),
            player_hp=obs_data.get("player_hp", 0),
            monster_name=obs_data.get("monster_name", "goblin"),
            monster_hp=obs_data.get("monster_hp", 0),
            inventory=obs_data.get("inventory", []),
            player_location=obs_data.get("player_location", [0,0]),
            monster_location=obs_data.get("monster_location", [0,0]),
            engine_feedback=obs_data.get("engine_feedback", ""),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
        )

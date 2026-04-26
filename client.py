from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import GamemasterAction, GamemasterObservation


class GamemasterEnv(
    EnvClient[GamemasterAction, GamemasterObservation, State]
):
    """
    Client for the Gamemaster Env Environment.
    """

    def _step_payload(self, action: GamemasterAction) -> Dict:
        """
        Convert GamemasterAction to JSON payload for step message.
        """
        return {
            "narrative_response": action.narrative_response,
            "target_to_damage": action.target_to_damage,
            "damage_amount": action.damage_amount,
            "item_to_give": action.item_to_give,
        }

    def _parse_result(self, payload: Dict) -> StepResult[GamemasterObservation]:
        """
        Parse server response into StepResult[GamemasterObservation].
        """
        obs_data = payload.get("observation", {})
        observation = GamemasterObservation(
            player_input=obs_data.get("player_input", ""),
            system_dice_roll=obs_data.get("system_dice_roll", 0),
            player_hp=obs_data.get("player_hp", 0),
            goblin_hp=obs_data.get("goblin_hp", 0),
            inventory=obs_data.get("inventory", []),
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
        """
        Parse server response into State object.
        """
        return State(
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
        )

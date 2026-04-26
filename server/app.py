import gradio as gr
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from openenv.core.env_server.http_server import create_app
from server.gamemaster_env_environment import GamemasterEnvironment
from models import GamemasterAction, GamemasterObservation

# 1. OpenEnv API (available at /api)
api_app = create_app(
    GamemasterEnvironment,
    GamemasterAction,
    GamemasterObservation,
    env_name="gamemaster_env",
    max_concurrent_envs=5,
)

# 2. Visual Dashboard
def get_html_state(obs, env_level, monster_name):
    player_pct = (obs.player_hp / 20) * 100
    monster_max = 10 + (env_level * 5)
    monster_pct = (obs.goblin_hp / monster_max) * 100
    return f"""
    <div style='background: #0b0f19; padding: 20px; border-radius: 15px; color: white; font-family: sans-serif;'>
        <div style='display: flex; gap: 20px;'>
            <div style='flex: 1; border: 2px solid #00c8ff; padding: 15px; border-radius: 10px;'>
                <h3 style='color: #00c8ff;'>🛡️ PLAYER HP: {obs.player_hp}/20</h3>
                <div style='background: #333; height: 20px;'><div style='background: #00ff88; width: {player_pct}%; height: 100%;'></div></div>
            </div>
            <div style='flex: 1; border: 2px solid #ff4444; padding: 15px; border-radius: 10px;'>
                <h3 style='color: #ff4444;'>👹 {monster_name.upper()} HP: {obs.goblin_hp}/{monster_max}</h3>
                <div style='background: #333; height: 20px;'><div style='background: #ff0000; width: {monster_pct}%; height: 100%;'></div></div>
            </div>
        </div>
        <p style='text-align: center; color: #ffaa00; font-weight: bold;'>DUNGEON DEPTH: LEVEL {env_level}</p>
    </div>
    """

with gr.Blocks() as visual_ui:
    gr.Markdown("# 🎲 AI Gamemaster RL Dashboard")
    obs_state = gr.State()
    env_state = gr.State()
    
    with gr.Row():
        with gr.Column(scale=2):
            status_html = gr.HTML()
            game_log = gr.Textbox(label="Game History", lines=10)
        with gr.Column(scale=1):
            player_in = gr.Textbox(label="Player Action")
            roll_lab = gr.Label(label="Dice Roll")
            
    with gr.Row():
        narr = gr.Textbox(label="GM Response")
        dmg_val = gr.Number(label="Damage", value=0)
        btn = gr.Button("Execute Turn", variant="primary")

    def run_init():
        e = GamemasterEnvironment()
        o = e.reset()
        return get_html_state(o, e.dungeon_level, e.current_monster), f"Started! {o.player_input}", o.player_input, o.system_dice_roll, e, o

    def run_turn(e, o, n, d):
        a = GamemasterAction(narrative_response=n, damage_amount=d, target_to_damage=e.current_monster)
        o_new = e.step(a)
        return get_html_state(o_new, e.dungeon_level, e.current_monster), f"GM: {n}\nEngine: {o_new.engine_feedback}", o_new.player_input, o_new.system_dice_roll, o_new

    visual_ui.load(run_init, outputs=[status_html, game_log, player_in, roll_lab, env_state, obs_state])
    btn.click(run_turn, inputs=[env_state, obs_state, narr, dmg_val], outputs=[status_html, game_log, player_in, roll_lab, obs_state])

# 3. Mount Together
app = FastAPI()
app.mount("/api", api_app)
app = gr.mount_gradio_app(app, visual_ui, path="/")

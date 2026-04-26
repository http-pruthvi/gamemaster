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

# 2. Visual Dashboard UI
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

with gr.Blocks(title="AI Gamemaster") as visual_ui:
    gr.Markdown("# 🎲 AI Gamemaster RL Dashboard")
    obs_state = gr.State()
    env_state = gr.State()
    
    with gr.Row():
        with gr.Column(scale=2):
            status_html = gr.HTML()
            game_log = gr.Textbox(label="Battle History", lines=10)
        with gr.Column(scale=1):
            player_in = gr.Textbox(label="Simulated Player Action")
            roll_lab = gr.Label(label="Engine Dice Roll")
            
    with gr.Row():
        narr = gr.Textbox(label="Your GM Narrative Response")
        dmg_val = gr.Number(label="Damage to Apply", value=0)
        btn = gr.Button("Execute Turn", variant="primary")

    def run_init():
        e = GamemasterEnvironment()
        o = e.reset()
        return get_html_state(o, e.dungeon_level, e.current_monster), f"Adventure Started! A {e.current_monster} appears.", o.player_input, o.system_dice_roll, e, o

    def run_turn(e, o, n, d):
        a = GamemasterAction(narrative_response=n, damage_amount=d, target_to_damage=e.current_monster)
        o_new = e.step(a)
        return get_html_state(o_new, e.dungeon_level, e.current_monster), f"GM: {n}\nEngine Result: {o_new.engine_feedback}", o_new.player_input, o_new.system_dice_roll, o_new

    visual_ui.load(run_init, outputs=[status_html, game_log, player_in, roll_lab, env_state, obs_state])
    btn.click(run_turn, inputs=[env_state, obs_state, narr, dmg_val], outputs=[status_html, game_log, player_in, roll_lab, obs_state])

# 3. FastAPI Server with Redirects
app = FastAPI()

# Mount the OpenEnv API
app.mount("/api", api_app)

# Support /web for backward compatibility with OpenEnv CLI/HF defaults
@app.get("/web", include_in_schema=False)
async def web_redirect():
    return RedirectResponse(url="/")

# Mount Gradio at the Root
app = gr.mount_gradio_app(app, visual_ui, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

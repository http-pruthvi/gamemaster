import gradio as gr
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from openenv.core.env_server.http_server import create_app
from server.gamemaster_env_environment import GamemasterEnvironment
from models import GamemasterAction, GamemasterObservation

# 1. Create the base OpenEnv API app
api_app = create_app(
    GamemasterEnvironment,
    GamemasterAction,
    GamemasterObservation,
    env_name="gamemaster_env",
    max_concurrent_envs=5,
)

# 2. Define the VISUAL UI
def get_html_state(obs, env_level, monster_name):
    player_pct = (obs.player_hp / 20) * 100
    monster_max = 10 + (env_level * 5)
    monster_pct = (obs.goblin_hp / monster_max) * 100
    
    return f"""
    <div style='display: flex; justify-content: space-between; gap: 20px; font-family: sans-serif; background: #0b0f19; padding: 20px; border-radius: 15px;'>
        <div style='flex: 1; padding: 20px; border: 2px solid #00c8ff; border-radius: 12px; background: #16202c;'>
            <h3 style='color: #00c8ff; margin-top: 0; letter-spacing: 2px;'>🛡️ HERO</h3>
            <div style='background: #333; height: 24px; border-radius: 6px; overflow: hidden; margin-bottom: 10px;'>
                <div style='background: linear-gradient(90deg, #00ff88, #55ff00); width: {player_pct}%; height: 100%; transition: width 0.5s;'></div>
            </div>
            <p style='color: white; font-size: 1.2em;'><b>HP:</b> {obs.player_hp} / 20</p>
            <p style='color: #ffd700;'><b>Loot:</b> {", ".join(obs.inventory) if obs.inventory else "Nothing yet"}</p>
        </div>
        <div style='flex: 1; padding: 20px; border: 2px solid #ff4444; border-radius: 12px; background: #2c1616;'>
            <h3 style='color: #ff4444; margin-top: 0; letter-spacing: 2px;'>👹 {monster_name.upper()}</h3>
            <div style='background: #333; height: 24px; border-radius: 6px; overflow: hidden; margin-bottom: 10px;'>
                <div style='background: linear-gradient(90deg, #ff0000, #ff6600); width: {monster_pct}%; height: 100%; transition: width 0.5s;'></div>
            </div>
            <p style='color: white; font-size: 1.2em;'><b>HP:</b> {obs.goblin_hp} / {monster_max}</p>
            <p style='color: #ffaa00;'><b>Dungeon Depth:</b> Level {env_level}</p>
        </div>
    </div>
    """

with gr.Blocks(theme=gr.themes.Monochrome()) as visual_ui:
    gr.Markdown("# 🎲 AI Gamemaster - Interactive Visual Sandbox")
    gr.Markdown("Test the self-improving rules engine manually. Type a response and check if the HP bars update correctly.")
    
    env_state = gr.State(lambda: GamemasterEnvironment())
    current_obs = gr.State(lambda: GamemasterEnvironment().reset())
    
    with gr.Row():
        with gr.Column(scale=2):
            visual_status = gr.HTML()
            log = gr.Textbox(label="Battle Log", lines=12, interactive=False)
        
        with gr.Column(scale=1):
            player_act = gr.Textbox(label="Simulated Player Input", interactive=False)
            dice_roll = gr.Label(label="Engine Dice Roll (d20)")
            feedback_box = gr.Textbox(label="Rules Engine Feedback", interactive=False)
            
    with gr.Row():
        narrative = gr.Textbox(label="Your GM Narrative", placeholder="e.g. The goblin stumbles back as you strike!")
        with gr.Column():
            dmg = gr.Number(label="Apply Damage", value=0)
            target = gr.Textbox(label="Target Name", value="goblin")
            submit_btn = gr.Button("Submit Action", variant="primary")
            reset_btn = gr.Button("Reset Game")

    def init_ui():
        env = GamemasterEnvironment()
        obs = env.reset()
        return (get_html_state(obs, env.dungeon_level, env.current_monster), 
                f"Adventure begins! A {env.current_monster} blocks your path.", 
                obs.player_input, obs.system_dice_roll, obs.engine_feedback, env, obs)

    def play_step(env, current_obs, narr, d, targ):
        action = GamemasterAction(narrative_response=narr, damage_amount=d, target_to_damage=targ)
        new_obs = env.step(action)
        new_log = f"GM: {narr}\nResult: {new_obs.engine_feedback}\n---\nPlayer: {new_obs.player_input}"
        return (get_html_state(new_obs, env.dungeon_level, env.current_monster), 
                new_log, new_obs.player_input, new_obs.system_dice_roll, new_obs.engine_feedback, new_obs)

    visual_ui.load(init_ui, outputs=[visual_status, log, player_act, dice_roll, feedback_box, env_state, current_obs])
    submit_btn.click(play_step, inputs=[env_state, current_obs, narrative, dmg, target], 
                    outputs=[visual_status, log, player_act, dice_roll, feedback_box, current_obs])
    reset_btn.click(init_ui, outputs=[visual_status, log, player_act, dice_roll, feedback_box, env_state, current_obs])

# 3. COMBINE EVERYTHING INTO ONE APP
app = FastAPI()

# Mount the OpenEnv API at /api
app.mount("/api", api_app)

# Mount the Visual Dashboard at /
app = gr.mount_gradio_app(app, visual_ui, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

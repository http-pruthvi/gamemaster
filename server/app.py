import gradio as gr
from openenv.core.env_server.http_server import create_app
from server.gamemaster_env_environment import GamemasterEnvironment
from models import GamemasterAction, GamemasterObservation

from fastapi.responses import RedirectResponse

# Create the standard OpenEnv App
app = create_app(
    GamemasterEnvironment,
    GamemasterAction,
    GamemasterObservation,
    env_name="gamemaster_env",
    max_concurrent_envs=5,
)

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/web")

# --- CUSTOM VISUAL UI FOR HACKATHON ---
def get_html_state(obs, env_level, monster_name):
    player_pct = (obs.player_hp / 20) * 100
    monster_max = 10 + (env_level * 5)
    monster_pct = (obs.goblin_hp / monster_max) * 100
    
    return f"""
    <div style='display: flex; justify-content: space-between; gap: 20px; font-family: sans-serif;'>
        <div style='flex: 1; padding: 15px; border: 2px solid #00c8ff; border-radius: 10px; background: #001a24;'>
            <h3 style='color: #00c8ff; margin-top: 0;'>🛡️ PLAYER</h3>
            <div style='background: #333; height: 20px; border-radius: 5px;'>
                <div style='background: linear-gradient(90deg, #00ff88, #55ff00); width: {player_pct}%; height: 100%; border-radius: 5px;'></div>
            </div>
            <p style='color: white;'>HP: {obs.player_hp} / 20</p>
            <p style='color: #ffd700;'>Inventory: {", ".join(obs.inventory) if obs.inventory else "Empty"}</p>
        </div>
        <div style='flex: 1; padding: 15px; border: 2px solid #ff4444; border-radius: 10px; background: #240000;'>
            <h3 style='color: #ff4444; margin-top: 0;'>👹 {monster_name.upper()}</h3>
            <div style='background: #333; height: 20px; border-radius: 5px;'>
                <div style='background: linear-gradient(90deg, #ff0000, #ff6600); width: {monster_pct}%; height: 100%; border-radius: 5px;'></div>
            </div>
            <p style='color: white;'>HP: {obs.goblin_hp} / {monster_max}</p>
            <p style='color: #ffaa00;'>Dungeon Level: {env_level}</p>
        </div>
    </div>
    """

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎲 AI Gamemaster RL Environment")
    gr.Markdown("This dashboard allows you to manually play the role of the Gamemaster to test the environment's rules engine.")
    
    env_state = gr.State(lambda: GamemasterEnvironment())
    current_obs = gr.State(lambda: GamemasterEnvironment().reset())
    
    with gr.Row():
        with gr.Column(scale=2):
            visual_status = gr.HTML()
            log = gr.Textbox(label="Game Log", lines=10, interactive=False)
        
        with gr.Column(scale=1):
            player_act = gr.Textbox(label="Current Player Input", interactive=False)
            dice_roll = gr.Label(label="Engine Dice Roll")
            feedback_box = gr.Textbox(label="Engine Rule Feedback", interactive=False)
            
    with gr.Row():
        narrative = gr.Textbox(label="Your GM Narrative Response", placeholder="e.g. You strike the orc!")
        dmg = gr.Number(label="Damage Amount", value=0)
        target = gr.Textbox(label="Target to Damage", value="goblin")
        item = gr.Textbox(label="Item to Give", placeholder="null")
        submit_btn = gr.Button("Submit GM Action", variant="primary")
        reset_btn = gr.Button("Reset Dungeon")

    def init_ui():
        env = GamemasterEnvironment()
        obs = env.reset()
        return (
            get_html_state(obs, env.dungeon_level, env.current_monster),
            f"Game Started! A {env.current_monster} appears.\nPlayer says: {obs.player_input}",
            obs.player_input,
            obs.system_dice_roll,
            obs.engine_feedback,
            env,
            obs
        )

    def play_step(env, current_obs, narr, d, targ, itm):
        action = GamemasterAction(
            narrative_response=narr, 
            damage_amount=d, 
            target_to_damage=targ if targ != "null" else None, 
            item_to_give=itm if itm != "null" else None
        )
        new_obs = env.step(action)
        
        new_log = f"GM: {narr}\nResult: {new_obs.engine_feedback}\n---\nPlayer: {new_obs.player_input}"
        
        return (
            get_html_state(new_obs, env.dungeon_level, env.current_monster),
            new_log,
            new_obs.player_input,
            new_obs.system_dice_roll,
            new_obs.engine_feedback,
            new_obs
        )

    demo.load(init_ui, outputs=[visual_status, log, player_act, dice_roll, feedback_box, env_state, current_obs])
    submit_btn.click(play_step, inputs=[env_state, current_obs, narrative, dmg, target, item], 
                    outputs=[visual_status, log, player_act, dice_roll, feedback_box, current_obs])
    reset_btn.click(init_ui, outputs=[visual_status, log, player_act, dice_roll, feedback_box, env_state, current_obs])

# Mount the visual UI to the FastAPI app
app = gr.mount_gradio_app(app, demo, path="/web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

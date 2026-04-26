import gradio as gr
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from openenv.core.env_server.http_server import create_app

# ROBUST IMPORTS FOR DOCKER
try:
    from .gamemaster_env_environment import GamemasterEnvironment
    from ..models import GamemasterAction, GamemasterObservation
except (ImportError, ModuleNotFoundError):
    try:
        from server.gamemaster_env_environment import GamemasterEnvironment
        from models import GamemasterAction, GamemasterObservation
    except (ImportError, ModuleNotFoundError):
        from gamemaster_env_environment import GamemasterEnvironment
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
def get_html_state(obs, env_level):
    party_html = ""
    max_hps = {"Fighter": 20, "Rogue": 15, "Wizard": 10, "Cleric": 18}
    for player, hp in obs.party_hp.items():
        max_hp = max_hps[player]
        pct = (hp / max_hp) * 100
        color = "#00ff88" if hp > 0 else "#555"
        party_html += f"""
        <div style='margin-bottom: 5px;'>
            <div style='display: flex; justify-content: space-between;'><span style='color: white; font-size: 0.9em;'>{player}</span> <span style='color: #aaa; font-size: 0.8em;'>{hp}/{max_hp}</span></div>
            <div style='background: #333; height: 10px; border-radius: 3px;'><div style='background: {color}; width: {pct}%; height: 100%; border-radius: 3px;'></div></div>
        </div>
        """

    monster_max = 10 + (env_level * 5)
    monster_pct = (obs.monster_hp / monster_max) * 100
    
    return f"""
    <div style='background: #0b0f19; padding: 20px; border-radius: 15px; color: white; font-family: sans-serif;'>
        <div style='display: flex; gap: 20px;'>
            <div style='flex: 1; border: 2px solid #00c8ff; padding: 15px; border-radius: 10px;'>
                <h3 style='color: #00c8ff; margin-top: 0;'>🛡️ PARTY</h3>
                {party_html}
                <p style='color: #ffd700; margin-top: 10px; font-size: 0.9em;'>Inventory: {", ".join(obs.inventory) if obs.inventory else "Empty"}</p>
            </div>
            <div style='flex: 1; border: 2px solid #ff4444; padding: 15px; border-radius: 10px;'>
                <h3 style='color: #ff4444; margin-top: 0;'>👹 {obs.monster_name.upper()}</h3>
                <div style='background: #333; height: 20px; border-radius: 5px;'><div style='background: #ff0000; width: {monster_pct}%; height: 100%; border-radius: 5px;'></div></div>
                <p style='color: #aaa; font-size: 0.9em; margin-top: 5px;'>HP: {obs.monster_hp}/{monster_max}</p>
                <p style='color: #ffaa00; margin-top: 15px;'>DUNGEON LEVEL: {env_level}</p>
            </div>
        </div>
    </div>
    """

with gr.Blocks(title="AI Gamemaster", theme=gr.themes.Monochrome()) as visual_ui:
    gr.Markdown("# 🎲 AI Gamemaster - Autonomous RL Dashboard")
    gr.Markdown("The AI learns through reinforcement. If the party fails, the dungeon will automatically reset.")
    
    obs_state = gr.State()
    env_state = gr.State()
    
    with gr.Row():
        with gr.Column(scale=2):
            status_html = gr.HTML()
            game_log = gr.Textbox(label="Battle History", lines=8)
        with gr.Column(scale=1):
            player_in = gr.Textbox(label="Simulated Player Action", interactive=False)
            roll_lab = gr.Label(label="Engine Dice Roll")
            
    with gr.Row():
        with gr.Column(scale=2):
            gm_log_out = gr.Textbox(label="[System 2] AI GM Logic", interactive=False)
            narr_out = gr.Textbox(label="AI GM Narrative Response", lines=3, interactive=False)
        with gr.Column(scale=1):
            dmg_val = gr.Number(label="Applied Damage", value=0, interactive=False)
            btn = gr.Button("Execute AI Turn", variant="primary")
            reset_btn = gr.Button("Reset Dungeon")

    def run_init():
        e = GamemasterEnvironment()
        o = e.reset()
        return (get_html_state(o, e.dungeon_level), 
                f"Adventure Started! A {o.monster_name} appears.", 
                f"[{o.active_player}]: {o.player_input}", 
                o.system_dice_roll, 
                "Awaiting logic...", 
                "Awaiting narrative...", 
                0, e, o)

    def run_turn(e, o):
        if o.done:
            return run_init()

        # 1. "AI Decision Logic"
        is_hit = o.system_dice_roll >= 10
        is_search = "search" in o.player_input.lower() or "move" in o.player_input.lower()
        is_unlock = "unlock" in o.player_input.lower()
        
        logic = f"Engine rolled {o.system_dice_roll}. "
        if is_hit:
            logic += f"Threshold 10 met. Applying 5 damage to {o.monster_name}."
            d = 5
            t = o.monster_name
            n = f"With a powerful strike, the {o.active_player} hits the {o.monster_name} for {d} damage!"
        elif is_search and o.monster_hp <= 0:
            logic += f"Monster is dead. Advancing level."
            d = 0
            t = None
            n = f"The {o.monster_name} is defeated. The party loots the room and descends deeper."
        elif is_unlock and "Rusty Key" in o.inventory:
            logic += "Player has key. Unlocking door."
            d = 0
            t = None
            n = "The party inserts the Rusty Key. The doors groan open, path is clear!"
        else:
            logic += f"Miss or illegal action. 0 damage."
            d = 0
            t = None
            n = f"The {o.active_player} swings, but the {o.monster_name} dodges!"

        # 2. Execute Action
        a = GamemasterAction(gm_logic=logic, narrative_response=n, damage_amount=d, target_to_damage=t)
        o_new = e.step(a)
        
        # Check for immediate Game Over
        if o_new.done:
            msg = "PARTY FAILED! Re-running Quest..."
            return (get_html_state(o_new, e.dungeon_level), msg, "QUEST OVER", 0, "Dungeon Failure", "The heroes have fallen...", 0, o_new)
        
        log_entry = f"AI Logic: {logic}\nAI Narrative: {n}\nEngine Result: {o_new.engine_feedback}\n---\n[{o_new.active_player}]: {o_new.player_input}"
        
        return (get_html_state(o_new, e.dungeon_level), 
                log_entry, 
                f"[{o_new.active_player}]: {o_new.player_input}", 
                o_new.system_dice_roll, 
                logic, n, d, o_new)

    visual_ui.load(run_init, outputs=[status_html, game_log, player_in, roll_lab, gm_log_out, narr_out, dmg_val, env_state, obs_state])
    btn.click(run_turn, inputs=[env_state, obs_state], outputs=[status_html, game_log, player_in, roll_lab, gm_log_out, narr_out, dmg_val, obs_state])
    reset_btn.click(run_init, outputs=[status_html, game_log, player_in, roll_lab, gm_log_out, narr_out, dmg_val, env_state, obs_state])

# 3. Server
app = FastAPI()
app.mount("/api", api_app)
@app.get("/web", include_in_schema=False)
async def web_redirect(): return RedirectResponse(url="/")
app = gr.mount_gradio_app(app, visual_ui, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

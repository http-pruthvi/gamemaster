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
    gr.Markdown("# 🎲 AI Gamemaster - Bleeding Edge Environment (4 Players)")
    gr.Markdown("Test the latest mechanics: 4-Player Party Dynamics, System 2 Reasoning, and Durable Recall.")
    
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
            gm_log_in = gr.Textbox(label="[System 2] GM Logic (Chain-of-Thought)", placeholder="Explain why you are making this ruling...")
            narr = gr.Textbox(label="GM Narrative Response", lines=3)
        with gr.Column(scale=1):
            dmg_val = gr.Number(label="Damage to Apply", value=0)
            target_val = gr.Textbox(label="Target Name", value="goblin")
            item_val = gr.Textbox(label="Item to Give (optional)", placeholder="null")
            with gr.Accordion("Advanced: Generate Next Monster", open=False):
                nm_name = gr.Textbox(label="Next Monster Name")
                nm_hp = gr.Number(label="Next Monster HP", value=0)
                nm_dmg = gr.Number(label="Next Monster DMG", value=0)
            btn = gr.Button("Execute Turn", variant="primary")

    def run_init():
        e = GamemasterEnvironment()
        o = e.reset()
        return get_html_state(o, e.dungeon_level), f"Adventure Started! A {o.monster_name} appears.", f"[{o.active_player}]: {o.player_input}", o.system_dice_roll, e, o

    def run_turn(e, o, l, n, d, t, itm, nmn, nmh, nmd):
        a = GamemasterAction(
            gm_logic=l,
            narrative_response=n,
            damage_amount=int(d) if d else 0,
            target_to_damage=t if t else None,
            item_to_give=itm if itm and itm != "null" else None,
            next_monster_name=nmn if nmn else None,
            next_monster_hp=int(nmh) if nmh else None,
            next_monster_dmg=int(nmd) if nmd else None
        )
        o_new = e.step(a)
        log_entry = f"GM Logic: {l}\nGM Narrative: {n}\nEngine Feedback: {o_new.engine_feedback}\n---\n[{o_new.active_player}]: {o_new.player_input}"
        return get_html_state(o_new, e.dungeon_level), log_entry, f"[{o_new.active_player}]: {o_new.player_input}", o_new.system_dice_roll, o_new

    visual_ui.load(run_init, outputs=[status_html, game_log, player_in, roll_lab, env_state, obs_state])
    btn.click(run_turn, inputs=[env_state, obs_state, gm_log_in, narr, dmg_val, target_val, item_val, nm_name, nm_hp, nm_dmg], outputs=[status_html, game_log, player_in, roll_lab, obs_state])

# 3. FastAPI Server with Redirects
app = FastAPI()

app.mount("/api", api_app)

@app.get("/web", include_in_schema=False)
async def web_redirect():
    return RedirectResponse(url="/")

app = gr.mount_gradio_app(app, visual_ui, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

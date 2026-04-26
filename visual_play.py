import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Layout
from rich.table import Table
from rich.progress import ProgressBar
from rich import print as rprint
from server.gamemaster_env_environment import GamemasterEnvironment
from models import GamemasterAction

console = Console()

def make_hp_bar(current, max_hp, color="green"):
    percentage = max(0, min(1, current / max_hp))
    bar_width = 20
    filled = int(bar_width * percentage)
    bar = "█" * filled + "░" * (bar_width - filled)
    return f"[{color}][{bar}][/] {current}/{max_hp} HP"

def run_visual_demo():
    env = GamemasterEnvironment()
    obs = env.reset()
    
    with console.screen() as screen:
        for turn in range(1, 11):
            # 1. Display the "World State" Panel
            state_table = Table.grid(expand=True)
            state_table.add_column(justify="left")
            state_table.add_column(justify="right")
            
            player_hp_view = make_hp_bar(obs.player_hp, 20, "green")
            monster_hp_view = make_hp_bar(obs.goblin_hp, 10 + (env.dungeon_level * 5), "red")
            
            state_table.add_row(f"[bold cyan]PLAYER[/]: {player_hp_view}", f"[bold red]{env.current_monster.upper()}[/]: {monster_hp_view}")
            state_table.add_row(f"[yellow]Inventory[/]: {', '.join(obs.inventory) if obs.inventory else 'Empty'}", f"[bold white]DUNGEON LEVEL[/]: {env.dungeon_level}")

            header = Panel(state_table, title=f"[bold white]Turn {turn}[/]", border_style="blue")
            
            # 2. Display the Action
            player_panel = Panel(f"[italic]{obs.player_input}[/]", title="[bold yellow]Player Action[/]", border_style="yellow")
            
            # 3. Dice Roll Logic
            roll_panel = Panel(f"🎲 [bold white]The Engine rolled a {obs.system_dice_roll}[/]", border_style="magenta")
            
            console.clear()
            console.print(header)
            console.print(player_panel)
            console.print(roll_panel)
            
            # 4. Simulate the GM (AI) thinking and acting
            # In a real run, this would be the LLM's response
            rprint("\n[italic grey]AI Gamemaster is deciding...[/]")
            time.sleep(1.5)
            
            # Mocking a "Correct" GM Action for visual clarity
            is_hit = obs.system_dice_roll >= 10
            is_search = "search" in obs.player_input.lower()
            
            if is_hit:
                narrative = f"You lunge forward! The {env.current_monster} screams as your blade strikes home."
                action = GamemasterAction(narrative_response=narrative, target_to_damage=env.current_monster, damage_amount=5)
            elif is_search:
                narrative = f"The {env.current_monster} lies defeated. You find a shiny object in the dust."
                action = GamemasterAction(narrative_response=narrative, item_to_give="gold coin")
            else:
                narrative = f"You swing wildly, but the {env.current_monster} dances out of reach."
                action = GamemasterAction(narrative_response=narrative, damage_amount=0)

            gm_panel = Panel(f"{action.narrative_response}\n\n[bold green]System Output:[/] {{'damage': {action.damage_amount}, 'target': '{action.target_to_damage}', 'item': '{action.item_to_give}'}}", 
                             title="[bold blue]AI Gamemaster Response[/]", border_style="blue")
            
            console.print(gm_panel)
            
            obs = env.step(action)
            rprint(f"\n[bold white]Feedback:[/] [italic]{obs.engine_feedback}[/]")
            
            if obs.done:
                rprint("\n[bold red]─── GAME OVER ───[/]")
                break
                
            time.sleep(2)

if __name__ == "__main__":
    run_visual_demo()

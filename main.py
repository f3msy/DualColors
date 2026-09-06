from __future__ import annotations
import time

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich import box

try:
    from pydualsense import pydualsense
except ImportError:
    pydualsense = None

console = Console()

Color_File = Path("colors.txt")
RGB = Tuple[int, int, int]

@dataclass
class AppState:
    colors: Dict[str, str] = field(default_factory=dict)
    controller: Optional[object] = None
    connected: bool = False
    current_color: Optional[str] = None
    current_rgb: Optional[RGB] = None

class ColorLibrary:
    @staticmethod
    def load(path: Path = Color_File) -> Tuple[Dict[str, str], int]:
        colors: Dict[str, str] = {}
        skipped = 0

        if not path.exists():
            console.print(f"[red]Color file not found: {path}[/red]")
            return colors, skipped

        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            name, rgb = (part.strip() for part in line.split("=", 1))
            name = name.lower()

            if ColorLibrary._is_valid_rgb(rgb):
                colors[name] = rgb
            else:
                skipped += 1

        return colors, skipped

    @staticmethod
    def _is_valid_rgb(rgb: str) -> bool:
        try:
            values = tuple(int(v) for v in rgb.split(","))
        except ValueError:
            return False
        return len(values) == 3 and all(0 <= v <= 255 for v in values)


def hsv_to_rgb(h: float, s: float, v: float) -> RGB:
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def rgb_swatch(rgb: RGB, width: int = 24) -> Text:
    r, g, b = rgb
    return Text("█" * width, style=f"rgb({r},{g},{b})")

class Controller:
    @staticmethod
    def connect() -> Optional[object]:
        if pydualsense is None:
            return None
        try:
            ds = pydualsense()
            ds.init()
            return ds
        except Exception:
            return None

    @staticmethod
    def set_color(ds: object, rgb: RGB) -> bool:
        try:
            ds.light.setColorI(*rgb)
            return True
        except Exception:
            return False

    @staticmethod
    def close(ds: Optional[object]) -> None:
        if ds is None:
            return
        try:
            ds.close()
        except Exception:
            pass


def print_header(state: AppState) -> None:
    status = "[green]● Connected[/green]" if state.connected else "[red]● Not Connected[/red]"
    console.print(Panel(
        "[bold cyan]DualColors[/bold cyan]\n"
        "[dim]A tool for managing your DualSense Controller's RGB lighting.[/dim]",
        border_style="cyan",
    ))
    console.print(f"  Controller: {status}\n")

def print_menu() -> str:
    menu = Table.grid(padding=(0, 2))
    menu.add_column(style="bold cyan", justify="right")
    menu.add_column()
    menu.add_row("1", "Select Color")
    menu.add_row("2", "RGB")
    menu.add_row("3", "List Colors")
    menu.add_row("4", "Info")
    menu.add_row("5", "Exit")

    console.print(Panel(menu, title="Menu", border_style="blue"))
    return Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5"], default="1")

def print_error(message: str, details: str = "") -> None:
    body = f"[bold red]Error[/bold red]\n\n{message}"
    if details:
        body += f"\n\n[dim]{details}[/dim]"
    console.print(Panel(body, title="Error", border_style="red"))

def print_colors_table(colors: Dict[str, str]) -> None:
    table = Table(title="Available Colors", box=box.ROUNDED)
    table.add_column("Color", style="cyan")
    table.add_column("RGB", style="magenta")
    table.add_column("Preview", justify="center")

    for name in sorted(colors):
        r, g, b = (int(v) for v in colors[name].split(","))
        table.add_row(name, colors[name], Text("███", style=f"rgb({r},{g},{b})"))

    console.print(table)

def print_status(state: AppState) -> None:
    status_text = "[green]Connected[/green]" if state.connected else "[red]Disconnected[/red]"
    border_style = "green" if state.connected else "red"
    
    console.print(Panel(
        "Device:   DualSense (PlayStation 5)\n"
        f"Status:   {status_text}\n"
        f"Current:  {state.current_color or '[dim]none set[/dim]'}\n"
        f"RGB:      {state.current_rgb or '[dim]none set[/dim]'}",
        title="Info",
        border_style=border_style,
    ))

def action_select_color(state: AppState) -> None:
    console.clear()
    console.print(Panel(
        "[bold]Select a Color[/bold] [dim](type 'back' to return)[/dim]",
        border_style="blue",
    ))

    while True:
        name = Prompt.ask("Color name").strip().lower()

        if name in ("back", "0", ""):
            return

        if name not in state.colors:
            console.print("[red]Color not found. See 'List Colors' in the main menu.[/red]")
            continue

        rgb = tuple(int(v) for v in state.colors[name].split(","))

        if Controller.set_color(state.controller, rgb):
            r, g, b = rgb
            console.print(f"[rgb({r},{g},{b}) bold]{name}[/rgb({r},{g},{b}) bold] - RGB {rgb}")
            state.current_color, state.current_rgb = name, rgb
        else:
            console.print("[red]Failed to set color[/red]")

        if not Confirm.ask("\nSelect another color?", default=False):
            return

def action_rainbow_mode(state: AppState) -> None:
    console.clear()
    console.print(Panel("[bold]RGB [green]Enabled[/green][/bold]\n\nPress CTRL+C to stop\n\nIf you close this Window, the RGB Mode will automatically stop.", border_style="cyan"))

    hue = 0.0
    try:
        while True:
            rgb = hsv_to_rgb(hue, 1, 1)
            Controller.set_color(state.controller, rgb)
            state.current_rgb = rgb
            state.current_color = "RGB Mode"
            hue = (hue + 2) % 360
            time.sleep(0.05)
    except KeyboardInterrupt:
        console.print("\n[yellow]RGB stopped.[/yellow]")
        state.controller.light.setColorI(0,0,145) # automatically set the color to default (darkish blue) when RGB mode stops
        state.current_color = "Default"

def action_list_colors(state: AppState) -> None:
    console.clear()
    print_colors_table(state.colors)
    Prompt.ask("\nPress Enter to continue", default="")

def action_show_status(state: AppState) -> None:
    console.clear()
    print_status(state)
    Prompt.ask("\nPress Enter to continue", default="")


Menu_Options = {
    "1": action_select_color,
    "2": action_rainbow_mode,
    "3": action_list_colors,
    "4": action_show_status,
}
Connection_Req = {"1", "2", "4"}

def initialize() -> AppState:
    state = AppState()

    with console.status("[bold]Initializing Astro...[/bold]"):
        state.colors, skipped = ColorLibrary.load()
        state.controller = Controller.connect()
        state.connected = state.controller is not None

    if skipped:
        console.print(f"[yellow]⚠ {skipped} invalid color entries were skipped.[/yellow]\n")

    return state

def main() -> None:
    console.clear()
    state = initialize()

    if not state.colors:
        print_error(f"No valid colors found in '{Color_File}'.")
        return

    if pydualsense is None:
        print_error(
            "Some dependencies are missing",
            "Install them with: pip install pydualsense hidapi",
        )
        return

    try:
        while True:
            console.clear()
            print_header(state)
            choice = print_menu()

            if choice == "5":
                break

            if choice in Connection_Req and not state.connected:
                print_error(
                    "Unable to connect to the DualSense controller",
                    "Make sure that your controller is connected to your PC\n"
                )
                Prompt.ask("\nPress Enter to continue", default="")
                continue

            Menu_Options[choice](state)
    finally:
        try:
            state.controller.light.setColorI(0,0,145) # set color to default when closing / stopping the tool
        except Exception:
            pass
        console.print("[yellow]Stopping...[/yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold][yellow]You can now close this window.[/yellow][/bold]")
    except Exception as exc:
        print_error("Unexpected error occurred", str(exc))

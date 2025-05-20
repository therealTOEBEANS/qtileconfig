# TOEBEANS' qtile config
# (c) Thor Smith 2025

# --- Imports ---
import logging # Standard Python logging module
import subprocess # For running external commands (e.g., autostart script)
import os # For autostart script path

from libqtile import bar, layout, qtile, widget, hook
from libqtile.config import Click, Drag, Group, Key, KeyChord, Match, Screen
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal

# --- Variables ---
mod = "mod4"  # Sets Super/Windows key as the primary modifier
mod1 = "mod1" # Sets Alt key as an alternative modifier
# terminal = guess_terminal() # Automatically detects the default terminal
terminal = "kitty" # CHANGED: Set kitty as the default terminal

# -- Font Variables --
font_primary = "Noto Sans" # A common, good-looking alternative if DejaVu Sans isn't preferred/installed

# -- Color Variables --
# --- Base Colors ---
color_red = "#FF0000"          # Red, often used for alerts or important highlights
color_white = "#FFFFFF"        # White
color_black = "#000000"        # Black
color_orange = "#FFA500"       # Orange, used for Brightness Control chord
color_light_blue = "#ADD8E6"   # Light Blue, used for Volume Control chord

# --- UI Element Colors ---
color_active_border = color_red       # Border color for focused windows (red)
color_inactive_border = color_white   # Border color for unfocused windows (white)
color_alert_foreground = color_red  # Foreground color for alerts

# --- Chord Widget Specific Colors ---
color_launch_chord_foreground = color_alert_foreground
color_launch_chord_background = color_white
color_brightness_chord_foreground = color_orange
color_brightness_chord_background = color_black
color_volume_chord_foreground = color_light_blue
color_volume_chord_background = color_black


# Get a logger instance
logger = logging.getLogger(__name__)
logger.critical("QTILE CONFIG.PY: Script execution started - App launcher changes implemented.")

# --- Gap Configuration ---
DEFAULT_GAP_SIZE = 5
_gaps_enabled_state = True  # True means gaps are on by default

# --- Layouts ---
# Define layouts here so the toggle functions can modify their instances before reload
layouts = [
    layout.Columns(
        border_focus=color_active_border,
        border_normal=color_inactive_border,
        border_focus_stack=[color_active_border, color_inactive_border],
        border_width=4,
        margin=DEFAULT_GAP_SIZE if _gaps_enabled_state else 0
    ),
    layout.Max(
        margin=DEFAULT_GAP_SIZE if _gaps_enabled_state else 0,
        border_focus=color_active_border,
        border_normal=color_inactive_border,
        border_width=4
        ),
    layout.Tile(
        margin=DEFAULT_GAP_SIZE if _gaps_enabled_state else 0,
        border_width=4,
        border_focus=color_active_border,
        border_normal=color_inactive_border
        )
]

# --- Toggle Gaps Function ---
def toggle_gaps(qtile_instance):
    """Toggles window gaps on/off by modifying layout margins and reloading config."""
    global _gaps_enabled_state
    _gaps_enabled_state = not _gaps_enabled_state
    new_margin = DEFAULT_GAP_SIZE if _gaps_enabled_state else 0

    for lyt_idx, _ in enumerate(qtile_instance.config.layouts): 
        if hasattr(layouts[lyt_idx], 'margin'):
             layouts[lyt_idx].margin = new_margin
    
    if 'floating_layout' in globals() and hasattr(floating_layout, 'margin'):
        floating_layout.margin = new_margin

    logger.info(f"Toggling gaps. New state: {'Enabled' if _gaps_enabled_state else 'Disabled'}. Margin: {new_margin}")
    qtile_instance.reload_config()

# --- Keybindings ---
keys = [
    # --- Window Navigation ---
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left window"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right window"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "space", lazy.layout.next(), desc="Move window focus to next window in stack"),

    # --- Window Manipulation (Moving Windows) ---
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move focused window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move focused window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move focused window down in stack"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move focused window up in stack"),

    # --- Window Sizing (Resizing Windows) ---
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow focused window to the left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow focused window to the right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow focused window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow focused window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes to default"),

    # --- Layout Specific Commands ---
    Key([mod, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle between split/unsplit sides of stack (Columns layout)"),

    # --- Application Launchers ---
    Key([mod], "Return", lazy.spawn(terminal), desc=f"Launch default terminal ({terminal})"), # Updated desc
    Key([mod], "r", lazy.spawncmd(), desc="Spawn a command using Qtile's prompt widget"),

    # --- NEW/MODIFIED Application Launchers (Super+Alt) ---
    Key([mod, mod1], "f", lazy.spawn("xfe"), desc="Launch XFE file explorer"),
    Key([mod, mod1], "semicolon", lazy.spawn(terminal), desc=f"Launch {terminal} (Super+Alt+;)"),
    Key([mod, mod1], "t", lazy.spawn("codium"), desc="Launch Codium text editor"),
    Key([mod, mod1], "e", lazy.spawn("xdg-open /home/tori/code/stable/edtr3.html"), desc="Open edtr3.html"),


    # --- Window Management ---
    Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen for focused window"),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating state for focused window"),

    # --- Qtile Management ---
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload Qtile configuration"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),

    # --- Rofi Launcher Chord ---
    KeyChord([mod], "tab",
        [
            Key( [], "Tab", lazy.spawn("rofi -show drun"), lazy.ungrab_chord(), desc='Rofi: Show applications (drun)'),
            Key( [], "w", lazy.spawn("rofi -show window"), lazy.ungrab_chord(), desc='Rofi: Show open windows'),
            Key( [], "q", lazy.spawn("rofi -show run"), lazy.ungrab_chord(), desc='Rofi: Show run command prompt'),
        ], name="Rofi Launcher", desc="Access Rofi launchers"
    ),

    # --- Brightness Control Chord ---
    KeyChord([mod1], "j",
       [
           Key( [], "k", lazy.spawn('brightnessctl set +5%'), desc='Increase screen brightness by 5%'),
           Key( [], "j", lazy.spawn('brightnessctl set 5%-'), desc='Decrease screen brightness by 5%'),
       ], name="Brightness Control", mode=True, desc="Toggle brightness control mode"
    ),

    # --- Volume Control Chord ---
    KeyChord([mod1], "u",
       [
           Key( [], "i", lazy.spawn('amixer -D pulse sset Master 5%+'), desc='Increase volume by 5%'),
           Key( [], "u", lazy.spawn('amixer -D pulse sset Master 5%-'), desc='Decrease volume by 5%'),
       ], name="Volume Control", mode=True, desc="Toggle volume control mode"
    ),

    # --- Gaps Toggle Keybinding ---
    Key([mod, "control", "shift"], "z", lazy.function(toggle_gaps), desc="Toggle window gaps"),
]

# --- Virtual Terminal (VT) Switching ---
for vt_num in range(1, 8):
    keys.append(
        Key(
            ["control", mod1], 
            f"f{vt_num}",
            lazy.core.change_vt(vt_num).when(func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to Virtual Terminal {vt_num}"
        )
    )

# --- Groups (Workspaces) & Group Keybindings ---
groups = [Group(i) for i in "123456789"]

for i in groups:
    keys.extend([
        Key(
            [mod], i.name,
            lazy.group[i.name].toscreen(),
            desc=f"Switch to group {i.name}"
        ),
        Key(
            [mod, "shift"], i.name,
            lazy.window.togroup(i.name, switch_group=True),
            desc=f"Move focused window to group {i.name} & follow"
        )
    ])


# --- Widget Defaults ---
widget_defaults = dict(
    font=font_primary,
    fontsize=12,
    padding=3,
    background=color_black
)
extension_defaults = widget_defaults.copy()

# --- Screens & Bar ---
screens = [
    Screen(
        bottom=bar.Bar(
            [
                widget.GroupBox(
                    desc="Displays group (workspace) numbers",
                    highlight_method='block',
                    this_current_screen_border=color_red,
                    active=color_red,
                    inactive=color_white,
                    hide_unused=False,
                    disable_drag=True,
                    use_mouse_wheel=False,
                    padding_x=5,
                    borderwidth=2,
                ),
                widget.Prompt(desc="Input prompt for lazy.spawncmd()"),
                widget.WindowName(desc="Displays the name of the focused window"),
                widget.Chord(
                    chords_colors={
                        "Rofi Launcher": (color_launch_chord_foreground, color_launch_chord_background),
                        "Brightness Control": (color_brightness_chord_foreground, color_brightness_chord_background),
                        "Volume Control": (color_volume_chord_foreground, color_volume_chord_background)
                    },
                    name_transform=lambda name: name.upper(),
                    desc="Displays active key chord name"
                ),
                widget.TextBox(
                    "[g]", 
                    mouse_callbacks={
                        'Button1': lazy.spawn('xdg-open https://gemini.google.com/app'),
                        'Button3': lazy.spawn('xdg-open https://www.google.com/')
                    },
                    foreground=color_white, 
                    desc="Clickable links for Gemini and Google"
                ),
                widget.TextBox(
                    "[f]",
                    mouse_callbacks={
                        'Button1': lazy.spawn('thunar'),
                        'Button3': lazy.spawn('veracrypt')
                    },
                    foreground=color_white,
                    desc="Clickable links for Thunar and Veracrypt"
                ),
                widget.Battery(
                    format='{char} {percent:2.0%}',
                    update_interval=60,
                    low_foreground=color_alert_foreground,
                    low_percentage=0.25,
                    charge_char='⚡',
                    discharge_char='🔋',
                    desc="Displays battery status"
                ),
                widget.Systray(desc="System tray for notification icons"),
                widget.Clock(
                    format="%m-%d-%y %a %I:%M:%S %p",
                    foreground=color_red,
                    desc="Displays date and time"
                ),
            ],
            24, # Bar height
            background=color_black
        ),
    ),
]

# --- Mouse Bindings for Floating Layouts ---
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front())
]

# --- Other Qtile Settings ---
dgroups_key_binder = None
dgroups_app_rules = []
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False

floating_layout = layout.Floating( 
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),
        Match(wm_class="makebranch"),
        Match(wm_class="maketag"),
        Match(wm_class="ssh-askpass"),
        Match(title="branchdialog"),
        Match(title="pinentry"),
    ],
    margin=DEFAULT_GAP_SIZE if _gaps_enabled_state else 0,
    border_focus=color_active_border,
    border_normal=color_inactive_border,
    border_width=4
)

auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True
auto_minimize = True

# --- Autostart Applications ---
@hook.subscribe.startup_once
def autostart():
    home = os.path.expanduser('~/.config/qtile/autostart.sh')
    if os.path.exists(home):
        logger.info(f"Running autostart script: {home}")
        subprocess.run([home], check=False) 
    else:
        logger.warning(f"Autostart script not found: {home}")

# --- Wayland Specific (Optional) ---
wl_input_rules = None
wl_xcursor_theme = None
wl_xcursor_size = 24

# --- WM Name (for Java compatibility) ---
wmname = "LG3D"

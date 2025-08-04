# ==============================================================================
# === TOEBEANS' LAPTOP QTILE CONFIG ============================================
# === (c) Thor Smith 2025 ======================================================
# ==============================================================================

# ==============================================================================
# === IMPORTS ==================================================================
# ==============================================================================
import logging
import os
import subprocess

from libqtile import bar, hook, layout, qtile, widget
from libqtile.config import Click, Drag, Group, Key, KeyChord, Match, Screen
from libqtile.lazy import lazy
from libqtile.widget import base

# ==============================================================================
# === CONSTANTS & VARIABLES ====================================================
# ==============================================================================

# --- Keys ---
MOD = "mod4"  # Super/Windows key
ALT = "mod1"  # Alt key

# --- Applications ---
TERMINAL = "kitty"

# --- Fonts ---
FONT_PRIMARY = "monospace"

# --- Gaps ---
DEFAULT_GAP_SIZE = 5
gaps_enabled = True  # True means gaps are on by default

# --- Color Palette ---
# A centralized dictionary for all colors makes theming easier.
colors = {
    # --- Base Colors ---
    "red":          "#FF0000",
    "white":        "#FFFFFF",
    "black":        "#000000",
    "orange":       "#FFA500",
    "light_blue":   "#ADD8E6",

    # --- UI Element Colors ---
    "border_active":   "#FF0000", # Red
    "border_inactive": "#FFFFFF", # White
    "alert":           "#FF0000", # Red

    # --- Chord Widget Specific Colors ---
    "launch_chord_fg":      "#FF0000",
    "launch_chord_bg":      "#FFFFFF",
    "brightness_chord_fg":  "#FFA500",
    "brightness_chord_bg":  "#000000",
    "volume_chord_fg":      "#ADD8E6",
    "volume_chord_bg":      "#000000",
    "bluetooth_chord_fg":   "#FF0000",
    "bluetooth_chord_bg":   "#FFFFFF",
}

# --- Logging ---
# Get a logger instance for debugging.
logger = logging.getLogger(__name__)
logger.critical("QTILE CONFIG.PY: Script execution started.")


# ==============================================================================
# === CUSTOM WIDGETS & FUNCTIONS ===============================================
# ==============================================================================

class BluetoothCtlWidget(base.ThreadPoolText):
    """A custom widget to control Bluetooth power and open bluetoothctl."""
    def __init__(self, **config):
        base.ThreadPoolText.__init__(self, "", **config)
        self.update_interval = 5
        self.add_callbacks({
            'Button1': self.toggle_power,
            'Button3': self.open_bluetoothctl,
        })

    def _get_power_status(self):
        """Gets the current Bluetooth power status."""
        try:
            output = subprocess.check_output(['bluetoothctl', 'show'], text=True)
            return "On" if 'Powered: yes' in output else "Off"
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "N/A"

    def poll(self):
        """Polls for the Bluetooth status and updates the widget text."""
        status = self._get_power_status()
        return f"BT: {status}"

    def toggle_power(self):
        """Toggles Bluetooth power on or off."""
        status = self._get_power_status()
        if status == "On":
            qtile.cmd_spawn('bluetoothctl power off')
            qtile.cmd_spawn('notify-send "Bluetooth" "Bluetooth turned OFF."')
        elif status == "Off":
            qtile.cmd_spawn('bluetoothctl power on')
            qtile.cmd_spawn('notify-send "Bluetooth" "Bluetooth turned ON."')
        self.update(self.poll())

    def open_bluetoothctl(self):
        """Opens an interactive bluetoothctl session in the terminal."""
        qtile.cmd_spawn(f"{TERMINAL} -e bluetoothctl")


def toggle_gaps(qtile_instance):
    """Toggles window gaps on/off by modifying layout margins and reloading config."""
    global gaps_enabled
    gaps_enabled = not gaps_enabled
    new_margin = DEFAULT_GAP_SIZE if gaps_enabled else 0

    # Update margin for all layouts in the config
    for lyt in qtile_instance.config.layouts:
        if hasattr(lyt, 'margin'):
            lyt.margin = new_margin
            
    # Also update the floating layout margin
    if hasattr(qtile_instance.config.floating_layout, 'margin'):
        qtile_instance.config.floating_layout.margin = new_margin

    status_message = "Enabled" if gaps_enabled else "Disabled"
    qtile_instance.cmd_spawn(f'notify-send "Qtile Gaps" "Window gaps are now {status_message}."')
    logger.info(f"Toggling gaps. New state: {status_message}. Margin: {new_margin}")
    qtile_instance.reload_config()


# ==============================================================================
# === KEYBINDINGS ==============================================================
# ==============================================================================
keys = [
    # --- Window Navigation ---
    Key([MOD], "h", lazy.layout.left(), desc="Move focus to left window"),
    Key([MOD], "l", lazy.layout.right(), desc="Move focus to right window"),
    Key([MOD], "j", lazy.layout.down(), desc="Move focus down"),
    Key([MOD], "k", lazy.layout.up(), desc="Move focus up"),
    Key([MOD], "space", lazy.layout.next(), desc="Move window focus to next window in stack"),

    # --- Window Manipulation (Moving) ---
    Key([MOD, "shift"], "h", lazy.layout.shuffle_left(), desc="Move focused window left"),
    Key([MOD, "shift"], "l", lazy.layout.shuffle_right(), desc="Move focused window right"),
    Key([MOD, "shift"], "j", lazy.layout.shuffle_down(), desc="Move focused window down"),
    Key([MOD, "shift"], "k", lazy.layout.shuffle_up(), desc="Move focused window up"),

    # --- Window Manipulation (Resizing) ---
    Key([MOD, "control"], "h", lazy.layou t.grow_left(), desc="Grow focused window left"),
    Key([MOD, "control"], "l", lazy.layout.grow_right(), desc="Grow focused window right"),
    Key([MOD, "control"], "j", lazy.layout.grow_down(), desc="Grow focused window down"),
    Key([MOD, "control"], "k", lazy.layout.grow_up(), desc="Grow focused window up"),
    Key([MOD], "n", lazy.layout.normalize(), desc="Reset all window sizes to default"),

    # --- Layout Specific Commands ---
    Key([MOD, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle split/unsplit (Columns)"),

    # --- Application Launchers ---
    Key([MOD], "Return", lazy.spawn(TERMINAL), desc=f"Launch terminal ({TERMINAL})"),
    Key([MOD], "r", lazy.spawncmd(), desc="Spawn a command using Qtile's prompt"),
    Key([ALT], "space", lazy.spawn('bash -c "scrot -s - | xclip -selection clipboard -target image/png -i"'), desc="Take a screenshot with scrot"),

    # --- Window Management ---
    Key([MOD], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([MOD], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen"),
    Key([MOD], "t", lazy.window.toggle_floating(), desc="Toggle floating state"),

    # --- Qtile Management ---
    Key([MOD, "control"], "r", lazy.reload_config(), desc="Reload Qtile configuration"),
    Key([MOD, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([MOD, "control", "shift"], "z", lazy.function(toggle_gaps), desc="Toggle window gaps"),

    # --- Key Chords ---
    KeyChord([MOD], "tab", [
        Key([], "Tab", lazy.spawn("rofi -show drun"), lazy.ungrab_chord(), desc='Rofi: Show applications'),
        Key([], "w", lazy.spawn("rofi -show window"), lazy.ungrab_chord(), desc='Rofi: Show open windows'),
        Key([], "q", lazy.spawn("rofi -show run"), lazy.ungrab_chord(), desc='Rofi: Show run prompt'),
        Key([], "f", lazy.spawn("xfe"), lazy.ungrab_chord(), desc="Launch XFE file explorer"),
        Key([], "semicolon", lazy.spawn(TERMINAL), lazy.ungrab_chord(), desc=f"Launch {TERMINAL}"),
        Key([], "t", lazy.spawn("codium"), lazy.ungrab_chord(), desc="Launch Codium text editor"),
        Key([], "e", lazy.spawn("xdg-open /home/tori/code/stable/edtr3.html"), lazy.ungrab_chord(), desc="Open edtr3.html"),
    ], name="Rofi Launcher"),

    KeyChord([ALT], "j", [
        Key([], "k", lazy.spawn('brightnessctl set +20%'), desc='Increase brightness 20%'),
        Key([], "j", lazy.spawn('brightnessctl set 20%-'), desc='Decrease brightness 20%'),
    ], name="Brightness Control", mode=True),

    KeyChord([ALT], "u", [
        Key([], "i", lazy.spawn('amixer -D pulse sset Master 10%+'), desc='Increase volume 10%'),
        Key([], "u", lazy.spawn('amixer -D pulse sset Master 10%-'), desc='Decrease volume 10%'),
    ], name="Volume Control", mode=True),
    
    KeyChord([ALT], "b", [
        Key([], "o", lazy.spawn("bash -c 'if bluetoothctl show | grep -q \"Powered: yes\"; then bluetoothctl power off; else bluetoothctl power on; fi'"), desc="Toggle Bluetooth power"),
        Key([], "s", lazy.spawn(f"{TERMINAL} -e bluetoothctl scan on"), desc="Scan for devices"),
        Key([], "p", lazy.spawn(f"{TERMINAL} -e bluetoothctl pair"), desc="Pair with a device"),
        Key([], "c", lazy.spawn(f"{TERMINAL} -e bluetoothctl connect"), desc="Connect to a device"),
        Key([], "d", lazy.spawn(f"{TERMINAL} -e bluetoothctl disconnect"), desc="Disconnect from a device"),
        Key([], "l", lazy.spawn(f"{TERMINAL} -e bluetoothctl devices"), desc="List paired devices"),
    ], name="Bluetooth Control"),
]

# --- Virtual Terminal (VT) Switching (for Wayland) ---
for vt_num in range(1, 8):
    keys.append(
        Key(["control", ALT], f"f{vt_num}",
            lazy.core.change_vt(vt_num).when(func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to VT {vt_num}"
        )
    )

# ==============================================================================
# === GROUPS (WORKSPACES) ======================================================
# ==============================================================================
groups = [Group(i) for i in "123456789"]

for i in groups:
    keys.extend([
        # MOD + group number = switch to group
        Key([MOD], i.name, lazy.group[i.name].toscreen(),
            desc=f"Switch to group {i.name}"),
        # MOD + shift + group number = move focused window to group & follow
        Key([MOD, "shift"], i.name, lazy.window.togroup(i.name, switch_group=True),
            desc=f"Move focused window to group {i.name} & follow")
    ])

# ==============================================================================
# === LAYOUTS ==================================================================
# ==============================================================================
layout_theme = {
    "border_width": 4,
    "margin": DEFAULT_GAP_SIZE if gaps_enabled else 0,
    "border_focus": colors["border_active"],
    "border_normal": colors["border_inactive"],
}

layouts = [
    layout.Columns(**layout_theme),
    layout.Max(**layout_theme),
    layout.Tile(**layout_theme),
]

# ==============================================================================
# === WIDGETS & BAR ============================================================
# ==============================================================================
widget_defaults = dict(
    font=FONT_PRIMARY,
    fontsize=12,
    padding=3,
    background=colors["black"],
)
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        bottom=bar.Bar([
            widget.GroupBox(
                desc="Displays group (workspace) numbers",
                highlight_method='block',
                this_current_screen_border=colors["red"],
                active=colors["red"],
                inactive=colors["white"],
                hide_unused=False,
                disable_drag=True,
                use_mouse_wheel=False,
                padding_x=5,
                borderwidth=2,
            ),
            widget.Prompt(
                desc="Input prompt for lazy.spawncmd()",
                width=10,
                prompt="> "
            ),
            widget.WindowName(desc="Displays the name of the focused window"),
            widget.Chord(
                chords_colors={
                    "Rofi Launcher":      (colors["launch_chord_fg"], colors["launch_chord_bg"]),
                    "Brightness Control": (colors["brightness_chord_fg"], colors["brightness_chord_bg"]),
                    "Volume Control":     (colors["volume_chord_fg"], colors["volume_chord_bg"]),
                    "Bluetooth Control":  (colors["bluetooth_chord_fg"], colors["bluetooth_chord_bg"]),
                },
                name_transform=lambda name: name.upper(),
                desc="Displays active key chord name"
            ),
            widget.TextBox(
                "[g]",
                mouse_callbacks={'Button1': lazy.spawn('xdg-open https://gemini.google.com/app')},
                foreground=colors["white"],
                desc="Clickable link for Gemini"
            ),
            widget.TextBox(
                "[f]",
                mouse_callbacks={'Button1': lazy.spawn('thunar'), 'Button3': lazy.spawn('veracrypt')},
                foreground=colors["white"],
                desc="Clickable links for Thunar and Veracrypt"
            ),
            widget.TextBox(
                "[w]",
                mouse_callbacks={'Button1': lazy.spawn(f'{TERMINAL} -e nm-tui')},
                foreground=colors["white"],
                desc="Click to open Wi-Fi TUI (nm-tui)"
            ),
            BluetoothCtlWidget(
                foreground=colors["red"],
                desc="Bluetooth control widget"
            ),
            widget.Battery(
                format='{char} {percent:2.0%}',
                update_interval=60,
                low_foreground=colors["alert"],
                low_percentage=0.25,
                charge_char='⚡',
                discharge_char='🔋',
                desc="Displays battery status"
            ),
            widget.Systray(desc="System tray for notification icons"),
            widget.Clock(
                format="%m-%d-%y %a %I:%M:%S %p",
                foreground=colors["red"],
                desc="Displays date and time"
            ),
        ],
            24,  # Bar height
            background=colors["black"],
        ),
    ),
]

# ==============================================================================
# === MOUSE & FLOATING WINDOWS =================================================
# ==============================================================================
mouse = [
    Drag([MOD], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([MOD], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([MOD], "Button2", lazy.window.bring_to_front())
]

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
    **layout_theme
)

# ==============================================================================
# === GENERAL SETTINGS & HOOKS =================================================
# ==============================================================================
dgroups_key_binder = None
dgroups_app_rules = []
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True
auto_minimize = True
wl_input_rules = None
wmname = "LG3D"  # For Java app compatibility

@hook.subscribe.startup_once
def autostart():
    """Runs the autostart script if it exists."""
    autostart_script = os.path.expanduser('~/.config/qtile/autostart.sh')
    if os.path.exists(autostart_script):
        logger.info(f"Running autostart script: {autostart_script}")
        subprocess.run([autostart_script], check=False)
    else:
        logger.warning(f"Autostart script not found: {autostart_script}")

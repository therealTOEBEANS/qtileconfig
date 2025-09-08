# +===========================================================================+
# |==================================----=====================================|
# |===| TOEBEANS' LAPTOP QTILE CONFIG v3 (multimonitor enhancements)       |==|
# |==================================----=====================================|
# |===|   (c) Thor Smith 2025                                              |==|
# |==================================----=====================================|
# |===|     ver. 1.2.0                                                     |==|
# |==================================----=====================================|
# +===========================================================================+


import logging
import os
import shutil
import subprocess

from libqtile import bar, hook, layout, qtile, widget
from libqtile.config import Click, Drag, Group, Key, KeyChord, Match, Screen
from libqtile.lazy import lazy
from libqtile.widget import base

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MOD = "mod4"   # Super/Windows key
ALT = "mod1"   # Alt key
TERMINAL = "kitty"
FONT_PRIMARY = "monospace"
DEFAULT_GAP_SIZE = 5

# colors (config1-style dict)
colors = {
    "red": "#FF0000",
    "white": "#FFFFFF",
    "black": "#000000",
    "orange": "#FFA500",
    "light_blue": "#ADD8E6",
    "border_active":   "#FF0000",
    "border_inactive": "#FFFFFF",
    "alert":           "#FF0000",
    "launch_chord_fg":     "#FF0000",
    "launch_chord_bg":     "#FFFFFF",
    "brightness_chord_fg": "#FFA500",
    "brightness_chord_bg": "#000000",
    "volume_chord_fg":     "#ADD8E6",
    "volume_chord_bg":     "#000000",
    "bluetooth_chord_fg":  "#FF0000",
    "bluetooth_chord_bg":  "#FFFFFF",
}

logger = logging.getLogger(__name__)
logger.critical("QTILE CONFIG v3 (multimonitor): start")

# dynamic gaps flag
gaps_enabled = True

# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------
class BluetoothCtlWidget(base.ThreadPoolText):
    def __init__(self, **config):
        base.ThreadPoolText.__init__(self, "", **config)
        self.update_interval = 5
        self.add_callbacks({'Button1': self.toggle_power, 'Button3': self.open_bluetoothctl})

    def _get_power_status(self):
        try:
            output = subprocess.check_output(['bluetoothctl', 'show'], text=True)
            return "On" if 'Powered: yes' in output else "Off"
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "N/A"

    def poll(self):
        return f"BT: {self._get_power_status()}"

    def toggle_power(self):
        status = self._get_power_status()
        if status == "On":
            qtile.cmd_spawn('bluetoothctl power off')
            qtile.cmd_spawn('notify-send "Bluetooth" "Bluetooth turned OFF."')
        elif status == "Off":
            qtile.cmd_spawn('bluetoothctl power on')
            qtile.cmd_spawn('notify-send "Bluetooth" "Bluetooth turned ON."')
        self.update(self.poll())

    def open_bluetoothctl(self):
        qtile.cmd_spawn(f"{TERMINAL} -e bluetoothctl")

# A custom widget to show the status of the internal keyboard and toggle it.
class InternalKeyboardToggle(base.ThreadPoolText):
    def __init__(self, **config):
        base.ThreadPoolText.__init__(self, "[?]", **config)
        self.update_interval = 2
        self.keyboard_name = "AT Translated Set 2 keyboard"
        self.toggle_script_path = "/home/tori/.local/bin/keyblock.sh"
        self.add_callbacks({'Button1': self.toggle_keyboard})

    def poll(self):
        try:
            # Check the "Device Enabled" property using xinput
            props = subprocess.check_output(['xinput', 'list-props', self.keyboard_name], text=True)
            for line in props.split('\n'):
                if "Device Enabled" in line:
                    # The state is the last field on the line (0 or 1)
                    state = line.split()[-1]
                    return "[on.]" if state == '1' else "[off]"
            return "[err]"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Return error state if xinput fails or keyboard not found
            return "[N/A]"

    def toggle_keyboard(self):
        qtile.cmd_spawn(self.toggle_script_path)
        # Immediately update the text after running the script for instant feedback
        self.update(self.poll())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def toggle_gaps(qtile_instance):
    global gaps_enabled
    gaps_enabled = not gaps_enabled
    new_margin = DEFAULT_GAP_SIZE if gaps_enabled else 0

    for lyt in qtile_instance.config.layouts:
        if hasattr(lyt, 'margin'):
            lyt.margin = new_margin
    if hasattr(qtile_instance.config.floating_layout, 'margin'):
        qtile_instance.config.floating_layout.margin = new_margin

    status_message = "Enabled" if gaps_enabled else "Disabled"
    qtile_instance.cmd_spawn(f'notify-send "Qtile Gaps" "Window gaps are now {status_message}."')
    logger.info(f"gaps -> {status_message} (margin={new_margin})")
    qtile_instance.reload_config()

# Choose group on a specific screen (without stealing focus from primary)
# screen_index: 0 = laptop(primary), 1 = external

def choose_group_on_screen(qtile_instance, group_name: str, screen_index: int):
    try:
        current = qtile_instance.current_screen.index
        # jump to target screen, show the group there, then jump back
        qtile_instance.cmd_to_screen(screen_index)
        qtile_instance.groups_map[group_name].cmd_toscreen()
        qtile_instance.cmd_to_screen(current)
    except Exception as e:
        logger.error(f"choose_group_on_screen error: {e}")

# Convenience wrappers for digits 1..9 -> external screen index 1

def mk_external_group_key(num: int):
    name = str(num)
    def _fn(q):
        choose_group_on_screen(q, name, 1)
    return _fn

# Try to let the system apply layouts on hotplug, then tell qtile to re-read screens

def _maybe_autorandr():
    try:
        if shutil.which('autorandr'):
            subprocess.run(['autorandr', '--change'], check=False)
        else:
            # Fallback: best effort xrandr --auto
            subprocess.run(['xrandr', '--auto'], check=False)
    except Exception as e:
        logger.warning(f"autorandr/xrandr failed: {e}")

# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------
keys = [
    # Focus
    Key([MOD], "h", lazy.layout.left(), desc="Focus left"),
    Key([MOD], "l", lazy.layout.right(), desc="Focus right"),
    Key([MOD], "j", lazy.layout.down(), desc="Focus down"),
    Key([MOD], "k", lazy.layout.up(), desc="Focus up"),
    Key([MOD], "space", lazy.layout.next(), desc="Focus next"),

    # Move
    Key([MOD, "shift"], "h", lazy.layout.shuffle_left(), desc="Move left"),
    Key([MOD, "shift"], "l", lazy.layout.shuffle_right(), desc="Move right"),
    Key([MOD, "shift"], "j", lazy.layout.shuffle_down(), desc="Move down"),
    Key([MOD, "shift"], "k", lazy.layout.shuffle_up(), desc="Move up"),

    # Resize (fixed)
    Key([MOD, "control"], "h", lazy.layout.grow_left(), desc="Grow left"),
    Key([MOD, "control"], "l", lazy.layout.grow_right(), desc="Grow right"),
    Key([MOD, "control"], "j", lazy.layout.grow_down(), desc="Grow down"),
    Key([MOD, "control"], "k", lazy.layout.grow_up(), desc="Grow up"),
    Key([MOD], "n", lazy.layout.normalize(), desc="Normalize"),

    # Layout
    Key([MOD, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle split"),

    # Launchers
    Key([MOD], "Return", lazy.spawn(TERMINAL), desc=f"Terminal ({TERMINAL})"),
    Key([MOD], "r", lazy.spawncmd(), desc="Spawn command"),

    # Screenshots (both aliases)
    Key([ALT], "space", lazy.spawn('bash -c "scrot -s - | xclip -selection clipboard -target image/png -i"'), desc="Screenshot (scrot)"),
    Key([ALT, "shift"], "space", lazy.spawn('scrotum'), desc="Screenshot (scrotum)"),

    # Window mgmt
    Key([MOD], "w", lazy.window.kill(), desc="Kill"),
    Key([MOD], "f", lazy.window.toggle_fullscreen(), desc="Fullscreen"),
    Key([MOD], "t", lazy.window.toggle_floating(), desc="Toggle floating"),

    # Qtile mgmt
    Key([MOD, "control"], "r", lazy.reload_config(), desc="Reload"),
    Key([MOD, "control"], "q", lazy.shutdown(), desc="Quit"),
    Key([MOD, "control", "shift"], "z", lazy.function(toggle_gaps), desc="Toggle gaps"),

    # Rofi chord
    KeyChord([MOD], "tab", [
        Key([], "Tab", lazy.spawn("rofi -show drun"), lazy.ungrab_chord(), desc='Apps'),
        Key([], "w", lazy.spawn("rofi -show window"), lazy.ungrab_chord(), desc='Windows'),
        Key([], "q", lazy.spawn("rofi -show run"), lazy.ungrab_chord(), desc='Run'),
        Key([], "f", lazy.spawn("xfe"), lazy.ungrab_chord(), desc="XFE"),
        Key([], "semicolon", lazy.spawn(TERMINAL), lazy.ungrab_chord(), desc=f"{TERMINAL}"),
        Key([], "t", lazy.spawn("codium"), lazy.ungrab_chord(), desc="Codium"),
        Key([], "e", lazy.spawn("xdg-open /home/tori/code/stable/edtr3.html"), lazy.ungrab_chord(), desc="edtr3"),
    ], name="Rofi Launcher"),

    # Brightness
    KeyChord([ALT], "j", [
        Key([], "k", lazy.spawn('brightnessctl set +20%'), desc='Brightness +20%'),
        Key([], "j", lazy.spawn('brightnessctl set 20%-'), desc='Brightness -20%'),
    ], name="Brightness Control", mode=True),

    # Volume
    KeyChord([ALT], "u", [
        Key([], "i", lazy.spawn('amixer -D pulse sset Master 10%+'), desc='Volume +10%'),
        Key([], "u", lazy.spawn('amixer -D pulse sset Master 10%-'), desc='Volume -10%'),
    ], name="Volume Control", mode=True),

    # Bluetooth (richer)
    KeyChord([ALT], "b", [
        Key([], "s", lazy.spawn(f"{TERMINAL} -e bluetoothctl scan on"), desc="Scan on"),
        Key([], "S", lazy.spawn("bluetoothctl scan off"), desc="Scan off"),
        Key([], "p", lazy.spawn(f"{TERMINAL} -e bluetoothctl pair"), desc="Pair"),
        Key([], "c", lazy.spawn(f"{TERMINAL} -e bluetoothctl connect"), desc="Connect"),
        Key([], "d", lazy.spawn(f"{TERMINAL} -e bluetoothctl disconnect"), desc="Disconnect"),
        Key([], "l", lazy.spawn(f"{TERMINAL} -e bluetoothctl devices"), desc="Devices"),
        Key([], "t", lazy.spawn(f"{TERMINAL} -e bluetoothctl trust"), desc="Trust"),
        Key([], "f", lazy.spawn(f"{TERMINAL} -e bluetoothctl forget"), desc="Forget"),
        Key([], "o", lazy.spawn("bash -c 'if bluetoothctl show | grep -q \"Powered: yes\"; then bluetoothctl power off; else bluetoothctl power on; fi'"), desc="Power toggle"),
    ], name="Bluetooth Control"),
]

# Wayland VT switching
for vt_num in range(1, 8):
    keys.append(
        Key(["control", ALT], f"f{vt_num}",
            lazy.core.change_vt(vt_num).when(func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to VT {vt_num}")
    )

# Bind MOD+ALT+1..9 to set group on external display (screen index 1)
for i in range(1, 10):
    keys.append(Key([MOD, ALT], str(i), lazy.function(mk_external_group_key(i)), desc=f"Show group {i} on external screen"))

# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------
groups = [Group(i) for i in "123456789"]

for i in groups:
    keys.extend([
        Key([MOD], i.name, lazy.group[i.name].toscreen(), desc=f"Switch to group {i.name}"),
        Key([MOD, "shift"], i.name, lazy.window.togroup(i.name, switch_group=True), desc=f"Move window to {i.name} & follow"),
    ])

# ---------------------------------------------------------------------------
# Layouts
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Screens: define two. Primary (index 0) has the bar. Secondary (index 1) no bar.
# Qtile will use only as many as are connected; extra definitions are ignored.
# On hotplug, we trigger reconfigure_screens so the second screen attaches.
# ---------------------------------------------------------------------------
widget_defaults = dict(font=FONT_PRIMARY, fontsize=12, padding=3, background=colors["black"]) 
extension_defaults = widget_defaults.copy()

_primary_bar = bar.Bar([
    widget.GroupBox(
        desc="Groups",
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
    widget.Prompt(desc="spawncmd", width=10, prompt="> "),
    widget.WindowName(desc="Focused window"),
    widget.Chord(
        chords_colors={
            "Rofi Launcher":      (colors["launch_chord_fg"], colors["launch_chord_bg"]),
            "Brightness Control": (colors["brightness_chord_fg"], colors["brightness_chord_bg"]),
            "Volume Control":     (colors["volume_chord_fg"], colors["volume_chord_bg"]),
            "Bluetooth Control":  (colors["bluetooth_chord_fg"], colors["bluetooth_chord_bg"]),
        },
        name_transform=lambda name: name.upper(),
        desc="Chord name"
    ),
    # This widget shows the on/off state of the internal keyboard
    InternalKeyboardToggle(foreground=colors["red"], desc="Toggle internal keyboard"),
    widget.TextBox("[g]", mouse_callbacks={'Button1': lazy.spawn('xdg-open https://gemini.google.com/app')}, foreground=colors["white"], desc="Gemini"),
    widget.TextBox("[f]", mouse_callbacks={'Button1': lazy.spawn('thunar'), 'Button3': lazy.spawn('veracrypt')}, foreground=colors["white"], desc="Files/VeraCrypt"),
    widget.TextBox("[w]", mouse_callbacks={'Button1': lazy.spawn(f'{TERMINAL} -e nm-tui')}, foreground=colors["white"], desc="Wi-Fi TUI"),
    BluetoothCtlWidget(foreground=colors["red"], desc="Bluetooth"),
    widget.Battery(format='{percent:2.0%}', update_interval=60, low_foreground=colors["alert"], low_percentage=0.25, charge_char='⚡', discharge_char='🔋', desc="Battery"),
    widget.Systray(desc="Tray"),
    widget.Clock(format="%m-%d-%y %a %I:%M:%S %p", foreground=colors["red"], desc="Clock"),
], 24, background=colors["black"]) 

screens = [
    Screen(bottom=_primary_bar),  # Screen 0: laptop (primary) with bar
    Screen(),                     # Screen 1: external, no bar
]

# ---------------------------------------------------------------------------
# Floating + Mouse
# ---------------------------------------------------------------------------
mouse = [
    Drag([MOD], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([MOD], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([MOD], "Button2", lazy.window.bring_to_front()),
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
    **layout_theme,
)

# ---------------------------------------------------------------------------
# General settings
# ---------------------------------------------------------------------------
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

# Wayland placeholders
wl_input_rules = None

wmname = "LG3D"

# ---------------------------------------------------------------------------
# Hooks: autostart + react to RANDR/Wayland screen changes
# ---------------------------------------------------------------------------
@hook.subscribe.startup_once
def autostart():
    # Try to apply a stored layout first (if autorandr exists), then run user's autostart
    _maybe_autorandr()
    home = os.path.expanduser('~/.config/qtile/autostart.sh')
    if os.path.exists(home):
        logger.info(f"Running autostart: {home}")
        subprocess.run([home], check=False)
    else:
        logger.warning(f"Autostart script not found: {home}")

# On X11, this fires when RANDR changes (plug/unplug). On Wayland, qtile also tracks outputs.
@hook.subscribe.screen_change
def on_screen_change(event):
    logger.info("screen_change detected -> autorandr --change; reconfigure screens")
    _maybe_autorandr()
    qtile.cmd_reconfigure_screens()

# Also listen for screens_reconfigured to log the new state
@hook.subscribe.screens_reconfigured
def on_screens_reconfigured():
    try:
        count = qtile.core.num_screens
        logger.info(f"screens_reconfigured: now {count} screen(s)")
    except Exception:
        pass

import json
import os
import random
import re
import tkinter as tk
from collections import defaultdict
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk


class RouletteBoardApp:
    RED_NUMBERS = {
        1,
        3,
        5,
        7,
        9,
        12,
        14,
        16,
        18,
        19,
        21,
        23,
        25,
        27,
        30,
        32,
        34,
        36,
    }

    CHIP_DENOMS = [1, 5, 25, 100, 500, 1000]
    CHIP_COLORS = {
        1: ("#f3f4f6", "#d1d5db", "#111827", "#b91c1c"),
        5: ("#ef4444", "#b91c1c", "#ffffff", "#fee2e2"),
        25: ("#16a34a", "#166534", "#ffffff", "#dcfce7"),
        100: ("#111827", "#374151", "#f9fafb", "#9ca3af"),
        500: ("#7c3aed", "#5b21b6", "#ffffff", "#ddd6fe"),
        1000: ("#f59e0b", "#b45309", "#111827", "#fde68a"),
    }
    STRATEGY_MODES = ("standard", "recovery", "progression", "repeat")
    RULE_OPERATORS = (">=", ">", "<=", "<", "==", "!=")
    BASE_METRICS = (
        "win_streak",
        "loss_streak",
        "spin_count",
        "bankroll",
        "session_profit",
        "drawdown",
        "last_spin_net",
    )
    TARGET_METRICS = ("hit_streak", "miss_streak", "spins_since_hit", "hits_total", "miss_total")
    RULE_ACTIONS = ("set_bet_amount", "clear_all_bets", "switch_mode", "set_chip_denom")
    WHEEL_FAMILIES = ("American", "European")
    AMERICAN_BET_OPTIONS = ("Double Zero (0/00)", "Triple Zero (0/00/000)")
    EUROPEAN_BET_OPTIONS = ("European Standard", "French (En Prison)", "French (La Partage)")
    WHEEL_TYPE_OPTIONS = (
        "American - Double Zero (0/00)",
        "American - Triple Zero (0/00/000)",
        "European - Standard",
        "French - En Prison",
        "French - La Partage",
    )
    EVEN_MONEY_OUTSIDE_IDS = (
        "outside_1_18",
        "outside_even",
        "outside_red",
        "outside_black",
        "outside_odd",
        "outside_19_36",
    )
    FRENCH_FINALES_PLEINES_NAME = "Finales Pleines (Same Final Digit)"
    FRENCH_FINALES_A_CHEVAL_NAME = "Finales a Cheval (Split Final Digit)"
    FRENCH_FINALES_DIGITS = tuple(str(d) for d in range(10))
    FRENCH_CALL_BET_OPTIONS = (
        "Voisins du Zero",
        "Tiers du Cylindre",
        "Orphelins",
        "Jeu Zero",
        FRENCH_FINALES_PLEINES_NAME,
        FRENCH_FINALES_A_CHEVAL_NAME,
    )
    FRENCH_CALL_BETS = {
        "Voisins du Zero": [
            {"kind": "trio", "numbers": (0, 2, 3), "units": 2},
            {"kind": "split", "numbers": (4, 7), "units": 1},
            {"kind": "split", "numbers": (12, 15), "units": 1},
            {"kind": "split", "numbers": (18, 21), "units": 1},
            {"kind": "split", "numbers": (19, 22), "units": 1},
            {"kind": "split", "numbers": (25, 26), "units": 1},
            {"kind": "split", "numbers": (32, 35), "units": 1},
        ],
        "Tiers du Cylindre": [
            {"kind": "split", "numbers": (5, 8), "units": 1},
            {"kind": "split", "numbers": (10, 11), "units": 1},
            {"kind": "split", "numbers": (13, 16), "units": 1},
            {"kind": "split", "numbers": (23, 24), "units": 1},
            {"kind": "split", "numbers": (27, 30), "units": 1},
            {"kind": "split", "numbers": (33, 36), "units": 1},
        ],
        "Jeu Zero": [
            {"kind": "split", "numbers": (0, 3), "units": 1},
            {"kind": "split", "numbers": (12, 15), "units": 1},
            {"kind": "straight", "numbers": (26,), "units": 1},
            {"kind": "split", "numbers": (32, 35), "units": 1},
        ],
        "Orphelins": [
            {"kind": "straight", "numbers": (1,), "units": 1},
            {"kind": "split", "numbers": (6, 9), "units": 1},
            {"kind": "split", "numbers": (14, 17), "units": 1},
            {"kind": "split", "numbers": (17, 20), "units": 1},
            {"kind": "split", "numbers": (31, 34), "units": 1},
        ],
        FRENCH_FINALES_PLEINES_NAME: [],
        FRENCH_FINALES_A_CHEVAL_NAME: [],
    }
    STAGE_NAMES = ("Beginning", "Recovery")
    STAGE_TRIGGER_TYPES = ("Win", "Loss", "Bet Type", "Bankroll", "Count", "Exact Bet")
    STAGE_TRIGGER_BASES = ("Current Spin", "Count Based")
    STAGE_TRIGGER_ACTIONS = (
        "No Action",
        "Set Bet Type",
        "Set Bet Amount",
        "Set Bet Type + Amount",
        "Clear Bets",
        "Switch Stage",
    )
    STAGE_TRIGGER_ACTION_SCOPES = ("This Trigger", "Group")
    SETTINGS_VERSION = 1
    SETTINGS_FILE = "board_settings.json"
    SETTINGS_DEFAULT_FILE = "board_settings.default.json"
    SETTINGS_SCHEMA_FILE = "board_settings.schema.json"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Las Vegas Roulette Board")
        self.board_settings = {}
        self.board_settings_path = ""
        self.board_settings_default_path = ""
        self.board_settings_schema_path = ""
        self.settings_status_var = None
        self.settings_theme_board_var = None
        self.settings_theme_surround_var = None
        self.settings_popup_enabled_var = None
        self.settings_popup_mode_var = None
        self.settings_popup_delay_var = None
        self._init_board_settings()
        self.root.configure(bg=self._surround_color())

        self.selected_chip = tk.IntVar(value=1)
        self.spots = {}
        self.bets = defaultdict(list)
        self.stack_tags = {}
        self.legend_canvases = {}

        self.tooltip = tk.Label(
            self.root,
            bg=self._popup_background_color(),
            fg=self._popup_text_color(),
            bd=1,
            relief="solid",
            padx=8,
            pady=4,
            font=("Segoe UI", 10, "bold"),
            highlightthickness=1,
            highlightbackground=self._popup_border_color(),
        )
        self.tooltip.place_forget()
        self.chip_add_popup_after_id = None
        self.hover_popup_until_motion = False
        self.hover_popup_origin = None
        self.chip_hover_fallback_spot_id = None
        self.hover_popup_after_id = None
        self.hover_popup_pending_spot_id = None

        self.total_var = tk.StringVar(value="Total Bets: $0")
        self.map_pad = 8
        self.mini_cell_w = 53
        self.mini_cell_h = 42
        self.mini_zero_w = 56
        self.max_rules_per_spin = 3
        self._init_strategy_state()
        self.active_screen = "board"

        self._build_navigation()
        self._build_screen_host()
        self._build_board_screen()
        self._build_system_creator_screen()
        self._build_testing_screen()
        self._build_settings_screen()
        self._show_screen("board")
        self._apply_board_settings_runtime(rebuild_board=False)

        self._align_spin_map_right()
        self._refresh_payout_chart()
        self._refresh_legend_highlight()
        self._refresh_trigger_metric_choices()
        self._refresh_action_targets()
        self._refresh_session_status()

    def _init_strategy_state(self):
        self.current_mode = tk.StringVar(value=self.STRATEGY_MODES[0])
        self.set_mode_var = tk.StringVar(value=self.current_mode.get())
        self.start_bankroll_var = tk.StringVar(value="10000")
        self.spin_input_var = tk.StringVar(value="")
        self.session_status_var = tk.StringVar(value="")
        self.monitor_target_var = tk.StringVar(value="")
        self.trigger_mode_var = tk.StringVar(value="any")
        self.trigger_metric_var = tk.StringVar(value=self.BASE_METRICS[0])
        self.trigger_metric_target_var = tk.StringVar(value="")
        self.trigger_operator_var = tk.StringVar(value=self.RULE_OPERATORS[0])
        self.trigger_value_var = tk.StringVar(value="1")
        self.trigger_priority_var = tk.StringVar(value="50")
        self.action_type_var = tk.StringVar(value=self.RULE_ACTIONS[0])
        self.action_target_var = tk.StringVar(value="")
        self.action_value_var = tk.StringVar(value="1")
        self.action_next_mode_var = tk.StringVar(value="")
        self.wheel_family_var = tk.StringVar(value=self.WHEEL_FAMILIES[0])
        self.american_bet_option_var = tk.StringVar(value=self.AMERICAN_BET_OPTIONS[0])
        self.european_bet_option_var = tk.StringVar(value=self.EUROPEAN_BET_OPTIONS[0])
        self.wheel_type_var = tk.StringVar(value=self.WHEEL_TYPE_OPTIONS[0])
        self.stage_var = tk.StringVar(value=self.STAGE_NAMES[0])
        self.stage_profit_increment_var = tk.StringVar(value="")
        self.stage_trigger_basis_var = tk.StringVar(value=self.STAGE_TRIGGER_BASES[0])
        self.stage_trigger_type_var = tk.StringVar(value=self.STAGE_TRIGGER_TYPES[0])
        self.stage_trigger_target_var = tk.StringVar(value="")
        self.stage_trigger_amount_var = tk.StringVar(value="")
        self.stage_trigger_count_threshold_var = tk.StringVar(value="2")
        self.stage_trigger_action_var = tk.StringVar(value=self.STAGE_TRIGGER_ACTIONS[0])
        self.stage_trigger_action_target_var = tk.StringVar(value="")
        self.stage_trigger_action_amount_var = tk.StringVar(value="")
        self.stage_trigger_action_scope_var = tk.StringVar(value=self.STAGE_TRIGGER_ACTION_SCOPES[0])
        self.stage_trigger_group_id_var = tk.StringVar(value="")

        self.rules = []
        self.next_rule_id = 1
        self.stage_triggers = []
        self.next_stage_trigger_id = 1
        self.next_profit_stage_target = None
        self.stage_trigger_hit_counts = defaultdict(int)
        self.stage_group_action_cache = {}
        self.stage_active_bet_target = ""
        self.monitored_targets = []
        self.target_stats = defaultdict(
            lambda: {
                "hit_streak": 0,
                "miss_streak": 0,
                "spins_since_hit": 0,
                "hits_total": 0,
                "miss_total": 0,
            }
        )

        self.rules_listbox = None
        self.monitor_listbox = None
        self.log_listbox = None
        self.trigger_metric_combo = None
        self.trigger_metric_target_combo = None
        self.monitor_target_combo = None
        self.action_type_combo = None
        self.action_target_combo = None
        self.action_value_entry = None
        self.mode_combo = None
        self.monitor_target_display_to_id = {}
        self.monitor_target_id_to_display = {}
        self.stage_listbox = None
        self.stage_trigger_listbox = None
        self.stage_trigger_target_combo = None
        self.stage_trigger_action_target_combo = None
        self.wheel_family_combo = None
        self.american_bet_option_combo = None
        self.european_bet_option_combo = None
        self.wheel_type_combo = None
        self.wheel_call_button_row = None
        self.call_bets_button = None
        self.call_bets_display_host = None
        self.call_bets_display_inner = None
        self.call_bets_display_row = None
        self.call_bets_spacer = None
        self.call_bets_reserved_h = 0
        self.call_bets_left_panel = None
        self.call_bets_right_panel = None
        self.call_bets_listbox_left = None
        self.call_bets_listbox_right = None
        self.call_bet_popup = None
        self.call_bet_name_combo = None
        self.call_bet_name_var = None
        self.call_bet_amount_var = None
        self.call_bet_final_digit_var = None
        self.call_bet_final_digit_controls = []
        self.call_bet_entry_ids_left = []
        self.call_bet_entry_ids_right = []
        self.stage_trigger_target_display_to_id = {}
        self.stage_trigger_target_id_to_display = {}
        self.stage_action_target_display_to_value = {}
        self.stage_action_target_value_to_display = {}
        self.last_spin = None
        self.last_spin_net = 0
        self.en_prison_pending = set()
        self.spin_count = 0
        self.win_streak = 0
        self.loss_streak = 0
        self.bankroll = 0
        self.peak_bankroll = 0
        self.en_prison_pending = set()
        self.call_bet_entries = []
        self.next_call_bet_id = 1
        self.bet_chip_sources = defaultdict(list)
        self.spot_hover_display_names = {}
        self.marker_spot_ids = set()
        self.marker_hover_radius = 14
        self.marker_popup_spot_id = None
        self._reset_session_counters(from_init=True)

    def _default_board_settings(self):
        return {
            "version": self.SETTINGS_VERSION,
            "theme": {
                "board_felt_color": "#0f7a36",
                "surround_color": "#ffffff",
            },
            "hover_popup": {
                "enabled": True,
                "mode": "detailed",
                "delay_ms": 0,
                "style": {
                    "background_color": "#111827",
                    "text_color": "#f9fafb",
                    "border_color": "#111111",
                },
            },
        }

    def _init_board_settings(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.board_settings_path = os.path.join(base_dir, self.SETTINGS_FILE)
        self.board_settings_default_path = os.path.join(base_dir, self.SETTINGS_DEFAULT_FILE)
        self.board_settings_schema_path = os.path.join(base_dir, self.SETTINGS_SCHEMA_FILE)

        base_settings = self._default_board_settings()
        file_defaults = self._load_json_object(self.board_settings_default_path)
        if file_defaults:
            base_settings = self._deep_merge_dict(base_settings, file_defaults)

        user_settings = self._load_json_object(self.board_settings_path)
        merged = self._deep_merge_dict(base_settings, user_settings or {})
        merged = self._migrate_board_settings(merged)
        self.board_settings = self._normalize_board_settings(merged)

    @staticmethod
    def _load_json_object(path):
        if not path or not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _migrate_board_settings(self, payload):
        if not isinstance(payload, dict):
            return self._default_board_settings()
        version = self._safe_int(payload.get("version"), 0)
        if version <= 0:
            payload["version"] = self.SETTINGS_VERSION
            return payload
        if version < self.SETTINGS_VERSION:
            payload["version"] = self.SETTINGS_VERSION
        return payload

    def _normalize_board_settings(self, payload):
        defaults = self._default_board_settings()
        merged = self._deep_merge_dict(defaults, payload if isinstance(payload, dict) else {})
        theme = merged.get("theme", {})
        if not isinstance(theme, dict):
            theme = {}
        hover_popup = merged.get("hover_popup", {})
        if not isinstance(hover_popup, dict):
            hover_popup = {}
        hover_style = hover_popup.get("style", {})
        if not isinstance(hover_style, dict):
            hover_style = {}

        normalized = {
            "version": self.SETTINGS_VERSION,
            "theme": {
                "board_felt_color": self._normalize_hex_color(
                    theme.get("board_felt_color"),
                    defaults["theme"]["board_felt_color"],
                ),
                "surround_color": self._normalize_hex_color(
                    theme.get("surround_color"),
                    defaults["theme"]["surround_color"],
                ),
            },
            "hover_popup": {
                "enabled": bool(hover_popup.get("enabled", defaults["hover_popup"]["enabled"])),
                "mode": str(hover_popup.get("mode", defaults["hover_popup"]["mode"])).strip().lower(),
                "delay_ms": self._safe_int(
                    hover_popup.get("delay_ms", defaults["hover_popup"]["delay_ms"]),
                    defaults["hover_popup"]["delay_ms"],
                ),
                "style": {
                    "background_color": self._normalize_hex_color(
                        hover_style.get("background_color"),
                        defaults["hover_popup"]["style"]["background_color"],
                    ),
                    "text_color": self._normalize_hex_color(
                        hover_style.get("text_color"),
                        defaults["hover_popup"]["style"]["text_color"],
                    ),
                    "border_color": self._normalize_hex_color(
                        hover_style.get("border_color"),
                        defaults["hover_popup"]["style"]["border_color"],
                    ),
                },
            },
        }

        if normalized["hover_popup"]["mode"] not in {"compact", "detailed"}:
            normalized["hover_popup"]["mode"] = defaults["hover_popup"]["mode"]
        normalized["hover_popup"]["delay_ms"] = max(0, min(3000, normalized["hover_popup"]["delay_ms"]))
        return normalized

    @staticmethod
    def _deep_merge_dict(base, override):
        result = {}
        base = base if isinstance(base, dict) else {}
        override = override if isinstance(override, dict) else {}
        for key, value in base.items():
            if isinstance(value, dict):
                result[key] = RouletteBoardApp._deep_merge_dict(value, override.get(key))
            else:
                result[key] = value
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = RouletteBoardApp._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _normalize_hex_color(value, fallback):
        text = str(value).strip() if value is not None else ""
        if re.fullmatch(r"#[0-9A-Fa-f]{6}", text):
            return text.lower()
        return fallback

    def _sync_settings_controls_from_state(self):
        if self.settings_theme_board_var is not None:
            self.settings_theme_board_var.set(self._board_felt_color())
        if self.settings_theme_surround_var is not None:
            self.settings_theme_surround_var.set(self._surround_color())
        if self.settings_popup_enabled_var is not None:
            self.settings_popup_enabled_var.set(self._popup_enabled())
        if self.settings_popup_mode_var is not None:
            self.settings_popup_mode_var.set(self._popup_mode())
        if self.settings_popup_delay_var is not None:
            self.settings_popup_delay_var.set(str(self._popup_delay_ms()))

    def _apply_settings_from_controls(self):
        if self.settings_theme_board_var is None:
            return

        next_payload = self._deep_merge_dict(
            self.board_settings,
            {
                "version": self.SETTINGS_VERSION,
                "theme": {
                    "board_felt_color": self.settings_theme_board_var.get().strip(),
                    "surround_color": self.settings_theme_surround_var.get().strip(),
                },
                "hover_popup": {
                    "enabled": bool(self.settings_popup_enabled_var.get()),
                    "mode": self.settings_popup_mode_var.get().strip().lower(),
                    "delay_ms": self._safe_int(self.settings_popup_delay_var.get(), 0),
                },
            },
        )
        self.board_settings = self._normalize_board_settings(next_payload)
        self._sync_settings_controls_from_state()
        self._apply_board_settings_runtime(rebuild_board=True)
        if self.settings_status_var is not None:
            self.settings_status_var.set(
                f"Applied settings in memory. Click Save to persist to {self.board_settings_path}"
            )

    def _save_board_settings_to_disk(self):
        self._apply_settings_from_controls()
        try:
            with open(self.board_settings_path, "w", encoding="utf-8") as f:
                json.dump(self.board_settings, f, indent=2)
            if self.settings_status_var is not None:
                self.settings_status_var.set(f"Saved settings to {self.board_settings_path}")
            self._append_log(f"Saved board settings: {self.board_settings_path}")
        except OSError as exc:
            messagebox.showerror("Settings Save Failed", str(exc))

    def _apply_board_settings_runtime(self, rebuild_board=True):
        surround_color = self._surround_color()
        self.root.configure(bg=surround_color)
        if hasattr(self, "screen_host") and self.screen_host is not None:
            self.screen_host.configure(bg=surround_color)
        if hasattr(self, "canvas") and self.canvas is not None:
            self.canvas.configure(bg=surround_color)
        if hasattr(self, "tooltip") and self.tooltip is not None:
            self.tooltip.configure(
                bg=self._popup_background_color(),
                fg=self._popup_text_color(),
                highlightbackground=self._popup_border_color(),
            )
        if rebuild_board and hasattr(self, "canvas") and self.canvas is not None:
            self._rebuild_board_for_wheel()
        self._sync_settings_controls_from_state()

    def _board_felt_color(self):
        return self.board_settings.get("theme", {}).get("board_felt_color", "#0f7a36")

    def _surround_color(self):
        return self.board_settings.get("theme", {}).get("surround_color", "#ffffff")

    def _popup_enabled(self):
        return bool(self.board_settings.get("hover_popup", {}).get("enabled", True))

    def _popup_mode(self):
        mode = str(self.board_settings.get("hover_popup", {}).get("mode", "detailed")).strip().lower()
        return mode if mode in {"compact", "detailed"} else "detailed"

    def _popup_delay_ms(self):
        delay = self._safe_int(self.board_settings.get("hover_popup", {}).get("delay_ms", 0), 0)
        return max(0, min(3000, delay))

    def _popup_background_color(self):
        return self.board_settings.get("hover_popup", {}).get("style", {}).get("background_color", "#111827")

    def _popup_text_color(self):
        return self.board_settings.get("hover_popup", {}).get("style", {}).get("text_color", "#f9fafb")

    def _popup_border_color(self):
        return self.board_settings.get("hover_popup", {}).get("style", {}).get("border_color", "#111111")

    def _build_navigation(self):
        nav = tk.Frame(self.root, bg="#e5e7eb")
        nav.pack(fill="x", padx=12, pady=(8, 6))
        self.nav_frame = nav
        self.nav_buttons = {}

        nav_specs = (
            ("board", "Board"),
            ("system", "System Creator"),
            ("testing", "Testing / Evaluation"),
            ("settings", "Settings"),
        )
        for screen_key, label in nav_specs:
            btn = tk.Button(
                nav,
                text=label,
                command=lambda key=screen_key: self._show_screen(key),
                font=("Segoe UI", 10, "bold"),
                padx=12,
                pady=6,
                bd=1,
                relief="raised",
            )
            btn.pack(side="left", padx=(0, 6))
            self.nav_buttons[screen_key] = btn

    def _build_screen_host(self):
        self.screen_host = tk.Frame(self.root, bg="#FFFFFF")
        self.screen_host.pack(fill="both", expand=True)
        self.screens = {
            "board": tk.Frame(self.screen_host, bg="#FFFFFF"),
            "system": tk.Frame(self.screen_host, bg="#FFFFFF"),
            "testing": tk.Frame(self.screen_host, bg="#FFFFFF"),
            "settings": tk.Frame(self.screen_host, bg="#FFFFFF"),
        }

    def _build_board_screen(self):
        board_screen = self.screens["board"]
        self.board_content = tk.Frame(board_screen, bg="#FFFFFF")
        self.board_content.pack(fill="both", expand=True)

        self._build_top_panel(self.board_content)
        self._build_board_canvas(self.board_content)
        self._build_layout()

    def _build_system_creator_screen(self):
        system_screen = self.screens["system"]

        heading = tk.Label(
            system_screen,
            text="System Creator",
            bg="#FFFFFF",
            fg="#111827",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        heading.pack(fill="x", padx=12, pady=(10, 6))

        self._build_system_panel(system_screen)

    def _build_testing_screen(self):
        testing_screen = self.screens["testing"]

        heading = tk.Label(
            testing_screen,
            text="Testing / Evaluation",
            bg="#FFFFFF",
            fg="#111827",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        heading.pack(fill="x", padx=12, pady=(10, 6))

        content = tk.Frame(testing_screen, bg="#FFFFFF")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._build_modes_section(content)

        notes = tk.LabelFrame(
            content,
            text="Evaluation Notes",
            bg="#FFFFFF",
            fg="#111827",
            padx=10,
            pady=10,
            font=("Segoe UI", 10, "bold"),
        )
        notes.pack(side="left", fill="both", expand=True)
        tk.Label(
            notes,
            text=(
                "Use this screen to apply spins, run random tests, and review session logs.\n"
                "System definition stays isolated in the System Creator screen."
            ),
            bg="#FFFFFF",
            fg="#334155",
            justify="left",
            anchor="nw",
            font=("Segoe UI", 10),
        ).pack(fill="x")

    def _build_settings_screen(self):
        settings_screen = self.screens["settings"]

        heading = tk.Label(
            settings_screen,
            text="Settings",
            bg="#FFFFFF",
            fg="#111827",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        heading.pack(fill="x", padx=12, pady=(10, 6))

        content = tk.Frame(settings_screen, bg="#FFFFFF")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        appearance = tk.LabelFrame(
            content,
            text="Board Appearance",
            bg="#FFFFFF",
            fg="#111827",
            padx=10,
            pady=10,
            font=("Segoe UI", 10, "bold"),
        )
        appearance.pack(fill="x", anchor="nw")

        self.settings_theme_board_var = tk.StringVar(value=self._board_felt_color())
        self.settings_theme_surround_var = tk.StringVar(value=self._surround_color())

        row1 = tk.Frame(appearance, bg="#FFFFFF")
        row1.pack(anchor="w", pady=(0, 6))
        tk.Label(row1, text="Board felt color (#RRGGBB)", bg="#FFFFFF", fg="#111827", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(row1, textvariable=self.settings_theme_board_var, width=12).pack(side="left", padx=(8, 0))

        row2 = tk.Frame(appearance, bg="#FFFFFF")
        row2.pack(anchor="w")
        tk.Label(row2, text="Surround color (#RRGGBB)", bg="#FFFFFF", fg="#111827", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(row2, textvariable=self.settings_theme_surround_var, width=12).pack(side="left", padx=(18, 0))

        popup = tk.LabelFrame(
            content,
            text="Hover Popup",
            bg="#FFFFFF",
            fg="#111827",
            padx=10,
            pady=10,
            font=("Segoe UI", 10, "bold"),
        )
        popup.pack(fill="x", anchor="nw", pady=(10, 0))

        self.settings_popup_enabled_var = tk.BooleanVar(value=self._popup_enabled())
        self.settings_popup_mode_var = tk.StringVar(value=self._popup_mode())
        self.settings_popup_delay_var = tk.StringVar(value=str(self._popup_delay_ms()))

        row3 = tk.Frame(popup, bg="#FFFFFF")
        row3.pack(anchor="w")
        tk.Checkbutton(
            row3,
            text="Enable hover popups",
            variable=self.settings_popup_enabled_var,
            bg="#FFFFFF",
            fg="#111827",
            activebackground="#FFFFFF",
            activeforeground="#111827",
            selectcolor="#FFFFFF",
            font=("Segoe UI", 9),
        ).pack(side="left")

        row4 = tk.Frame(popup, bg="#FFFFFF")
        row4.pack(anchor="w", pady=(8, 0))
        tk.Label(row4, text="Popup mode", bg="#FFFFFF", fg="#111827", font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(
            row4,
            textvariable=self.settings_popup_mode_var,
            values=("compact", "detailed"),
            width=10,
            state="readonly",
        ).pack(side="left", padx=(8, 18))
        tk.Label(row4, text="Delay (ms)", bg="#FFFFFF", fg="#111827", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(row4, textvariable=self.settings_popup_delay_var, width=8).pack(side="left", padx=(8, 0))

        actions = tk.Frame(content, bg="#FFFFFF")
        actions.pack(fill="x", pady=(12, 0))
        tk.Button(
            actions,
            text="Apply",
            command=self._apply_settings_from_controls,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="raised",
            bd=2,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=5,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Save",
            command=self._save_board_settings_to_disk,
            bg="#0f766e",
            fg="#ffffff",
            activebackground="#115e59",
            activeforeground="#ffffff",
            relief="raised",
            bd=2,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=5,
        ).pack(side="left", padx=(8, 0))

        self.settings_status_var = tk.StringVar(value=f"Settings file: {self.board_settings_path}")
        tk.Label(
            content,
            textvariable=self.settings_status_var,
            bg="#FFFFFF",
            fg="#334155",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(10, 0))

    def _show_screen(self, screen_key):
        self.active_screen = screen_key
        for key, frame in self.screens.items():
            if key == screen_key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        for key, btn in self.nav_buttons.items():
            if key == screen_key:
                btn.configure(bg="#1d4ed8", fg="#ffffff", activebackground="#1e40af", activeforeground="#ffffff")
            else:
                btn.configure(bg="#f8fafc", fg="#111827", activebackground="#e2e8f0", activeforeground="#111827")

        # No-op: board screen no longer uses a vertical scrollbar.

    def _build_system_panel(self, parent):
        system_panel = tk.Frame(parent, bg="#FFFFFF")
        system_panel.pack(fill="x", padx=12, pady=(0, 8))
        self.system_panel = system_panel

        self._build_stage_section(system_panel)
        self._build_stage_triggers_section(system_panel)
        self._refresh_stage_list()
        self._refresh_stage_trigger_target_choices()
        self._refresh_stage_trigger_list()

    def _build_stage_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="1) Stages",
            bg="#FFFFFF",
            fg="#111827",
            padx=10,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        )
        frame.pack(side="left", fill="y", padx=(0, 8))

        tk.Label(
            frame,
            text="Stage flow order:",
            bg="#FFFFFF",
            fg="#111827",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        self.stage_listbox = tk.Listbox(frame, width=42, height=4, exportselection=False)
        self.stage_listbox.pack(fill="x", pady=(4, 6))

        goal_row = tk.Frame(frame, bg="#FFFFFF")
        goal_row.pack(anchor="w")
        tk.Label(goal_row, text="Profit goal step", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(goal_row, textvariable=self.stage_profit_increment_var, width=8).pack(side="left", padx=(6, 4))
        tk.Label(goal_row, text="(optional)", bg="#FFFFFF", fg="#475569", font=("Segoe UI", 9)).pack(side="left")

        tk.Button(
            frame,
            text="Apply Stage Goal",
            command=self._apply_stage_goal_settings,
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        ).pack(anchor="w", pady=(6, 0))

    def _build_stage_triggers_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="2) Trigger Sequence",
            bg="#FFFFFF",
            fg="#111827",
            padx=10,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        )
        frame.pack(side="left", fill="both", expand=True)

        row1 = tk.Frame(frame, bg="#FFFFFF")
        row1.pack(anchor="w")
        tk.Label(row1, text="Basis", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(
            row1,
            textvariable=self.stage_trigger_basis_var,
            values=self.STAGE_TRIGGER_BASES,
            width=12,
            state="readonly",
        ).pack(side="left", padx=(6, 10))
        tk.Label(row1, text="Trigger type", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(
            row1,
            textvariable=self.stage_trigger_type_var,
            values=self.STAGE_TRIGGER_TYPES,
            width=14,
            state="readonly",
        ).pack(side="left", padx=(6, 0))

        row2 = tk.Frame(frame, bg="#FFFFFF")
        row2.pack(anchor="w", pady=(6, 0))
        tk.Label(row2, text="Condition target", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        self.stage_trigger_target_combo = ttk.Combobox(
            row2,
            textvariable=self.stage_trigger_target_var,
            width=42,
            state="readonly",
        )
        self.stage_trigger_target_combo.pack(side="left", padx=(6, 0))

        row3 = tk.Frame(frame, bg="#FFFFFF")
        row3.pack(anchor="w", pady=(6, 0))
        tk.Label(row3, text="Condition amount", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(row3, textvariable=self.stage_trigger_amount_var, width=10).pack(side="left", padx=(6, 0))
        tk.Label(row3, text="Count threshold", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left", padx=(14, 0))
        tk.Entry(row3, textvariable=self.stage_trigger_count_threshold_var, width=8).pack(side="left", padx=(6, 0))

        row4 = tk.Frame(frame, bg="#FFFFFF")
        row4.pack(anchor="w", pady=(6, 0))
        tk.Label(row4, text="Result action", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        action_combo = ttk.Combobox(
            row4,
            textvariable=self.stage_trigger_action_var,
            values=self.STAGE_TRIGGER_ACTIONS,
            width=18,
            state="readonly",
        )
        action_combo.pack(side="left", padx=(6, 8))
        action_combo.bind("<<ComboboxSelected>>", self._on_stage_action_changed)
        tk.Label(row4, text="Action target", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        self.stage_trigger_action_target_combo = ttk.Combobox(
            row4,
            textvariable=self.stage_trigger_action_target_var,
            width=36,
            state="readonly",
        )
        self.stage_trigger_action_target_combo.pack(side="left", padx=(6, 0))

        row5 = tk.Frame(frame, bg="#FFFFFF")
        row5.pack(anchor="w", pady=(6, 0))
        tk.Label(row5, text="Action amount", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(row5, textvariable=self.stage_trigger_action_amount_var, width=10).pack(side="left", padx=(6, 8))
        tk.Label(row5, text="Scope", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(
            row5,
            textvariable=self.stage_trigger_action_scope_var,
            values=self.STAGE_TRIGGER_ACTION_SCOPES,
            width=12,
            state="readonly",
        ).pack(side="left", padx=(6, 8))
        tk.Label(row5, text="Group ID", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(row5, textvariable=self.stage_trigger_group_id_var, width=12).pack(side="left", padx=(6, 0))

        btn_row = tk.Frame(frame, bg="#FFFFFF")
        btn_row.pack(anchor="w", pady=(8, 6))
        tk.Button(
            btn_row,
            text="Add Trigger",
            command=self._add_stage_trigger,
            bg="#0ea5e9",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        ).pack(side="left", padx=(0, 6))
        tk.Button(
            btn_row,
            text="Remove Trigger",
            command=self._remove_selected_stage_trigger,
            bg="#475569",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        ).pack(side="left")

        self.stage_trigger_listbox = tk.Listbox(frame, height=9, width=96, exportselection=False)
        self.stage_trigger_listbox.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text=(
                "Order matters. First matching trigger moves stage to Recovery.\n"
                "Attach result actions to each trigger, or set Scope=Group for grouped behavior."
            ),
            bg="#FFFFFF",
            fg="#475569",
            justify="left",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(6, 0))

    def _apply_stage_goal_settings(self):
        raw_step = self.stage_profit_increment_var.get().strip()
        if raw_step:
            step = self._safe_int(raw_step, None)
            if step is None or step <= 0:
                messagebox.showerror("Invalid stage goal", "Profit goal step must be a positive integer or blank.")
                return
        self._reset_stage_progress()
        self._append_log("Stage goal settings applied.")

    def _refresh_stage_list(self):
        if self.stage_listbox is None:
            return
        self.stage_listbox.delete(0, tk.END)
        raw_step = self.stage_profit_increment_var.get().strip()
        step = self._safe_int(raw_step, 0) if raw_step else 0
        if step > 0:
            next_target = (
                f"${self.next_profit_stage_target:,}"
                if isinstance(self.next_profit_stage_target, int) and self.next_profit_stage_target > 0
                else "pending"
            )
            beginning_text = f"Beginning - reset on +${step:,} stage steps (next target {next_target})"
        else:
            beginning_text = "Beginning - reset on New Session Profit"
        self.stage_listbox.insert(tk.END, beginning_text)
        self.stage_listbox.insert(tk.END, "Recovery - entered after first matching trigger")
        self.stage_listbox.insert(tk.END, f"Current stage: {self.stage_var.get()}")

    def _refresh_stage_trigger_target_choices(self):
        options = self._build_metric_target_display_options()
        self.stage_trigger_target_display_to_id = {display: target for display, target in options}
        self.stage_trigger_target_id_to_display = {target: display for display, target in options}
        values = [display for display, _target in options]
        if self.stage_trigger_target_combo is not None:
            self.stage_trigger_target_combo.configure(values=values)
            selected_target = self._resolve_stage_trigger_target(self.stage_trigger_target_var.get())
            if selected_target and selected_target in self.stage_trigger_target_id_to_display:
                self.stage_trigger_target_var.set(self.stage_trigger_target_id_to_display[selected_target])
            else:
                self.stage_trigger_target_var.set("")
        self._refresh_stage_action_target_choices()

    def _resolve_stage_trigger_target(self, raw_value):
        text = str(raw_value).strip()
        if not text:
            return ""
        if text in self.spots:
            return text
        return self.stage_trigger_target_display_to_id.get(text, "")

    def _refresh_stage_action_target_choices(self):
        if self.stage_trigger_action_target_combo is None:
            return

        action = self.stage_trigger_action_var.get().strip()
        target_values = []
        mapping = {}

        if action in ("Set Bet Type", "Set Bet Amount", "Set Bet Type + Amount"):
            for target_id, display in self.stage_trigger_target_id_to_display.items():
                target_values.append(display)
                mapping[display] = target_id
        elif action == "Switch Stage":
            for stage in self.STAGE_NAMES:
                target_values.append(stage)
                mapping[stage] = stage

        self.stage_action_target_display_to_value = mapping
        self.stage_action_target_value_to_display = {value: display for display, value in mapping.items()}
        self.stage_trigger_action_target_combo.configure(values=target_values)

        current_value = self._resolve_stage_action_target(self.stage_trigger_action_target_var.get())
        if current_value and current_value in self.stage_action_target_value_to_display:
            self.stage_trigger_action_target_var.set(self.stage_action_target_value_to_display[current_value])
        else:
            self.stage_trigger_action_target_var.set("")

    def _resolve_stage_action_target(self, raw_value):
        text = str(raw_value).strip()
        if not text:
            return ""
        if text in self.spots or text in self.STAGE_NAMES:
            return text
        return self.stage_action_target_display_to_value.get(text, "")

    def _on_stage_action_changed(self, _event=None):
        self._refresh_stage_action_target_choices()

    def _add_stage_trigger(self):
        basis = self.stage_trigger_basis_var.get().strip()
        if basis not in self.STAGE_TRIGGER_BASES:
            messagebox.showerror("Invalid basis", "Choose a valid trigger basis.")
            return

        trigger_type = self.stage_trigger_type_var.get().strip()
        if trigger_type not in self.STAGE_TRIGGER_TYPES:
            messagebox.showerror("Invalid trigger", "Choose a valid trigger type.")
            return

        target = self._resolve_stage_trigger_target(self.stage_trigger_target_var.get())
        if trigger_type in ("Bet Type", "Exact Bet") and not target:
            messagebox.showerror("Missing bet target", "Bet Type and Exact Bet triggers require a target.")
            return
        if trigger_type not in ("Bet Type", "Exact Bet"):
            target = ""

        count_threshold = 1
        if basis == "Count Based":
            count_threshold = self._safe_int(self.stage_trigger_count_threshold_var.get(), None)
            if count_threshold is None or count_threshold <= 0:
                messagebox.showerror("Invalid threshold", "Count threshold must be a positive integer.")
                return

        amount_text = self.stage_trigger_amount_var.get().strip()
        amount = None
        if amount_text:
            amount = self._safe_int(amount_text, None)
            if amount is None or amount < 0:
                messagebox.showerror("Invalid amount", "Optional amount must be a non-negative integer.")
                return

        action = self.stage_trigger_action_var.get().strip()
        if action not in self.STAGE_TRIGGER_ACTIONS:
            messagebox.showerror("Invalid action", "Choose a valid trigger result action.")
            return

        action_scope = self.stage_trigger_action_scope_var.get().strip()
        if action_scope not in self.STAGE_TRIGGER_ACTION_SCOPES:
            messagebox.showerror("Invalid scope", "Action scope must be This Trigger or Group.")
            return

        group_id = self.stage_trigger_group_id_var.get().strip()
        if action_scope == "Group" and not group_id:
            messagebox.showerror("Missing group", "Group scope requires a Group ID.")
            return

        action_target = self._resolve_stage_action_target(self.stage_trigger_action_target_var.get())
        action_amount_text = self.stage_trigger_action_amount_var.get().strip()
        action_amount = None
        if action_amount_text:
            action_amount = self._safe_int(action_amount_text, None)
            if action_amount is None or action_amount < 0:
                messagebox.showerror("Invalid action amount", "Action amount must be a non-negative integer.")
                return

        if action in ("Set Bet Type", "Set Bet Amount", "Set Bet Type + Amount"):
            if action_target not in self.spots:
                messagebox.showerror("Invalid action target", "Set Bet actions require a valid bet target.")
                return
            if action in ("Set Bet Amount", "Set Bet Type + Amount") and action_amount is None:
                messagebox.showerror("Missing action amount", "Set Bet Amount actions require an amount.")
                return
        elif action == "Switch Stage":
            if action_target not in self.STAGE_NAMES:
                messagebox.showerror("Invalid action target", "Switch Stage requires Beginning or Recovery.")
                return
        else:
            action_target = ""
            action_amount = None

        trigger = {
            "id": self.next_stage_trigger_id,
            "basis": basis,
            "count_threshold": count_threshold,
            "type": trigger_type,
            "target": target,
            "amount": amount,
            "action": action,
            "action_target": action_target,
            "action_amount": action_amount,
            "action_scope": action_scope,
            "group_id": group_id,
        }
        self.next_stage_trigger_id += 1
        self.stage_triggers.append(trigger)
        self.stage_trigger_hit_counts[trigger["id"]] = 0
        self._refresh_stage_trigger_list()
        self._append_log(f"Added stage trigger T{trigger['id']}: {self._format_stage_trigger(trigger)}")

    def _remove_selected_stage_trigger(self):
        if self.stage_trigger_listbox is None:
            return
        selected = self.stage_trigger_listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        if idx < 0 or idx >= len(self.stage_triggers):
            return
        removed = self.stage_triggers.pop(idx)
        self.stage_trigger_hit_counts.pop(removed["id"], None)
        self.stage_group_action_cache.pop(removed.get("group_id", ""), None)
        self._refresh_stage_trigger_list()
        self._append_log(f"Removed stage trigger T{removed['id']}")

    def _refresh_stage_trigger_list(self):
        if self.stage_trigger_listbox is None:
            return
        self.stage_trigger_listbox.delete(0, tk.END)
        for idx, trigger in enumerate(self.stage_triggers, start=1):
            text = self._format_stage_trigger(trigger)
            if trigger.get("basis") == "Count Based":
                count_value = self.stage_trigger_hit_counts.get(trigger["id"], 0)
                text = f"{text} [count {count_value}]"
            self.stage_trigger_listbox.insert(tk.END, f"{idx}. {text}")

    def _format_stage_trigger(self, trigger):
        basis = trigger.get("basis", self.STAGE_TRIGGER_BASES[0])
        trigger_type = trigger["type"]
        target = trigger.get("target", "")
        amount = trigger.get("amount")
        action = trigger.get("action", "No Action")
        action_target = trigger.get("action_target", "")
        action_amount = trigger.get("action_amount")
        action_scope = trigger.get("action_scope", "This Trigger")
        group_id = trigger.get("group_id", "")

        condition_parts = [f"{basis}", trigger_type]
        if basis == "Count Based":
            condition_parts.append(f"x{trigger.get('count_threshold', 1)}")
        if target:
            condition_parts.append(self.stage_trigger_target_id_to_display.get(target, target))
        if amount is not None:
            condition_parts.append(f"${amount:,}")

        action_parts = [action]
        if action_target:
            action_display = self.stage_trigger_target_id_to_display.get(
                action_target,
                self.stage_action_target_value_to_display.get(action_target, action_target),
            )
            action_parts.append(action_display)
        if action_amount is not None:
            action_parts.append(f"${action_amount:,}")
        action_text = " ".join(action_parts)

        scope_text = action_scope if action_scope != "Group" else f"Group({group_id})"
        return f"{' | '.join(condition_parts)} => {action_text} [{scope_text}]"

    def _set_stage(self, stage, reason=""):
        if stage not in self.STAGE_NAMES:
            return
        changed = self.stage_var.get() != stage
        self.stage_var.set(stage)
        self._refresh_stage_list()
        if changed and reason:
            self._append_log(f"Stage -> {stage} ({reason})")

    def _reset_stage_progress(self):
        self.stage_var.set(self.STAGE_NAMES[0])
        raw_step = self.stage_profit_increment_var.get().strip()
        step = self._safe_int(raw_step, 0) if raw_step else 0
        start = self.bankroll if self.bankroll > 0 else self._safe_int(self.start_bankroll_var.get(), 10000)
        if step > 0:
            self.next_profit_stage_target = start + step
        else:
            self.next_profit_stage_target = None
        self.stage_trigger_hit_counts = defaultdict(int)
        self.stage_group_action_cache = {}
        self.stage_active_bet_target = ""
        self.hover_popup_until_motion = False
        self.hover_popup_origin = None
        self._refresh_stage_list()
        self._refresh_stage_trigger_list()

    def _evaluate_stage_triggers_for_spin(self):
        fired_trigger = None
        for trigger in self.stage_triggers:
            trigger_id = trigger["id"]
            matched = self._stage_trigger_matches(trigger)
            basis = trigger.get("basis", self.STAGE_TRIGGER_BASES[0])
            if basis == "Count Based":
                if matched:
                    self.stage_trigger_hit_counts[trigger_id] += 1
                else:
                    self.stage_trigger_hit_counts[trigger_id] = 0
                threshold = max(1, int(trigger.get("count_threshold", 1)))
                if self.stage_trigger_hit_counts[trigger_id] < threshold:
                    continue
                self.stage_trigger_hit_counts[trigger_id] = 0
            elif not matched:
                continue

            if matched or basis == "Count Based":
                fired_trigger = trigger
                self._set_stage("Recovery", reason=f"T{trigger['id']} matched")
                self._execute_stage_trigger_action(trigger)
                break

        start = self._safe_int(self.start_bankroll_var.get(), 0)
        raw_step = self.stage_profit_increment_var.get().strip()
        step = self._safe_int(raw_step, 0) if raw_step else 0
        if step > 0:
            if not isinstance(self.next_profit_stage_target, int):
                self.next_profit_stage_target = start + step
            if self.bankroll >= self.next_profit_stage_target:
                while self.bankroll >= self.next_profit_stage_target:
                    self.next_profit_stage_target += step
                self._set_stage("Beginning", reason="profit step reached")
        else:
            if self.bankroll > start:
                self._set_stage("Beginning", reason="session profit")

        self._refresh_stage_list()
        self._refresh_stage_trigger_list()
        return fired_trigger

    def _stage_trigger_matches(self, trigger):
        trigger_type = trigger["type"]
        amount = trigger.get("amount")
        target = trigger.get("target", "")

        if trigger_type == "Win":
            if self.last_spin_net <= 0:
                return False
            return amount is None or self.last_spin_net >= amount

        if trigger_type == "Loss":
            if self.last_spin_net >= 0:
                return False
            loss_amount = abs(self.last_spin_net)
            return amount is None or loss_amount >= amount

        if trigger_type == "Bet Type":
            if target not in self.spots:
                return False
            target_total = sum(self.bets[target])
            if target_total <= 0:
                return False
            return amount is None or target_total >= amount

        if trigger_type == "Bankroll":
            if amount is None:
                start = self._safe_int(self.start_bankroll_var.get(), 0)
                return self.bankroll <= start
            return self.bankroll <= amount

        if trigger_type == "Count":
            if amount is None:
                return self.spin_count > 0
            return self.spin_count >= amount

        if trigger_type == "Exact Bet":
            if target not in self.spots:
                return False
            target_total = sum(self.bets[target])
            if amount is None:
                return target_total > 0
            return target_total == amount

        return False

    def _execute_stage_trigger_action(self, trigger):
        action_trigger = trigger
        scope = trigger.get("action_scope", "This Trigger")
        group_id = str(trigger.get("group_id", "")).strip()
        if scope == "Group" and group_id:
            if group_id not in self.stage_group_action_cache:
                leader = trigger
                fallback = None
                for item in self.stage_triggers:
                    if str(item.get("group_id", "")).strip() == group_id:
                        if fallback is None:
                            fallback = item
                        if item.get("action", "No Action") != "No Action":
                            leader = item
                            break
                if leader is trigger and fallback is not None and leader.get("action", "No Action") == "No Action":
                    leader = fallback
                self.stage_group_action_cache[group_id] = leader
            action_trigger = self.stage_group_action_cache[group_id]

        action = action_trigger.get("action", "No Action")
        target = action_trigger.get("action_target", "")
        amount = action_trigger.get("action_amount")
        action_desc = action

        if action == "Set Bet Type":
            if target in self.spots:
                self.stage_active_bet_target = target
                action_desc = f"Set Bet Type -> {self.stage_trigger_target_id_to_display.get(target, target)}"
        elif action == "Set Bet Amount":
            if target in self.spots and amount is not None:
                self._set_spot_total(target, amount)
                action_desc = f"Set Bet Amount -> {self.stage_trigger_target_id_to_display.get(target, target)} ${amount:,}"
        elif action == "Set Bet Type + Amount":
            if target in self.spots and amount is not None:
                self.stage_active_bet_target = target
                self._set_spot_total(target, amount)
                action_desc = f"Set Bet Type+Amount -> {self.stage_trigger_target_id_to_display.get(target, target)} ${amount:,}"
        elif action == "Clear Bets":
            self._clear_bets()
            action_desc = "Clear Bets"
        elif action == "Switch Stage":
            if target in self.STAGE_NAMES:
                self._set_stage(target, reason=f"T{trigger['id']} action")
                action_desc = f"Switch Stage -> {target}"

        if action != "No Action":
            self._append_log(f"Trigger T{trigger['id']} action: {action_desc}")

    def _build_metrics_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="1) Metrics",
            bg="#FFFFFF",
            fg="#111827",
            padx=8,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        frame.pack(side="left", fill="y", padx=(0, 8))

        tk.Label(
            frame,
            text="Track hit/miss counters for:",
            bg="#FFFFFF",
            fg="#111827",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        self.monitor_target_combo = ttk.Combobox(
            frame,
            textvariable=self.monitor_target_var,
            width=44,
            state="readonly",
        )
        self.monitor_target_combo.pack(anchor="w", pady=(4, 4))

        btn_row = tk.Frame(frame, bg="#FFFFFF")
        btn_row.pack(anchor="w", pady=(0, 6))
        tk.Button(
            btn_row,
            text="Add",
            command=self._add_monitor_target,
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left", padx=(0, 6))
        tk.Button(
            btn_row,
            text="Remove",
            command=self._remove_selected_monitor,
            bg="#475569",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left")

        self.monitor_listbox = tk.Listbox(frame, width=48, height=8, exportselection=False)
        self.monitor_listbox.pack(fill="x")

    def _build_triggers_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="2) Triggers",
            bg="#FFFFFF",
            fg="#111827",
            padx=8,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        frame.pack(side="left", fill="y", padx=(0, 8))

        tk.Label(frame, text="Mode scope", bg="#FFFFFF", font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Combobox(
            frame,
            textvariable=self.trigger_mode_var,
            values=("any",) + self.STRATEGY_MODES,
            width=14,
            state="readonly",
        ).pack(anchor="w", pady=(2, 4))

        tk.Label(frame, text="Metric", bg="#FFFFFF", font=("Segoe UI", 9)).pack(anchor="w")
        self.trigger_metric_combo = ttk.Combobox(
            frame,
            textvariable=self.trigger_metric_var,
            width=20,
            state="readonly",
        )
        self.trigger_metric_combo.pack(anchor="w", pady=(2, 4))
        self.trigger_metric_combo.bind("<<ComboboxSelected>>", self._on_trigger_metric_changed)

        tk.Label(frame, text="Metric target (for hit/miss metrics)", bg="#FFFFFF", font=("Segoe UI", 9)).pack(anchor="w")
        self.trigger_metric_target_combo = ttk.Combobox(
            frame,
            textvariable=self.trigger_metric_target_var,
            width=20,
            state="normal",
        )
        self.trigger_metric_target_combo.pack(anchor="w", pady=(2, 4))

        row = tk.Frame(frame, bg="#FFFFFF")
        row.pack(anchor="w")
        tk.Label(row, text="Op", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(
            row,
            textvariable=self.trigger_operator_var,
            values=self.RULE_OPERATORS,
            width=5,
            state="readonly",
        ).pack(side="left", padx=(4, 8))
        tk.Label(row, text="Value", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(row, textvariable=self.trigger_value_var, width=8).pack(side="left", padx=(4, 0))

        pr_row = tk.Frame(frame, bg="#FFFFFF")
        pr_row.pack(anchor="w", pady=(4, 0))
        tk.Label(pr_row, text="Priority", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(pr_row, textvariable=self.trigger_priority_var, width=8).pack(side="left", padx=(4, 0))

    def _build_actions_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="3) Actions",
            bg="#FFFFFF",
            fg="#111827",
            padx=8,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        top_row = tk.Frame(frame, bg="#FFFFFF")
        top_row.pack(fill="x")

        tk.Label(top_row, text="Action", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        self.action_type_combo = ttk.Combobox(
            top_row,
            textvariable=self.action_type_var,
            values=self.RULE_ACTIONS,
            width=18,
            state="readonly",
        )
        self.action_type_combo.pack(side="left", padx=(4, 8))
        self.action_type_combo.bind("<<ComboboxSelected>>", self._on_action_changed)

        tk.Label(top_row, text="Target", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        self.action_target_combo = ttk.Combobox(
            top_row,
            textvariable=self.action_target_var,
            width=24,
            state="normal",
        )
        self.action_target_combo.pack(side="left", padx=(4, 8))

        tk.Label(top_row, text="Value", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        self.action_value_entry = tk.Entry(top_row, textvariable=self.action_value_var, width=8)
        self.action_value_entry.pack(side="left", padx=(4, 0))

        mode_row = tk.Frame(frame, bg="#FFFFFF")
        mode_row.pack(fill="x", pady=(6, 4))
        tk.Label(mode_row, text="Optional mode switch", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(
            mode_row,
            textvariable=self.action_next_mode_var,
            values=("",) + self.STRATEGY_MODES,
            width=16,
            state="readonly",
        ).pack(side="left", padx=(6, 0))

        btn_row = tk.Frame(frame, bg="#FFFFFF")
        btn_row.pack(fill="x", pady=(0, 6))
        tk.Button(
            btn_row,
            text="Add Rule",
            command=self._add_rule_from_builder,
            bg="#0ea5e9",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        ).pack(side="left", padx=(0, 6))
        tk.Button(
            btn_row,
            text="Delete Rule",
            command=self._remove_selected_rule,
            bg="#475569",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        ).pack(side="left")

        self.rules_listbox = tk.Listbox(frame, height=8, width=102, exportselection=False)
        self.rules_listbox.pack(fill="both", expand=True)

    def _build_modes_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="4) Modes / Session",
            bg="#FFFFFF",
            fg="#111827",
            padx=8,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        frame.pack(side="left", fill="both", padx=(0, 10))

        mode_row = tk.Frame(frame, bg="#FFFFFF")
        mode_row.pack(anchor="w")
        tk.Label(mode_row, text="Active mode", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        self.mode_combo = ttk.Combobox(
            mode_row,
            textvariable=self.set_mode_var,
            values=self.STRATEGY_MODES,
            width=12,
            state="readonly",
        )
        self.mode_combo.pack(side="left", padx=(4, 4))
        tk.Button(
            mode_row,
            text="Set",
            command=self._set_mode_from_ui,
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left")

        bank_row = tk.Frame(frame, bg="#FFFFFF")
        bank_row.pack(anchor="w", pady=(6, 0))
        tk.Label(bank_row, text="Start bankroll", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(bank_row, textvariable=self.start_bankroll_var, width=10).pack(side="left", padx=(6, 6))
        tk.Button(
            bank_row,
            text="Reset Session",
            command=self._reset_session_counters,
            bg="#0f766e",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left")

        spin_row = tk.Frame(frame, bg="#FFFFFF")
        spin_row.pack(anchor="w", pady=(6, 0))
        tk.Label(spin_row, text="Spin result", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(spin_row, textvariable=self.spin_input_var, width=6).pack(side="left", padx=(6, 4))
        tk.Button(
            spin_row,
            text="Apply",
            command=self._apply_spin_from_input,
            bg="#7c3aed",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            spin_row,
            text="Random",
            command=self._spin_random,
            bg="#6d28d9",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left")

        save_row = tk.Frame(frame, bg="#FFFFFF")
        save_row.pack(anchor="w", pady=(6, 0))
        tk.Button(
            save_row,
            text="Save JSON",
            command=self._save_strategy_json,
            bg="#1d4ed8",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left", padx=(0, 4))
        tk.Button(
            save_row,
            text="Load JSON",
            command=self._load_strategy_json,
            bg="#1d4ed8",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
        ).pack(side="left")

        tk.Label(
            frame,
            textvariable=self.session_status_var,
            bg="#FFFFFF",
            fg="#111827",
            justify="left",
            anchor="w",
            font=("Consolas", 9),
        ).pack(fill="x", pady=(6, 4))

        self.log_listbox = tk.Listbox(frame, width=50, height=6, exportselection=False)
        self.log_listbox.pack(fill="both", expand=True)

    def _common_strategy_targets(self):
        if not self.spots:
            return []
        preferred = [
            sid
            for sid in sorted(self.spots.keys())
            if sid.startswith(("column_", "dozen_", "outside_", "street_", "sixline_"))
        ]
        preferred_set = set(preferred)
        remainder = [sid for sid in sorted(self.spots.keys()) if sid not in preferred_set]
        return preferred + remainder

    def _display_members_text(self, spot_id):
        members = self._spot_numbers(spot_id)
        if not members:
            return ""

        positive_numbers = sorted([n for n in members if isinstance(n, int) and n > 0])
        tokens = []
        if "000" in members:
            tokens.append("000")
        if "00" in members:
            tokens.append("00")
        if 0 in members:
            tokens.append("0")
        tokens.extend([str(n) for n in positive_numbers])
        return " ".join(tokens)

    def _build_metric_target_display_options(self):
        if not self.spots:
            return []

        options = []
        used_display_names = set()

        def append_option(display_name, spot_id):
            clean_name = display_name
            if clean_name in used_display_names:
                clean_name = f"{display_name} [{spot_id}]"
            used_display_names.add(clean_name)
            options.append((clean_name, spot_id))

        all_spots = set(self.spots.keys())
        consumed = set()

        columns = sorted(
            [sid for sid in all_spots if sid.startswith("column_")],
            key=lambda sid: int(sid.split("_")[1]),
        )
        for idx, sid in enumerate(columns, start=1):
            append_option(f"Column.{idx}", sid)
        consumed.update(columns)

        dozens = sorted(
            [sid for sid in all_spots if sid.startswith("dozen_")],
            key=lambda sid: int(sid.split("_")[1]),
        )
        for idx, sid in enumerate(dozens, start=1):
            append_option(f"Dozen.{idx}", sid)
        consumed.update(dozens)

        outside_order = (
            ("outside_1_18", "Low (1-18)"),
            ("outside_19_36", "High (19-36)"),
            ("outside_even", "Even"),
            ("outside_odd", "Odd"),
            ("outside_red", "Red"),
            ("outside_black", "Black"),
        )
        for sid, label in outside_order:
            if sid in all_spots:
                append_option(label, sid)
                consumed.add(sid)

        sixlines = sorted(
            [sid for sid in all_spots if sid.startswith("sixline_")],
            key=lambda sid: tuple(int(v) for v in sid.split("_")[1:]),
        )
        for idx, sid in enumerate(sixlines, start=1):
            members = self._display_members_text(sid)
            append_option(f"Line.{idx} ({members})", sid)
        consumed.update(sixlines)

        streets = sorted(
            [sid for sid in all_spots if sid.startswith("street_")],
            key=lambda sid: int(sid.split("_")[1]),
        )
        for idx, sid in enumerate(streets, start=1):
            members = self._display_members_text(sid)
            append_option(f"Street.{idx} ({members})", sid)
        consumed.update(streets)

        baskets = sorted([sid for sid in all_spots if sid.startswith("basket_")])
        for idx, sid in enumerate(baskets, start=1):
            members = self._display_members_text(sid)
            if len(baskets) == 1:
                append_option(f"Basket ({members})", sid)
            else:
                append_option(f"Basket.{idx} ({members})", sid)
        consumed.update(baskets)

        corners = sorted(
            [sid for sid in all_spots if sid.startswith("corner_")],
            key=lambda sid: tuple(int(v) for v in sid.split("_")[1:]),
        )
        for idx, sid in enumerate(corners, start=1):
            members = self._display_members_text(sid)
            append_option(f"Corner.{idx} ({members})", sid)
        consumed.update(corners)

        trio_ids = [sid for sid in all_spots if sid.startswith("trio_")]
        if self._is_triple_zero_wheel():
            preferred_trios = [
                "trio_000_00_0",
                "trio_0_1_2",
                "trio_00_0_2",
                "trio_00_2_3",
            ]
            trio_rank = {sid: idx for idx, sid in enumerate(preferred_trios)}
            trios = sorted(
                trio_ids,
                key=lambda sid: (
                    trio_rank.get(sid, 999),
                    -float(self.spots.get(sid, {}).get("center", (0.0, 0.0))[1]),
                    float(self.spots.get(sid, {}).get("center", (0.0, 0.0))[0]),
                    self._display_members_text(sid),
                ),
            )
        else:
            trios = sorted(
                trio_ids,
                key=lambda sid: (
                    -float(self.spots.get(sid, {}).get("center", (0.0, 0.0))[1]),
                    float(self.spots.get(sid, {}).get("center", (0.0, 0.0))[0]),
                    self._display_members_text(sid),
                ),
            )
        for idx, sid in enumerate(trios, start=1):
            members = self._display_members_text(sid)
            append_option(f"Trio.{idx} ({members})", sid)
        consumed.update(trios)

        v_splits = sorted(
            [sid for sid in all_spots if sid.startswith("split_v_")],
            key=lambda sid: tuple(sorted([int(v) for v in sid.split("_")[2:]])),
        )
        for idx, sid in enumerate(v_splits, start=1):
            members = self._display_members_text(sid)
            append_option(f"VSplit.{idx} ({members})", sid)
        consumed.update(v_splits)

        zero_v_candidates = [sid for sid in all_spots if self._special_split_axis(sid) == "vertical"]
        if self._is_triple_zero_wheel():
            preferred_v = ["split_0_00"]
            v_rank = {sid: idx for idx, sid in enumerate(preferred_v)}
            zero_v_splits = sorted(zero_v_candidates, key=lambda sid: (v_rank.get(sid, 999), sid))
        else:
            zero_v_splits = sorted(
                zero_v_candidates,
                key=lambda sid: tuple(
                    sorted(
                        [
                            {"000": 0, "00": 1, "0": 2}.get(part, 99)
                            for part in sid.split("_")[1:]
                        ]
                    )
                ),
                reverse=True,
            )
        for idx, sid in enumerate(zero_v_splits, start=1):
            members = self._display_members_text(sid)
            append_option(f"VSplit.{self._alpha_index(idx)} ({members})", sid)
        consumed.update(zero_v_splits)

        h_splits = sorted(
            [sid for sid in all_spots if sid.startswith("split_h_")],
            key=lambda sid: tuple(sorted([int(v) for v in sid.split("_")[2:]])),
        )
        for idx, sid in enumerate(h_splits, start=1):
            members = self._display_members_text(sid)
            append_option(f"HSplit.{idx} ({members})", sid)
        consumed.update(h_splits)

        zero_h_candidates = [sid for sid in all_spots if self._special_split_axis(sid) == "horizontal"]
        if self._is_triple_zero_wheel():
            preferred_h = [
                "split_000_0",
                "split_000_00",
                "split_0_1",
                "split_0_2",
                "split_00_2",
                "split_00_3",
            ]
            h_rank = {sid: idx for idx, sid in enumerate(preferred_h)}
            zero_h_splits = sorted(zero_h_candidates, key=lambda sid: (h_rank.get(sid, 999), sid))
        else:
            zero_h_splits = sorted(
                zero_h_candidates,
                key=lambda sid: (
                    {"000": 0, "00": 1, "0": 2}.get(
                        sid.split("_")[1] if sid.split("_")[1] in {"000", "00", "0"} else sid.split("_")[2],
                        99,
                    ),
                    -int(sid.split("_")[2] if sid.split("_")[2].isdigit() else sid.split("_")[1]),
                ),
                reverse=True,
            )
        for idx, sid in enumerate(zero_h_splits, start=1):
            members = self._display_members_text(sid)
            append_option(f"HSplit.{self._alpha_index(idx)} ({members})", sid)
        consumed.update(zero_h_splits)

        special_splits = sorted(
            [
                sid
                for sid in all_spots
                if sid.startswith("split_") and not sid.startswith(("split_v_", "split_h_")) and sid not in consumed
            ],
            key=lambda sid: self._display_members_text(sid),
        )
        for idx, sid in enumerate(special_splits, start=1):
            members = self._display_members_text(sid)
            append_option(f"Split.{idx} ({members})", sid)
        consumed.update(special_splits)

        remaining = sorted(all_spots - consumed)
        for sid in remaining:
            label = self.spots[sid]["label"]
            append_option(label, sid)

        return options

    def _refresh_spot_hover_display_names(self):
        self.spot_hover_display_names = {}
        for display, spot_id in self._build_metric_target_display_options():
            short_name = display
            if " (" in short_name and not spot_id.startswith("outside_"):
                short_name = short_name.split(" (", 1)[0]
            if short_name.startswith("Column."):
                short_name = "Col." + short_name.split(".", 1)[1]
            if short_name.startswith("Dozen."):
                short_name = "Doz." + short_name.split(".", 1)[1]
            if spot_id.startswith("dozen_"):
                dozen_idx = spot_id.split("_")[1]
                short_name = f"Doz.{dozen_idx}"
            if spot_id.startswith("straight_"):
                short_name = spot_id.split("_", 1)[1]
            self.spot_hover_display_names[spot_id] = short_name

        for spot_id in self.spots:
            if spot_id not in self.spot_hover_display_names:
                if spot_id.startswith("straight_"):
                    self.spot_hover_display_names[spot_id] = spot_id.split("_", 1)[1]
                elif spot_id.startswith("dozen_"):
                    self.spot_hover_display_names[spot_id] = f"Doz.{spot_id.split('_')[1]}"
                else:
                    self.spot_hover_display_names[spot_id] = self.spots[spot_id]["label"]

    def _resolve_metric_display_target(self, raw_value):
        text = str(raw_value).strip()
        if not text:
            return ""
        if text in self.spots:
            return text
        return self.monitor_target_display_to_id.get(text, "")

    def _refresh_monitor_target_choices(self):
        options = self._build_metric_target_display_options()
        if self.monitor_target_combo is None:
            return
        self.monitor_target_display_to_id = {display: target for display, target in options}
        self.monitor_target_id_to_display = {target: display for display, target in options}
        display_values = [display for display, _target in options]
        self.monitor_target_combo.configure(values=display_values)

        selected_target = self._resolve_metric_display_target(self.monitor_target_var.get())
        if selected_target and selected_target in self.monitor_target_id_to_display:
            self.monitor_target_var.set(self.monitor_target_id_to_display[selected_target])
        else:
            self.monitor_target_var.set("")

    def _refresh_monitor_list(self):
        if self.monitor_listbox is None:
            return
        self.monitor_listbox.delete(0, tk.END)
        for target in self.monitored_targets:
            display_name = self.monitor_target_id_to_display.get(target, target)
            self.monitor_listbox.insert(tk.END, display_name)

    def _add_monitor_target(self):
        target = self._resolve_metric_display_target(self.monitor_target_var.get())
        if not target or target not in self.spots:
            messagebox.showerror("Invalid target", "Pick a valid betting target to monitor.")
            return
        if target not in self.monitored_targets:
            self.monitored_targets.append(target)
            self.target_stats[target]
            self._refresh_monitor_list()
            self._refresh_trigger_metric_choices()
        if target in self.monitor_target_id_to_display:
            self.monitor_target_var.set(self.monitor_target_id_to_display[target])

    def _remove_selected_monitor(self):
        if self.monitor_listbox is None:
            return
        selected = self.monitor_listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        target = self.monitored_targets[idx]
        self.monitored_targets.pop(idx)
        self.target_stats.pop(target, None)
        self._refresh_monitor_list()
        self._refresh_trigger_metric_choices()

    def _refresh_trigger_metric_choices(self):
        if self.trigger_metric_combo is None:
            return
        metric_values = self.BASE_METRICS + self.TARGET_METRICS
        self.trigger_metric_combo.configure(values=metric_values)
        if self.trigger_metric_var.get() not in metric_values:
            self.trigger_metric_var.set(metric_values[0])
        self._on_trigger_metric_changed()

    def _metric_requires_target(self, metric):
        return metric in self.TARGET_METRICS

    def _on_trigger_metric_changed(self, _event=None):
        if self.trigger_metric_target_combo is None:
            return
        metric = self.trigger_metric_var.get()
        requires_target = self._metric_requires_target(metric)
        targets = self._common_strategy_targets()
        self.trigger_metric_target_combo.configure(values=targets)
        if targets and self.trigger_metric_target_var.get() not in targets:
            self.trigger_metric_target_var.set(targets[0])
        if requires_target:
            self.trigger_metric_target_combo.configure(state="normal")
        else:
            self.trigger_metric_target_combo.configure(state="disabled")

    def _refresh_action_targets(self):
        if self.action_target_combo is None or self.action_value_entry is None:
            return
        action_type = self.action_type_var.get()
        if action_type == "set_bet_amount":
            choices = self._common_strategy_targets()
            self.action_target_combo.configure(values=choices, state="normal")
            if choices and self.action_target_var.get() not in choices:
                self.action_target_var.set(choices[0])
            self.action_value_entry.configure(state="normal")
            if not self.action_value_var.get().strip():
                self.action_value_var.set("1")
        elif action_type == "switch_mode":
            self.action_target_combo.configure(values=self.STRATEGY_MODES, state="readonly")
            if self.action_target_var.get() not in self.STRATEGY_MODES:
                self.action_target_var.set(self.STRATEGY_MODES[0])
            self.action_value_entry.configure(state="disabled")
        elif action_type == "set_chip_denom":
            self.action_target_combo.configure(values=(), state="disabled")
            self.action_target_var.set("")
            self.action_value_entry.configure(state="normal")
            if self.action_value_var.get().strip() not in {str(d) for d in self.CHIP_DENOMS}:
                self.action_value_var.set(str(self.selected_chip.get()))
        else:
            self.action_target_combo.configure(values=(), state="disabled")
            self.action_target_var.set("")
            self.action_value_entry.configure(state="disabled")
            self.action_value_var.set("")

    def _on_action_changed(self, _event=None):
        self._refresh_action_targets()

    def _add_rule_from_builder(self):
        mode_scope = self.trigger_mode_var.get().strip().lower()
        if mode_scope not in ("any",) + self.STRATEGY_MODES:
            messagebox.showerror("Invalid mode", "Mode scope must be one of Any/Standard/Recovery/Progression/Repeat.")
            return

        metric = self.trigger_metric_var.get().strip()
        if metric not in self.BASE_METRICS + self.TARGET_METRICS:
            messagebox.showerror("Invalid metric", "Select a valid trigger metric.")
            return

        metric_target = self.trigger_metric_target_var.get().strip()
        if self._metric_requires_target(metric):
            if metric_target not in self.spots:
                messagebox.showerror("Invalid metric target", "Select a valid target for hit/miss metrics.")
                return
            if metric_target not in self.monitored_targets:
                self.monitored_targets.append(metric_target)
                self.target_stats[metric_target]
                self._refresh_monitor_list()
        else:
            metric_target = ""

        operator = self.trigger_operator_var.get().strip()
        if operator not in self.RULE_OPERATORS:
            messagebox.showerror("Invalid operator", "Select a valid comparison operator.")
            return

        value = self._safe_int(self.trigger_value_var.get(), None)
        if value is None:
            messagebox.showerror("Invalid value", "Trigger value must be an integer.")
            return

        priority = self._safe_int(self.trigger_priority_var.get(), 50)

        action = self.action_type_var.get().strip()
        if action not in self.RULE_ACTIONS:
            messagebox.showerror("Invalid action", "Select a valid action.")
            return

        action_target = self.action_target_var.get().strip()
        action_value = self.action_value_var.get().strip()
        if action == "set_bet_amount":
            if action_target not in self.spots:
                messagebox.showerror("Invalid action target", "Choose a valid bet target.")
                return
            parsed_action_value = self._safe_int(action_value, None)
            if parsed_action_value is None or parsed_action_value < 0:
                messagebox.showerror("Invalid action value", "Bet amount must be a non-negative integer.")
                return
            action_value = parsed_action_value
        elif action == "switch_mode":
            if action_target not in self.STRATEGY_MODES:
                messagebox.showerror("Invalid action target", "Switch mode requires a valid mode target.")
                return
            action_value = 0
        elif action == "set_chip_denom":
            parsed_action_value = self._safe_int(action_value, None)
            if parsed_action_value not in self.CHIP_DENOMS:
                messagebox.showerror("Invalid chip", f"Chip denomination must be one of: {self.CHIP_DENOMS}")
                return
            action_target = ""
            action_value = parsed_action_value
        else:
            action_target = ""
            action_value = 0

        next_mode = self.action_next_mode_var.get().strip().lower()
        if next_mode and next_mode not in self.STRATEGY_MODES:
            messagebox.showerror("Invalid next mode", "Optional mode switch must be a valid mode.")
            return

        rule = {
            "id": self.next_rule_id,
            "mode": mode_scope,
            "metric": metric,
            "metric_target": metric_target,
            "operator": operator,
            "value": value,
            "priority": priority,
            "action": action,
            "action_target": action_target,
            "action_value": action_value,
            "next_mode": next_mode,
        }
        self.next_rule_id += 1
        self.rules.append(rule)
        self._refresh_rules_list()
        self._refresh_trigger_metric_choices()
        self._append_log(f"Added rule R{rule['id']}: {self._format_rule(rule)}")

    def _remove_selected_rule(self):
        if self.rules_listbox is None:
            return
        selected = self.rules_listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        ordered = self._ordered_rules()
        if idx < 0 or idx >= len(ordered):
            return
        rule_id = ordered[idx]["id"]
        self.rules = [r for r in self.rules if r["id"] != rule_id]
        self._refresh_rules_list()
        self._append_log(f"Deleted rule R{rule_id}")

    def _ordered_rules(self):
        return sorted(self.rules, key=lambda r: (-r["priority"], r["id"]))

    def _refresh_rules_list(self):
        if self.rules_listbox is None:
            return
        self.rules_listbox.delete(0, tk.END)
        for rule in self._ordered_rules():
            self.rules_listbox.insert(tk.END, f"R{rule['id']} P{rule['priority']} | {self._format_rule(rule)}")

    def _format_rule(self, rule):
        condition = f"{rule['metric']}"
        if rule.get("metric_target"):
            condition = f"{condition}({rule['metric_target']})"
        condition = f"mode={rule['mode']} and {condition} {rule['operator']} {rule['value']}"

        action = rule["action"]
        if action == "set_bet_amount":
            action_text = f"set_bet_amount({rule['action_target']}, {rule['action_value']})"
        elif action == "switch_mode":
            action_text = f"switch_mode({rule['action_target']})"
        elif action == "set_chip_denom":
            action_text = f"set_chip_denom({rule['action_value']})"
        else:
            action_text = action

        if rule.get("next_mode"):
            action_text = f"{action_text}; next_mode({rule['next_mode']})"
        return f"IF {condition} THEN {action_text}"

    def _set_mode_from_ui(self):
        mode = self.set_mode_var.get().strip().lower()
        if mode not in self.STRATEGY_MODES:
            messagebox.showerror("Invalid mode", "Choose a valid mode.")
            return
        self.current_mode.set(mode)
        self._refresh_session_status()
        self._append_log(f"Mode set to {mode}")

    def _reset_session_counters(self, from_init=False):
        start_bankroll = self._safe_int(self.start_bankroll_var.get(), None)
        if start_bankroll is None:
            if not from_init:
                messagebox.showerror("Invalid bankroll", "Start bankroll must be an integer.")
            start_bankroll = 10000
            self.start_bankroll_var.set(str(start_bankroll))

        self.bankroll = start_bankroll
        self.peak_bankroll = start_bankroll
        self.spin_count = 0
        self.win_streak = 0
        self.loss_streak = 0
        self.last_spin = None
        self.last_spin_net = 0

        self.target_stats = defaultdict(
            lambda: {
                "hit_streak": 0,
                "miss_streak": 0,
                "spins_since_hit": 0,
                "hits_total": 0,
                "miss_total": 0,
            }
        )
        for target in self._active_metric_targets():
            self.target_stats[target]
        self._reset_stage_progress()

        if self.log_listbox is not None and not from_init:
            self.log_listbox.delete(0, tk.END)
            self._append_log(f"Session reset with bankroll {self._signed_currency(self.bankroll)}")
        self._refresh_session_status()

    def _apply_spin_from_input(self):
        outcome = self._parse_spin_outcome(self.spin_input_var.get())
        if outcome is None:
            allowed_text = self._spin_input_hint_text()
            messagebox.showerror("Invalid spin", f"Enter a spin result: {allowed_text}.")
            return
        self._apply_spin(outcome)

    def _spin_random(self):
        if self._is_american_wheel():
            outcomes = ["00", 0] + list(range(1, 37))
            if self._is_triple_zero_wheel():
                outcomes = ["000"] + outcomes
        else:
            outcomes = [0] + list(range(1, 37))
        outcome = random.choice(outcomes)
        self.spin_input_var.set(str(outcome))
        self._apply_spin(outcome)

    def _parse_spin_outcome(self, raw_value):
        text = str(raw_value).strip().upper()
        if text == "000":
            return "000" if self._is_triple_zero_wheel() else None
        if text == "00":
            return "00" if self._is_american_wheel() else None
        n = self._safe_int(text, None)
        if n is None:
            return None
        if 0 <= n <= 36:
            return n
        return None

    def _spin_input_hint_text(self):
        if self._is_american_wheel():
            if self._is_triple_zero_wheel():
                return "000, 00, 0, or 1-36"
            return "00, 0, or 1-36"
        return "0 or 1-36"

    def _is_american_wheel(self):
        return self.wheel_family_var.get() == self.WHEEL_FAMILIES[0]

    def _is_triple_zero_wheel(self):
        return self._is_american_wheel() and self.american_bet_option_var.get() == self.AMERICAN_BET_OPTIONS[1]

    def _zero_pocket_tokens(self):
        if not self._is_american_wheel():
            return ("0",)
        if self._is_triple_zero_wheel():
            return ("000", "00", "0")
        return ("00", "0")

    def _zero_pocket_specs(self):
        tokens = self._zero_pocket_tokens()
        segment_h = 3.0 / max(1, len(tokens))
        start = 0.0
        specs = []
        for token in tokens:
            end = start + segment_h
            specs.append({"token": token, "start": start, "end": end})
            start = end
        return specs

    def _token_to_outcome(self, token):
        if token in ("00", "000"):
            return token
        return int(token)

    @staticmethod
    def _parse_special_token(token):
        text = str(token).strip()
        if text in ("00", "000"):
            return text
        try:
            return int(text)
        except ValueError:
            return None

    @staticmethod
    def _zero_pair_spot_id(token_a, token_b):
        if {token_a, token_b} == {"0", "00"}:
            return "split_0_00"
        ordered = sorted([str(token_a), str(token_b)], key=lambda t: {"000": -2, "00": -1}.get(t, int(t)))
        return f"split_{ordered[0]}_{ordered[1]}"

    @staticmethod
    def _alpha_index(index):
        n = int(index)
        if n <= 0:
            return "A"
        chars = []
        while n > 0:
            n -= 1
            chars.append(chr(ord("A") + (n % 26)))
            n //= 26
        return "".join(reversed(chars))

    @staticmethod
    def _special_split_axis(spot_id):
        if not spot_id.startswith("split_") or spot_id.startswith(("split_h_", "split_v_")):
            return None
        if spot_id in {"split_000_0", "split_000_00"}:
            return "horizontal"
        if spot_id == "split_0_00":
            return "vertical"
        parts = spot_id.split("_")[1:]
        if len(parts) != 2:
            return None
        token_a, token_b = parts
        zero_tokens = {"0", "00", "000"}

        def is_first_col_number(token):
            try:
                value = int(token)
            except ValueError:
                return False
            return 1 <= value <= 3

        if (token_a in zero_tokens and is_first_col_number(token_b)) or (
            token_b in zero_tokens and is_first_col_number(token_a)
        ):
            return "horizontal"
        if token_a in zero_tokens and token_b in zero_tokens:
            return "vertical"
        return None

    def _is_french_wheel(self):
        return self.wheel_family_var.get() == self.WHEEL_FAMILIES[1] and self.european_bet_option_var.get() in self.EUROPEAN_BET_OPTIONS[1:]

    def _is_french_en_prison(self):
        return self.wheel_family_var.get() == self.WHEEL_FAMILIES[1] and self.european_bet_option_var.get() == self.EUROPEAN_BET_OPTIONS[1]

    def _is_french_half_back(self):
        return self.wheel_family_var.get() == self.WHEEL_FAMILIES[1] and self.european_bet_option_var.get() == self.EUROPEAN_BET_OPTIONS[2]

    def _apply_spin(self, outcome):
        net = self._net_for_outcome(outcome)
        self.spin_count += 1
        self.last_spin = outcome
        self.last_spin_net = net
        self.bankroll += net
        self.peak_bankroll = max(self.peak_bankroll, self.bankroll)

        if net > 0:
            self.win_streak += 1
            self.loss_streak = 0
        elif net < 0:
            self.loss_streak += 1
            self.win_streak = 0
        else:
            self.win_streak = 0
            self.loss_streak = 0

        self._update_target_stats(outcome)
        stage_trigger = self._evaluate_stage_triggers_for_spin()
        fired = self._evaluate_rules_for_spin()
        self._refresh_session_status()

        stage_text = f"T{stage_trigger['id']}" if stage_trigger else "none"
        fired_text = ", ".join([f"R{r['id']}" for r in fired]) if fired else "none"
        self._append_log(
            f"Spin {self.spin_count}: result={outcome}, net={self._signed_currency(net)}, bankroll={self._signed_currency(self.bankroll)}, stage={self.stage_var.get()}, trigger={stage_text}, rules={fired_text}"
        )

    def _active_metric_targets(self):
        targets = set(self.monitored_targets)
        for rule in self.rules:
            if self._metric_requires_target(rule.get("metric", "")):
                target = rule.get("metric_target", "")
                if target in self.spots:
                    targets.add(target)
        return sorted(targets)

    def _update_target_stats(self, outcome):
        for target in self._active_metric_targets():
            if target not in self.spots:
                continue
            stats = self.target_stats[target]
            hit = self._spot_covers_outcome(target, outcome)
            if hit:
                stats["hit_streak"] += 1
                stats["miss_streak"] = 0
                stats["spins_since_hit"] = 0
                stats["hits_total"] += 1
            else:
                stats["miss_streak"] += 1
                stats["hit_streak"] = 0
                stats["spins_since_hit"] += 1
                stats["miss_total"] += 1

    def _evaluate_rules_for_spin(self):
        fired = []
        for rule in self._ordered_rules():
            if self._rule_matches(rule):
                self._execute_rule(rule)
                fired.append(rule)
                if len(fired) >= self.max_rules_per_spin:
                    break
        return fired

    def _rule_matches(self, rule):
        if rule["mode"] != "any" and rule["mode"] != self.current_mode.get():
            return False
        metric_value = self._metric_value(rule["metric"], rule.get("metric_target", ""))
        if metric_value is None:
            return False
        return self._compare_metric(metric_value, rule["operator"], rule["value"])

    def _metric_value(self, metric, target=""):
        if metric == "win_streak":
            return self.win_streak
        if metric == "loss_streak":
            return self.loss_streak
        if metric == "spin_count":
            return self.spin_count
        if metric == "bankroll":
            return self.bankroll
        if metric == "session_profit":
            start = self._safe_int(self.start_bankroll_var.get(), 0)
            return self.bankroll - start
        if metric == "drawdown":
            return max(0, self.peak_bankroll - self.bankroll)
        if metric == "last_spin_net":
            return self.last_spin_net

        if metric in self.TARGET_METRICS:
            if target not in self.spots:
                return None
            stats = self.target_stats[target]
            return stats.get(metric)
        return None

    def _compare_metric(self, lhs, operator, rhs):
        if operator == ">=":
            return lhs >= rhs
        if operator == ">":
            return lhs > rhs
        if operator == "<=":
            return lhs <= rhs
        if operator == "<":
            return lhs < rhs
        if operator == "==":
            return lhs == rhs
        if operator == "!=":
            return lhs != rhs
        return False

    def _execute_rule(self, rule):
        action = rule["action"]
        action_desc = action
        if action == "set_bet_amount":
            self._set_spot_total(rule["action_target"], rule["action_value"])
            action_desc = f"set_bet_amount {rule['action_target']}={rule['action_value']}"
        elif action == "clear_all_bets":
            self._clear_bets()
            action_desc = "clear_all_bets"
        elif action == "switch_mode":
            mode = rule["action_target"]
            if mode in self.STRATEGY_MODES:
                self.current_mode.set(mode)
                self.set_mode_var.set(mode)
                action_desc = f"switch_mode {mode}"
        elif action == "set_chip_denom":
            denom = rule["action_value"]
            if denom in self.CHIP_DENOMS:
                self._set_selected_chip(denom)
                action_desc = f"set_chip_denom {denom}"

        next_mode = rule.get("next_mode", "")
        if next_mode in self.STRATEGY_MODES:
            self.current_mode.set(next_mode)
            self.set_mode_var.set(next_mode)
            action_desc = f"{action_desc}; next_mode {next_mode}"
        self._append_log(f"Rule R{rule['id']} fired: {action_desc}")

    def _set_spot_total(self, spot_id, amount):
        if spot_id not in self.spots:
            return
        if amount <= 0:
            self._clear_spot_bet(spot_id)
            return

        chips = self._chip_breakdown(amount)
        if spot_id in self.stack_tags:
            self.canvas.delete(self.stack_tags[spot_id])
            self.stack_tags.pop(spot_id, None)
        self.bets[spot_id] = chips
        self.bet_chip_sources[spot_id] = [None] * len(chips)
        self._redraw_spot_stack(spot_id)
        self._update_total()

    def _chip_breakdown(self, amount):
        if amount <= 0:
            return []
        chips = []
        remaining = amount
        for denom in sorted(self.CHIP_DENOMS, reverse=True):
            count = remaining // denom
            if count > 0:
                chips.extend([denom] * count)
                remaining -= count * denom
        return chips

    def _append_log(self, text):
        if self.log_listbox is None:
            return
        self.log_listbox.insert(tk.END, text)
        if self.log_listbox.size() > 300:
            self.log_listbox.delete(0, self.log_listbox.size() - 301)
        self.log_listbox.yview_moveto(1.0)

    def _refresh_session_status(self):
        start = self._safe_int(self.start_bankroll_var.get(), 0)
        profit = self.bankroll - start
        drawdown = max(0, self.peak_bankroll - self.bankroll)
        wheel_desc = self.wheel_type_var.get()
        last = "-" if self.last_spin is None else str(self.last_spin)
        active_bet_type = self.stage_trigger_target_id_to_display.get(
            self.stage_active_bet_target,
            self.stage_active_bet_target if self.stage_active_bet_target else "-",
        )
        raw_step = self.stage_profit_increment_var.get().strip()
        step = self._safe_int(raw_step, 0) if raw_step else 0
        if step > 0 and isinstance(self.next_profit_stage_target, int):
            stage_reset_text = f"Stage Reset: +${step:,} increments (next ${self.next_profit_stage_target:,})"
        elif step > 0:
            stage_reset_text = f"Stage Reset: +${step:,} increments"
        else:
            stage_reset_text = "Stage Reset: New Session Profit"
        status = (
            f"Stage: {self.stage_var.get()} | Mode: {self.current_mode.get()} | Spins: {self.spin_count} | Last: {last} ({self._signed_currency(self.last_spin_net)})\n"
            f"Wheel: {wheel_desc} | Bankroll: {self._signed_currency(self.bankroll)} | Profit: {self._signed_currency(profit)} | Drawdown: {self._currency(drawdown)}\n"
            f"Win Streak: {self.win_streak} | Loss Streak: {self.loss_streak} | Rules: {len(self.rules)} | Stage Triggers: {len(self.stage_triggers)} | Active Bet Type: {active_bet_type}\n"
            f"{stage_reset_text}"
        )
        self.session_status_var.set(status)
        self.set_mode_var.set(self.current_mode.get())

    def _save_strategy_json(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="roulette_strategy.json",
        )
        if not file_path:
            return

        payload = {
            "version": 1,
            "start_bankroll": self._safe_int(self.start_bankroll_var.get(), 10000),
            "current_mode": self.current_mode.get(),
            "stage_profit_increment": self._safe_int(self.stage_profit_increment_var.get(), 0),
            "stage_triggers": self.stage_triggers,
            "monitored_targets": self.monitored_targets,
            "rules": self.rules,
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self._append_log(f"Saved strategy JSON: {file_path}")
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))

    def _load_strategy_json(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Load failed", str(exc))
            return

        if not isinstance(payload, dict):
            messagebox.showerror("Load failed", "Strategy JSON root must be an object.")
            return

        self.start_bankroll_var.set(str(self._safe_int(payload.get("start_bankroll"), 10000)))

        mode = str(payload.get("current_mode", self.STRATEGY_MODES[0])).strip().lower()
        if mode not in self.STRATEGY_MODES:
            mode = self.STRATEGY_MODES[0]
        self.current_mode.set(mode)
        self.set_mode_var.set(mode)

        stage_increment = self._safe_int(payload.get("stage_profit_increment"), 0)
        self.stage_profit_increment_var.set(str(stage_increment) if stage_increment > 0 else "")

        loaded_stage_triggers = []
        max_stage_id = 0
        for raw_trigger in payload.get("stage_triggers", []):
            trigger = self._normalize_loaded_stage_trigger(raw_trigger)
            if trigger is None:
                continue
            loaded_stage_triggers.append(trigger)
            max_stage_id = max(max_stage_id, trigger["id"])
        self.stage_triggers = loaded_stage_triggers
        self.next_stage_trigger_id = max_stage_id + 1 if max_stage_id > 0 else 1
        self.stage_trigger_hit_counts = defaultdict(int)
        self.stage_group_action_cache = {}

        loaded_targets = []
        for target in payload.get("monitored_targets", []):
            if isinstance(target, str) and target in self.spots and target not in loaded_targets:
                loaded_targets.append(target)
        self.monitored_targets = loaded_targets

        loaded_rules = []
        max_id = 0
        for raw_rule in payload.get("rules", []):
            rule = self._normalize_loaded_rule(raw_rule)
            if rule is None:
                continue
            loaded_rules.append(rule)
            max_id = max(max_id, rule["id"])

        self.rules = loaded_rules
        self.next_rule_id = max_id + 1 if max_id > 0 else 1

        self._refresh_stage_trigger_target_choices()
        self._refresh_stage_trigger_list()
        self._refresh_stage_list()
        self._refresh_monitor_target_choices()
        self._refresh_monitor_list()
        self._refresh_trigger_metric_choices()
        self._refresh_action_targets()
        self._refresh_rules_list()
        self._reset_session_counters()
        self._append_log(f"Loaded strategy JSON: {file_path}")

    def _normalize_loaded_rule(self, raw_rule):
        if not isinstance(raw_rule, dict):
            return None

        mode = str(raw_rule.get("mode", "any")).strip().lower()
        if mode not in ("any",) + self.STRATEGY_MODES:
            mode = "any"

        metric = str(raw_rule.get("metric", "")).strip()
        if metric not in self.BASE_METRICS + self.TARGET_METRICS:
            return None

        metric_target = str(raw_rule.get("metric_target", "")).strip()
        if self._metric_requires_target(metric):
            if metric_target not in self.spots:
                return None
        else:
            metric_target = ""

        operator = str(raw_rule.get("operator", "==")).strip()
        if operator not in self.RULE_OPERATORS:
            return None

        value = self._safe_int(raw_rule.get("value"), None)
        if value is None:
            return None

        priority = self._safe_int(raw_rule.get("priority"), 50)
        action = str(raw_rule.get("action", "")).strip()
        if action not in self.RULE_ACTIONS:
            return None

        action_target = str(raw_rule.get("action_target", "")).strip()
        action_value = raw_rule.get("action_value", 0)

        if action == "set_bet_amount":
            if action_target not in self.spots:
                return None
            action_value = self._safe_int(action_value, None)
            if action_value is None or action_value < 0:
                return None
        elif action == "switch_mode":
            if action_target not in self.STRATEGY_MODES:
                return None
            action_value = 0
        elif action == "set_chip_denom":
            action_target = ""
            action_value = self._safe_int(action_value, None)
            if action_value not in self.CHIP_DENOMS:
                return None
        else:
            action_target = ""
            action_value = 0

        next_mode = str(raw_rule.get("next_mode", "")).strip().lower()
        if next_mode and next_mode not in self.STRATEGY_MODES:
            next_mode = ""

        rule_id = self._safe_int(raw_rule.get("id"), self.next_rule_id)
        if rule_id is None or rule_id <= 0:
            rule_id = self.next_rule_id

        return {
            "id": rule_id,
            "mode": mode,
            "metric": metric,
            "metric_target": metric_target,
            "operator": operator,
            "value": value,
            "priority": priority,
            "action": action,
            "action_target": action_target,
            "action_value": action_value,
            "next_mode": next_mode,
        }

    def _normalize_loaded_stage_trigger(self, raw_trigger):
        if not isinstance(raw_trigger, dict):
            return None

        basis = str(raw_trigger.get("basis", self.STAGE_TRIGGER_BASES[0])).strip()
        if basis not in self.STAGE_TRIGGER_BASES:
            basis = self.STAGE_TRIGGER_BASES[0]

        count_threshold = self._safe_int(raw_trigger.get("count_threshold"), 1)
        if count_threshold is None or count_threshold <= 0:
            count_threshold = 1

        trigger_type = str(raw_trigger.get("type", "")).strip()
        if trigger_type not in self.STAGE_TRIGGER_TYPES:
            return None

        target = str(raw_trigger.get("target", "")).strip()
        if trigger_type in ("Bet Type", "Exact Bet"):
            if target not in self.spots:
                return None
        else:
            target = ""

        amount_raw = raw_trigger.get("amount", None)
        amount = None
        if amount_raw not in (None, ""):
            amount = self._safe_int(amount_raw, None)
            if amount is None or amount < 0:
                return None

        action = str(raw_trigger.get("action", "No Action")).strip()
        if action not in self.STAGE_TRIGGER_ACTIONS:
            action = "No Action"

        action_scope = str(raw_trigger.get("action_scope", "This Trigger")).strip()
        if action_scope not in self.STAGE_TRIGGER_ACTION_SCOPES:
            action_scope = "This Trigger"

        group_id = str(raw_trigger.get("group_id", "")).strip()
        if action_scope == "Group" and not group_id:
            action_scope = "This Trigger"

        action_target = str(raw_trigger.get("action_target", "")).strip()
        if action in ("Set Bet Type", "Set Bet Amount", "Set Bet Type + Amount"):
            if action_target not in self.spots:
                return None
        elif action == "Switch Stage":
            if action_target not in self.STAGE_NAMES:
                return None
        else:
            action_target = ""

        action_amount_raw = raw_trigger.get("action_amount", None)
        action_amount = None
        if action_amount_raw not in (None, ""):
            action_amount = self._safe_int(action_amount_raw, None)
            if action_amount is None or action_amount < 0:
                return None
        if action in ("Set Bet Amount", "Set Bet Type + Amount") and action_amount is None:
            return None

        trigger_id = self._safe_int(raw_trigger.get("id"), self.next_stage_trigger_id)
        if trigger_id is None or trigger_id <= 0:
            trigger_id = self.next_stage_trigger_id

        return {
            "id": trigger_id,
            "basis": basis,
            "count_threshold": count_threshold,
            "type": trigger_type,
            "target": target,
            "amount": amount,
            "action": action,
            "action_target": action_target,
            "action_amount": action_amount,
            "action_scope": action_scope,
            "group_id": group_id,
        }

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _signed_currency(value):
        amount = float(value)
        if abs(amount - round(amount)) < 1e-9:
            amount = int(round(amount))
            if amount > 0:
                return f"+${amount:,}"
            if amount < 0:
                return f"-${abs(amount):,}"
            return "$0"
        if amount > 0:
            return f"+${amount:,.2f}"
        if amount < 0:
            return f"-${abs(amount):,.2f}"
        return "$0"

    @staticmethod
    def _currency(value):
        amount = float(value)
        if abs(amount - round(amount)) < 1e-9:
            return f"${int(round(amount)):,}"
        return f"${amount:,.2f}"

    def _build_top_panel(self, parent):
        top = tk.Frame(parent, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=(4, 0))

        top_row = tk.Frame(top, bg="#FFFFFF")
        top_row.pack(fill="x", anchor="n")

        # Keep spin result map as far left/top as possible.
        self._build_payout_chart(top_row)

        left_controls = tk.Frame(top_row, bg="#FFFFFF")
        left_controls.pack(side="left", padx=(8, 0), anchor="n")

        self._build_wheel_controls(left_controls)

        self.legend_frame = tk.Frame(top_row, bg="#FFFFFF")
        self.legend_frame.pack(side="left", fill="y", padx=(8, 0), anchor="n")

        legend_chip_row = tk.Frame(self.legend_frame, bg="#FFFFFF")
        legend_chip_row.pack(anchor="w")

        for denom in self.CHIP_DENOMS:
            chip_canvas = tk.Canvas(
                legend_chip_row,
                width=62,
                height=62,
                bg="#FFFFFF",
                highlightthickness=0,
                bd=0,
            )
            chip_canvas.pack(side="left", padx=4)
            self._draw_chip(chip_canvas, 31, 31, 24, denom, top_label=True)
            chip_canvas.bind("<Button-1>", lambda _e, d=denom: self._set_selected_chip(d))
            self.legend_canvases[denom] = chip_canvas

        bet_controls = tk.Frame(top_row, bg="#FFFFFF")
        bet_controls.pack(side="left", padx=(10, 0), fill="y", anchor="n")

        controls_row = tk.Frame(bet_controls, bg="#FFFFFF")
        controls_row.pack(anchor="w")
        total_lbl = tk.Label(
            controls_row,
            textvariable=self.total_var,
            bg="#FFFFFF",
            fg="#000000",
            font=("Segoe UI", 14, "bold"),
        )
        total_lbl.pack(side="left")

        clear_btn = tk.Button(
            controls_row,
            text="Clear",
            command=self._clear_bets,
            bg="#0000FF",
            fg="#f9fafb",
            activebackground="#6b7280",
            activeforeground="#ffffff",
            relief="raised",
            bd=2,
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=6,
        )
        clear_btn.pack(side="left", padx=(16, 0))

        tk.Label(
            bet_controls,
            text="Right-click to remove Chips",
            bg="#FFFFFF",
            fg="#ef4444",
            font=("Segoe UI", 11, "bold"),
            anchor="e",
            justify="right",
        ).pack(fill="x", pady=(4, 0))

        self.call_bets_display_host = tk.Frame(self.legend_frame, bg="#FFFFFF", highlightthickness=0, bd=0)
        self.call_bets_display_host.pack(anchor="w", pady=(3, 3))
        self.call_bets_display_row = self.call_bets_display_host

        self.call_bets_display_inner = tk.Frame(self.call_bets_display_host, bg="#FFFFFF")
        self.call_bets_display_inner.pack(anchor="w")

        self.call_bets_button = tk.Button(
            self.call_bets_display_inner,
            text="Call Bets",
            command=self._open_call_bets_popup,
            bg="#0f766e",
            fg="#ffffff",
            activebackground="#115e59",
            activeforeground="#ffffff",
            relief="raised",
            bd=2,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=4,
        )
        self.call_bets_button.pack(side="left", padx=(0, 3), anchor="s")

        self.call_bets_left_panel = tk.LabelFrame(
            self.call_bets_display_inner,
            text="Call Bets 1-3",
            bg="#FFFFFF",
            fg="#111827",
            padx=6,
            pady=4,
            font=("Segoe UI", 9, "bold"),
        )
        self.call_bets_left_panel.pack(side="left", padx=(0, 3))
        self.call_bets_listbox_left = tk.Listbox(
            self.call_bets_left_panel,
            width=29,
            height=4,
            exportselection=False,
            activestyle="none",
        )
        self.call_bets_listbox_left.pack(fill="both", expand=True)
        self.call_bets_listbox_left.bind("<Button-3>", self._on_call_bet_list_click_left)
        self.call_bets_listbox_left.bind("<Button-2>", self._on_call_bet_list_click_left)

        self.call_bets_right_panel = tk.LabelFrame(
            self.call_bets_display_inner,
            text="Call Bets 4-6",
            bg="#FFFFFF",
            fg="#111827",
            padx=6,
            pady=4,
            font=("Segoe UI", 9, "bold"),
        )
        self.call_bets_right_panel.pack(side="left", padx=0)
        self.call_bets_listbox_right = tk.Listbox(
            self.call_bets_right_panel,
            width=29,
            height=4,
            exportselection=False,
            activestyle="none",
        )
        self.call_bets_listbox_right.pack(fill="both", expand=True)
        self.call_bets_listbox_right.bind("<Button-3>", self._on_call_bet_list_click_right)
        self.call_bets_listbox_right.bind("<Button-2>", self._on_call_bet_list_click_right)

        self.call_bets_display_host.update_idletasks()
        self.call_bets_reserved_h = max(1, self.call_bets_display_host.winfo_reqheight())
        self.call_bets_spacer = tk.Frame(
            self.legend_frame,
            bg="#FFFFFF",
            height=self.call_bets_reserved_h,
            highlightthickness=0,
            bd=0,
        )
        self.call_bets_spacer.pack_propagate(False)

        self._sync_wheel_option_controls()
        self._refresh_call_bets_list()

    def _build_wheel_controls(self, parent):
        wheel_frame = tk.LabelFrame(
            parent,
            text="Wheel Type / Rules",
            bg="#FFFFFF",
            fg="#111827",
            padx=8,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        )
        wheel_frame.pack(fill="x", expand=False, anchor="n", padx=(0, 8), pady=(0, 0))

        row1 = tk.Frame(wheel_frame, bg="#FFFFFF")
        row1.pack(anchor="w")
        tk.Label(row1, text="Wheel", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        self.wheel_type_combo = ttk.Combobox(
            row1,
            textvariable=self.wheel_type_var,
            values=self.WHEEL_TYPE_OPTIONS,
            width=34,
            state="readonly",
        )
        self.wheel_type_combo.pack(side="left", padx=(6, 0))
        self.wheel_type_combo.bind("<<ComboboxSelected>>", self._on_wheel_settings_changed)

        self.wheel_call_button_row = None

        self._sync_wheel_option_controls()

    def _on_wheel_settings_changed(self, _event=None):
        self._sync_wheel_option_controls()
        self._rebuild_board_for_wheel()
        self.en_prison_pending.clear()
        self._refresh_payout_chart()
        self._refresh_session_status()

    def _sync_wheel_option_controls(self):
        if self.wheel_type_var.get() not in self.WHEEL_TYPE_OPTIONS:
            self.wheel_type_var.set(self.WHEEL_TYPE_OPTIONS[0])

        wheel_type = self.wheel_type_var.get()
        mapping = {
            self.WHEEL_TYPE_OPTIONS[0]: (self.WHEEL_FAMILIES[0], self.AMERICAN_BET_OPTIONS[0], self.EUROPEAN_BET_OPTIONS[0]),
            self.WHEEL_TYPE_OPTIONS[1]: (self.WHEEL_FAMILIES[0], self.AMERICAN_BET_OPTIONS[1], self.EUROPEAN_BET_OPTIONS[0]),
            self.WHEEL_TYPE_OPTIONS[2]: (self.WHEEL_FAMILIES[1], self.AMERICAN_BET_OPTIONS[0], self.EUROPEAN_BET_OPTIONS[0]),
            self.WHEEL_TYPE_OPTIONS[3]: (self.WHEEL_FAMILIES[1], self.AMERICAN_BET_OPTIONS[0], self.EUROPEAN_BET_OPTIONS[1]),
            self.WHEEL_TYPE_OPTIONS[4]: (self.WHEEL_FAMILIES[1], self.AMERICAN_BET_OPTIONS[0], self.EUROPEAN_BET_OPTIONS[2]),
        }
        family, american_option, european_option = mapping.get(wheel_type, mapping[self.WHEEL_TYPE_OPTIONS[0]])
        self.wheel_family_var.set(family)
        self.american_bet_option_var.set(american_option)
        self.european_bet_option_var.set(european_option)
        self._sync_call_bets_controls()

    def _sync_call_bets_controls(self):
        is_french = self._is_french_wheel()
        if self.call_bets_button is not None:
            if is_french:
                self.call_bets_button.configure(state="normal")
            else:
                self.call_bets_button.configure(state="disabled")
                self._close_call_bet_popup()
        if self.call_bets_display_host is not None:
            if is_french:
                if self.call_bets_spacer is not None and self.call_bets_spacer.winfo_manager():
                    self.call_bets_spacer.pack_forget()
                if not self.call_bets_display_host.winfo_manager():
                    self.call_bets_display_host.pack(anchor="w", pady=(3, 3))
            else:
                if self.call_bets_display_host.winfo_manager():
                    self.call_bets_display_host.pack_forget()
                if self.call_bets_spacer is not None and not self.call_bets_spacer.winfo_manager():
                    self.call_bets_spacer.pack(anchor="w", pady=(3, 3))

    def _position_call_bets_display_boxes(self):
        # Call-bet list boxes now live in-flow directly below the chip legend.
        return

    def _rebuild_board_for_wheel(self):
        if not hasattr(self, "canvas"):
            return

        existing_bets = {spot_id: list(chips) for spot_id, chips in self.bets.items() if chips}
        existing_sources = {spot_id: list(self.bet_chip_sources.get(spot_id, [])) for spot_id in existing_bets}
        pending_before = set(self.en_prison_pending)

        self._hide_tooltip()
        self._hide_chip_add_popup()
        self.canvas.delete("all")
        self.spots = {}
        self.stack_tags = {}
        self._build_layout()

        self.bets = defaultdict(list)
        self.bet_chip_sources = defaultdict(list)
        for spot_id, chips in existing_bets.items():
            if spot_id not in self.spots:
                continue
            self.bets[spot_id] = list(chips)
            sources = list(existing_sources.get(spot_id, []))
            if len(sources) < len(chips):
                sources.extend([None] * (len(chips) - len(sources)))
            elif len(sources) > len(chips):
                sources = sources[: len(chips)]
            self.bet_chip_sources[spot_id] = sources
            self._redraw_spot_stack(spot_id)

        self.en_prison_pending = {
            spot_id
            for spot_id in pending_before
            if spot_id in self.EVEN_MONEY_OUTSIDE_IDS and spot_id in self.spots and sum(self.bets[spot_id]) > 0
        }

        self.monitored_targets = [target for target in self.monitored_targets if target in self.spots]
        for target in list(self.target_stats.keys()):
            if target not in self.spots:
                self.target_stats.pop(target, None)

        self._refresh_monitor_target_choices()
        self._refresh_monitor_list()
        self._refresh_trigger_metric_choices()
        self._refresh_action_targets()
        self._refresh_stage_trigger_target_choices()
        self._refresh_stage_trigger_list()
        self._refresh_rules_list()
        self._update_total()
        self._position_call_bets_display_boxes()

    def _build_payout_chart(self, parent):
        chart_wrap = tk.Frame(parent, bg="#FFFFFF")
        chart_wrap.pack(side="left", padx=(0, 0), anchor="n")
        self.chart_wrap = chart_wrap

        self.payout_title = tk.Label(
            chart_wrap,
            text="Spin Result Map",
            bg="#FFFFFF",
            fg="#000000",
            font=("Segoe UI", 10, "bold"),
        )
        self.payout_title.pack(anchor="center")

        self.payout_canvas = tk.Canvas(
            chart_wrap,
            width=self.mini_zero_w + self.cols * self.mini_cell_w + 2 * self.map_pad if hasattr(self, "cols") else 708,
            height=3 * self.mini_cell_h + 2 * self.map_pad,
            bg="#0f7a36",
            highlightthickness=1,
            highlightbackground="#d4af37",
            bd=0,
        )
        self.payout_canvas.pack()

        self._refresh_payout_chart()

    def _refresh_payout_chart(self):
        if not hasattr(self, "payout_canvas") or not hasattr(self, "cols"):
            return

        total_stake = sum(sum(v) for v in self.bets.values())
        self.payout_title.configure(text=f"Spin Result Map (Net win/loss per spin, Total Bet ${total_stake:,})")
        self.payout_canvas.delete("all")

        pad_x = self.map_pad
        pad_y = self.map_pad
        mini_cell_w = self.mini_cell_w
        mini_cell_h = self.mini_cell_h
        mini_zero_w = self.mini_zero_w
        left = pad_x
        top = pad_y

        for spec in self._zero_pocket_specs():
            token = spec["token"]
            y = top + spec["start"] * mini_cell_h
            h = (spec["end"] - spec["start"]) * mini_cell_h
            self._draw_spin_cell(left, y, mini_zero_w, h, token, self._net_for_outcome(self._token_to_outcome(token)))

        grid_left = left + mini_zero_w
        for c in range(self.cols):
            for r in range(3):
                n = self._number_at(c, r)
                x = grid_left + c * mini_cell_w
                y = top + r * mini_cell_h
                self._draw_spin_cell(x, y, mini_cell_w, mini_cell_h, str(n), self._net_for_outcome(n))

    def _align_spin_map_right(self):
        if not hasattr(self, "chart_wrap"):
            return
        # Keep the spin map pulled left so controls remain visible on smaller widths.
        self.chart_wrap.pack_configure(side="left", padx=(16, 0))

    def _draw_spin_cell(self, x, y, w, h, label, net):
        if net > 0:
            fill = "#ffffff"
            amount_color = "#2563eb"
        elif net < 0:
            fill = "#ffffff"
            amount_color = "#ea580c"
        else:
            fill = "#ffffff"
            amount_color = "#374151"

        self.payout_canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline="#d4af37", width=1)
        label_color = self._spin_label_color(label)
        self.payout_canvas.create_text(
            x + w / 2,
            y + h * 0.36,
            text=label,
            fill=label_color,
            font=("Segoe UI", 9, "bold"),
        )
        net_text = self._signed_currency(net)
        self.payout_canvas.create_text(
            x + w / 2,
            y + h * 0.72,
            text=net_text,
            fill=amount_color,
            font=("Segoe UI", 8, "bold"),
        )

    def _net_for_outcome(self, outcome):
        total_stake = 0.0
        total_return = 0.0
        apply_en_prison = self._is_french_en_prison()
        apply_half_back = self._is_french_half_back()
        next_prison_pending = set(self.en_prison_pending) if apply_en_prison else set()

        for spot_id, chips in self.bets.items():
            if not chips:
                continue
            spot_total = sum(chips)
            if spot_total <= 0:
                continue

            # En Prison resolution for the spin after zero:
            # win returns stake only (no profit), lose forfeits stake.
            if apply_en_prison and spot_id in next_prison_pending and outcome != 0:
                covered = self._spot_covers_outcome(spot_id, outcome)
                total_stake += spot_total
                if covered:
                    total_return += spot_total
                next_prison_pending.discard(spot_id)
                continue

            if spot_id in self.EVEN_MONEY_OUTSIDE_IDS and outcome == 0 and (apply_en_prison or apply_half_back):
                total_stake += spot_total
                if apply_half_back:
                    total_return += spot_total / 2
                else:
                    total_return += spot_total
                    next_prison_pending.add(spot_id)
                continue

            covered = self._spot_covers_outcome(spot_id, outcome)
            payout_mult = int(self.spots[spot_id]["payout"].split(":")[0])
            total_stake += spot_total
            if covered:
                total_return += spot_total * (payout_mult + 1)

        if apply_en_prison:
            # Keep pending list only for active even-money outside bets.
            self.en_prison_pending = {
                sid
                for sid in next_prison_pending
                if sid in self.bets and sum(self.bets[sid]) > 0 and sid in self.EVEN_MONEY_OUTSIDE_IDS
            }
        else:
            self.en_prison_pending = set()
        return total_return - total_stake

    def _spin_label_color(self, label):
        if label in {"0", "00", "000"}:
            return "#000000"
        try:
            n = int(label)
        except ValueError:
            return "#f8fafc"
        return "#ef4444" if n in self.RED_NUMBERS else "#111111"

    def _straight_popup_label_color(self, spot_id):
        token = str(spot_id).split("_", 1)[1] if "_" in str(spot_id) else ""
        if token in {"0", "00", "000"}:
            return "#16a34a"
        try:
            number = int(token)
        except ValueError:
            return "#000000"
        return "#b91c1c" if number in self.RED_NUMBERS else "#101010"

    @staticmethod
    def _outside_popup_label_color(spot_id):
        if str(spot_id).startswith("column_"):
            return "#7c3aed"
        if str(spot_id).startswith("dozen_"):
            return "#d946ef"
        outside_colors = {
            "outside_1_18": "#f97316",
            "outside_even": "#22ff22",
            "outside_red": "#b91c1c",
            "outside_black": "#101010",
            "outside_odd": "#00ffff",
            "outside_19_36": "#5b21b6",
        }
        return outside_colors.get(str(spot_id), "#000000")

    def _spot_covers_outcome(self, spot_id, outcome):
        numbers = self._spot_numbers(spot_id)
        return outcome in numbers

    def _spot_numbers(self, spot_id):
        if spot_id.startswith("straight_"):
            value = spot_id.replace("straight_", "")
            parsed = self._parse_special_token(value)
            return {parsed} if parsed is not None else set()

        if spot_id.startswith("split_h_") or spot_id.startswith("split_v_"):
            _, _, a, b = spot_id.split("_")
            return {int(a), int(b)}

        if spot_id.startswith("split_"):
            tokens = spot_id.split("_")[1:]
            if len(tokens) == 2:
                parsed_tokens = [self._parse_special_token(token) for token in tokens]
                if all(token is not None for token in parsed_tokens):
                    return set(parsed_tokens)

        if spot_id.startswith("corner_"):
            parts = spot_id.split("_")[1:]
            return {int(p) for p in parts}

        if spot_id.startswith("street_"):
            col = int(spot_id.split("_")[1]) - 1
            return {self._number_at(col, r) for r in range(3)}

        if spot_id.startswith("sixline_"):
            _, c1, c2 = spot_id.split("_")
            col1 = int(c1) - 1
            col2 = int(c2) - 1
            return {self._number_at(col1, r) for r in range(3)} | {self._number_at(col2, r) for r in range(3)}

        if spot_id.startswith(("topline_", "trio_", "basket_")):
            tokens = spot_id.split("_")[1:]
            parsed_tokens = [self._parse_special_token(token) for token in tokens]
            if all(token is not None for token in parsed_tokens):
                return set(parsed_tokens)

        if spot_id.startswith("column_"):
            col = int(spot_id.split("_")[1])
            return {n for n in range(1, 37) if n % 3 == col % 3}

        if spot_id.startswith("dozen_"):
            dz = int(spot_id.split("_")[1])
            start = 1 + (dz - 1) * 12
            return set(range(start, start + 12))

        if spot_id == "outside_1_18":
            return set(range(1, 19))
        if spot_id == "outside_even":
            return {n for n in range(1, 37) if n % 2 == 0}
        if spot_id == "outside_red":
            return set(self.RED_NUMBERS)
        if spot_id == "outside_black":
            return {n for n in range(1, 37) if n not in self.RED_NUMBERS}
        if spot_id == "outside_odd":
            return {n for n in range(1, 37) if n % 2 == 1}
        if spot_id == "outside_19_36":
            return set(range(19, 37))

        return set()

    def _build_board_canvas(self, parent):
        self.canvas_w = 1880
        self.canvas_h = 860
        self.canvas = tk.Canvas(
            parent,
            width=self.canvas_w,
            height=self.canvas_h,
            bg=self._surround_color(),
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.canvas.bind("<Configure>", lambda _e: self._position_call_bets_display_boxes())
        self.canvas.bind("<Motion>", self._on_canvas_motion_chip_hover_fallback, add="+")
        self.canvas.bind("<Leave>", self._on_canvas_leave_chip_hover_fallback, add="+")

    def _build_layout(self):
        self.marker_spot_ids = set()
        self.board_y = 26
        self.cell_w = 112
        self.cell_h = 136
        self.cols = 12
        self.vertical_gap = 18
        self.outside_box_gap = 3
        self.column_gap = 14
        self.zero_gap = self.column_gap
        base_column_w = 128 - 25
        self.column_bet_w = max(56, int(round(base_column_w * (2.0 / 3.0))))
        # Normalize every wheel to the triple-zero footprint width.
        # Non-triple layouts keep a left spacer before the zero pockets.
        self.zero_w = int(round(self.column_bet_w * 2.1))
        self.zero_draw_w = self.zero_w if self._is_triple_zero_wheel() else self.column_bet_w
        self.zero_left_spacer_w = max(0, self.zero_w - self.zero_draw_w)
        self.placed_chip_radius = 14
        self.marker_hover_radius = self.placed_chip_radius
        content_w = self.zero_w + self.zero_gap + self.cols * self.cell_w + self.column_gap + self.column_bet_w
        self.available_w = self.root.winfo_screenwidth() - 24
        self.board_x = int((self.available_w - content_w) / 2)
        self.zero_cell_x = self.board_x + self.zero_left_spacer_w

        num_left = self.board_x + self.zero_w + self.zero_gap
        num_top = self.board_y
        num_right = num_left + self.cols * self.cell_w
        num_bottom = num_top + 3 * self.cell_h
        full_right = num_right + self.column_gap + self.column_bet_w
        full_bottom = num_bottom + self.vertical_gap + 70 + self.vertical_gap + 72
        table_margin = self.vertical_gap

        frame_x1 = self.board_x - table_margin
        frame_y1 = self.board_y - table_margin
        frame_x2 = full_right + table_margin
        frame_y2 = full_bottom + table_margin
        self.table_right_edge = frame_x2
        self._draw_glass_swirl_background(frame_x1, frame_y1, frame_x2, frame_y2)
        self._draw_table_frame(frame_x1, frame_y1, frame_x2, frame_y2)

        self._draw_zero_cell(self.zero_cell_x, num_top, self.zero_draw_w, self.cell_h * 3)
        self._draw_number_grid(num_left, num_top)
        self._draw_column_bets(num_right, num_top)
        self._draw_bottom_outside_bets(num_left, num_bottom)
        self._create_inside_bet_spots(num_left, num_top)
        self._create_outside_bet_spots(num_left, num_top, num_right, num_bottom)
        self._refresh_spot_hover_display_names()

        # Tighten the canvas to board content so full-screen view doesn't leave clipped/off-screen bottom space.
        target_h = int(frame_y2 + 24)
        if target_h > 0 and target_h != self.canvas_h:
            self.canvas_h = target_h
            self.canvas.configure(height=self.canvas_h)

    def _draw_zero_cell(self, x, y, w, h):
        if self._is_triple_zero_wheel():
            # Right-facing triangle: 000 on the left, 00 and 0 nearest the number grid.
            box_w = max(32, self.column_bet_w)
            # Match triple-zero pocket box size to double-zero pocket box size.
            box_h = int(round(self.cell_h * 1.5))
            right_col_x = x + w - (box_w / 2.0)
            # Touching edge-to-edge with the right column (no gap, no overlap).
            left_col_x = right_col_x - box_w
            triangle_specs = (
                ("000", left_col_x, y + self.cell_h * 1.50),
                ("00", right_col_x, y + self.cell_h * 0.75),
                ("0", right_col_x, y + self.cell_h * 2.25),
            )
            for token, cx, cy in triangle_specs:
                x1 = cx - box_w / 2
                y1 = cy - box_h / 2
                x2 = cx + box_w / 2
                y2 = cy + box_h / 2
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self._board_felt_color(), outline="#d4af37", width=2)
                self.canvas.create_text(
                    cx,
                    cy,
                    text=token,
                    font=("Georgia", 26, "bold"),
                    fill="#000000",
                    justify="center",
                    angle=90,
                )
                self._add_spot(
                    f"straight_{token}",
                    f"Straight {token}",
                    (cx, cy),
                    payout="35:1",
                    hit_shape="rect",
                    hit_coords=(x1 + 4, y1 + 4, x2 - 4, y2 - 4),
                    has_marker=True,
                )
            return

        self.canvas.create_rectangle(x, y, x + w, y + h, fill=self._board_felt_color(), outline="#d4af37", width=2)
        specs = self._zero_pocket_specs()
        cell_h = h / 3.0
        font_size = 26

        for idx, spec in enumerate(specs):
            y1 = y + spec["start"] * cell_h
            y2 = y + spec["end"] * cell_h
            if idx > 0:
                self.canvas.create_line(x, y1, x + w, y1, fill="#d4af37", width=2)
            token = spec["token"]
            center_y = (y1 + y2) / 2
            self.canvas.create_text(
                x + w / 2,
                center_y,
                text=token,
                font=("Georgia", font_size, "bold"),
                fill="#000000",
                justify="center",
                angle=90,
            )
            self._add_spot(
                f"straight_{token}",
                f"Straight {token}",
                (x + w / 2, center_y),
                payout="35:1",
                hit_shape="rect",
                hit_coords=(x + 4, y1 + 4, x + w - 4, y2 - 4),
                has_marker=True,
            )

    def _draw_glass_swirl_background(self, table_x1, table_y1, table_x2, table_y2):
        self.canvas.create_rectangle(0, 0, self.canvas_w, self.canvas_h, fill=self._surround_color(), outline="")

    def _draw_table_frame(self, x1, y1, x2, y2):
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=self._board_felt_color(), outline="", width=0)

        # Porcelain edge and light glaze highlight.
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#0b1b3b", width=8)
        self.canvas.create_rectangle(x1 + 4, y1 + 4, x2 - 4, y2 - 4, outline="#60a5fa", width=3)
        self.canvas.create_rectangle(x1 + 8, y1 + 8, x2 - 8, y2 - 8, outline="#dbeafe", width=2)
        self.canvas.create_rectangle(x1 + 11, y1 + 11, x2 - 11, y2 - 11, outline="#1d4ed8", width=2)

    def _draw_compound_outside_label(self, cx, cy, main_text, detail_text, fill="#000000"):
        main_font = ("Georgia", 18, "bold")
        detail_font = ("Georgia", 12, "bold")
        main_metrics = tkfont.Font(family="Georgia", size=18, weight="bold")
        detail_metrics = tkfont.Font(family="Georgia", size=12, weight="bold")
        main_w = main_metrics.measure(main_text)
        detail_w = detail_metrics.measure(detail_text)
        start_x = int(cx - ((main_w + detail_w) / 2))

        self.canvas.create_text(
            start_x,
            cy,
            text=main_text,
            font=main_font,
            fill=fill,
            anchor="w",
        )
        self.canvas.create_text(
            start_x + main_w,
            cy,
            text=detail_text,
            font=detail_font,
            fill=fill,
            anchor="w",
        )

    def _draw_number_grid(self, left, top):
        for c in range(self.cols):
            for r in range(3):
                x1 = left + c * self.cell_w
                y1 = top + r * self.cell_h
                x2 = x1 + self.cell_w
                y2 = y1 + self.cell_h

                number = self._number_at(c, r)
                fill = "#b91c1c" if number in self.RED_NUMBERS else "#101010"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#d4af37", width=2)
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=str(number),
                    font=("Georgia", 26, "bold"),
                    fill="#f8fafc",
                )

                self._add_spot(
                    f"straight_{number}",
                    f"Straight {number}",
                    ((x1 + x2) / 2, (y1 + y2) / 2),
                    payout="35:1",
                    hit_shape="rect",
                    hit_coords=(x1 + 4, y1 + 4, x2 - 4, y2 - 4),
                    has_marker=True,
                )

    def _draw_column_bets(self, num_right, num_top):
        for r in range(3):
            y1, y2 = self._segmented_bounds(num_top, self.cell_h, r, 3, self.outside_box_gap)
            x1 = num_right + self.column_gap
            x2 = x1 + self.column_bet_w
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#7c3aed", outline="#d4af37", width=2)
            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=f"Col {3 - r}",
                font=("Georgia", 17, "bold"),
                fill="#000000",
                justify="center",
                angle=90,
            )

    def _draw_bottom_outside_bets(self, left, num_bottom):
        dozen_y1 = num_bottom + self.vertical_gap
        dozen_y2 = dozen_y1 + 70

        for i, text in enumerate(["Doz 1", "Doz 2", "Doz 3"]):
            x1, x2 = self._segmented_bounds(left, 4 * self.cell_w, i, 3, self.outside_box_gap)
            self.canvas.create_rectangle(x1, dozen_y1, x2, dozen_y2, fill="#d946ef", outline="#d4af37", width=2)
            self.canvas.create_text(
                (x1 + x2) / 2,
                (dozen_y1 + dozen_y2) / 2,
                text=text,
                font=("Georgia", 20, "bold"),
                fill="#000000",
            )

        even_y1 = dozen_y2 + self.vertical_gap
        even_y2 = even_y1 + 72
        labels = ["1-18", "EVEN", "RED", "BLACK", "ODD", "19-36"]

        for i, text in enumerate(labels):
            x1, x2 = self._segmented_bounds(left, 2 * self.cell_w, i, 6, self.outside_box_gap)
            fill = "#b91c1c" if text == "RED" else "#0f7a36"
            text_fill = "#000000"
            if text == "BLACK":
                fill = "#101010"
                text_fill = "#f8fafc"
            elif text == "EVEN":
                fill = "#22ff22"
            elif text == "1-18":
                fill = "#f97316"
            elif text == "19-36":
                fill = "#5b21b6"
            elif text == "ODD":
                fill = "#00FFFF"
            elif text == "RED":
                text_fill = "#f8fafc"
            self.canvas.create_rectangle(x1, even_y1, x2, even_y2, fill=fill, outline="#d4af37", width=2)
            cx = (x1 + x2) / 2
            cy = (even_y1 + even_y2) / 2
            if text == "1-18":
                self._draw_compound_outside_label(cx, cy, "Low ", "(1-18)", fill=text_fill)
            elif text == "19-36":
                self._draw_compound_outside_label(cx, cy, "High ", "(19-36)", fill=text_fill)
            else:
                self.canvas.create_text(
                    cx,
                    cy,
                    text=text,
                    font=("Georgia", 18, "bold"),
                    fill=text_fill,
                )

    def _create_inside_bet_spots(self, left, top):
        bottom = top + 3 * self.cell_h

        for c in range(self.cols - 1):
            x = left + (c + 1) * self.cell_w
            for r in range(3):
                y = top + r * self.cell_h + self.cell_h / 2
                n1 = self._number_at(c, r)
                n2 = self._number_at(c + 1, r)
                self._draw_bet_marker(x, y)
                self._add_spot(
                    f"split_h_{n1}_{n2}",
                    f"Split {min(n1, n2)}/{max(n1, n2)}",
                    (x, y),
                    payout="17:1",
                    hit_shape="oval",
                    hit_coords=(x - 11, y - 11, x + 11, y + 11),
                    has_marker=True,
                )

        for c in range(self.cols):
            x = left + c * self.cell_w + self.cell_w / 2
            for r in range(2):
                y = top + (r + 1) * self.cell_h
                n1 = self._number_at(c, r)
                n2 = self._number_at(c, r + 1)
                self._draw_bet_marker(x, y)
                self._add_spot(
                    f"split_v_{n1}_{n2}",
                    f"Split {min(n1, n2)}/{max(n1, n2)}",
                    (x, y),
                    payout="17:1",
                    hit_shape="oval",
                    hit_coords=(x - 11, y - 11, x + 11, y + 11),
                    has_marker=True,
                )

        for c in range(self.cols - 1):
            x = left + (c + 1) * self.cell_w
            for r in range(2):
                y = top + (r + 1) * self.cell_h
                nums = sorted(
                    [
                        self._number_at(c, r),
                        self._number_at(c + 1, r),
                        self._number_at(c, r + 1),
                        self._number_at(c + 1, r + 1),
                    ]
                )
                self._add_spot(
                    f"corner_{nums[0]}_{nums[1]}_{nums[2]}_{nums[3]}",
                    f"Corner {'/'.join(map(str, nums))}",
                    (x, y),
                    payout="8:1",
                    hit_shape="oval",
                    hit_coords=(x - 10, y - 10, x + 10, y + 10),
                    has_marker=True,
                )

        marker_gap_y = bottom + (self.vertical_gap / 2.0)
        for c in range(self.cols):
            x = left + c * self.cell_w + self.cell_w / 2
            nums = [self._number_at(c, r) for r in range(3)]
            self._draw_bet_marker(x, marker_gap_y, visible=True, color="#d946ef")
            self._add_spot(
                f"street_{c + 1}",
                f"Street {'/'.join(map(str, sorted(nums)))}",
                (x, marker_gap_y),
                payout="11:1",
                hit_shape="oval",
                hit_coords=(x - 13, marker_gap_y - 13, x + 13, marker_gap_y + 13),
                has_marker=True,
            )

        for c in range(self.cols - 1):
            x = left + (c + 1) * self.cell_w
            nums = sorted([self._number_at(c, r) for r in range(3)] + [self._number_at(c + 1, r) for r in range(3)])
            self._draw_bet_marker(x, marker_gap_y, visible=True, color="#7c3aed")
            self._add_spot(
                f"sixline_{c + 1}_{c + 2}",
                f"Six Line {'/'.join(map(str, nums))}",
                (x, marker_gap_y),
                payout="5:1",
                hit_shape="oval",
                hit_coords=(x - 13, marker_gap_y - 13, x + 13, marker_gap_y + 13),
                has_marker=True,
            )

        zero_x = left - self.zero_gap / 2
        self._create_zero_special_bets(top, bottom, zero_x, marker_gap_y)

    def _create_zero_special_bets(self, top, bottom, zero_x, marker_gap_y):
        if self._is_triple_zero_wheel():
            def hit_bounds(spot_id, fallback_center):
                spot = self.spots.get(spot_id)
                if spot is not None:
                    try:
                        x1, y1, x2, y2 = self.canvas.coords(spot["hit"])
                        return float(x1), float(y1), float(x2), float(y2)
                    except Exception:
                        pass
                cx, cy = fallback_center
                return float(cx - 12), float(cy - 12), float(cx + 12), float(cy + 12)

            def overlap_mid(a1, a2, b1, b2, fallback):
                lo = max(float(a1), float(b1))
                hi = min(float(a2), float(b2))
                if hi > lo:
                    return (lo + hi) / 2.0
                return float(fallback)

            p_000 = self.spots.get("straight_000", {}).get(
                "center",
                (self.zero_cell_x + self.zero_draw_w * 0.30, top + 1.50 * self.cell_h),
            )
            p_00 = self.spots.get("straight_00", {}).get(
                "center",
                (self.zero_cell_x + self.zero_draw_w * 0.72, top + 0.95 * self.cell_h),
            )
            p_0 = self.spots.get("straight_0", {}).get(
                "center",
                (self.zero_cell_x + self.zero_draw_w * 0.72, top + 2.05 * self.cell_h),
            )
            p_3 = self.spots.get("straight_3", {}).get(
                "center",
                (self.zero_cell_x + self.zero_draw_w + self.zero_gap + (self.cell_w / 2), top + 0.5 * self.cell_h),
            )
            p_2 = self.spots.get("straight_2", {}).get(
                "center",
                (self.zero_cell_x + self.zero_draw_w + self.zero_gap + (self.cell_w / 2), top + 1.5 * self.cell_h),
            )
            p_1 = self.spots.get("straight_1", {}).get(
                "center",
                (self.zero_cell_x + self.zero_draw_w + self.zero_gap + (self.cell_w / 2), top + 2.5 * self.cell_h),
            )

            b_000 = hit_bounds("straight_000", p_000)
            b_00 = hit_bounds("straight_00", p_00)
            b_0 = hit_bounds("straight_0", p_0)
            b_3 = hit_bounds("straight_3", p_3)
            b_2 = hit_bounds("straight_2", p_2)
            b_1 = hit_bounds("straight_1", p_1)

            gap_x = (b_00[2] + b_2[0]) / 2.0
            split_00_3_center = (
                gap_x,
                overlap_mid(b_00[1], b_00[3], b_3[1], b_3[3], (p_00[1] + p_3[1]) / 2.0),
            )
            split_00_2_center = (
                gap_x,
                overlap_mid(b_00[1], b_00[3], b_2[1], b_2[3], (p_00[1] + p_2[1]) / 2.0),
            )
            split_0_2_center = (
                gap_x,
                overlap_mid(b_0[1], b_0[3], b_2[1], b_2[3], (p_0[1] + p_2[1]) / 2.0),
            )
            split_0_1_center = (
                gap_x,
                overlap_mid(b_0[1], b_0[3], b_1[1], b_1[3], (p_0[1] + p_1[1]) / 2.0),
            )
            split_000_00_center = (
                (b_000[2] + b_00[0]) / 2.0,
                b_000[1] + ((b_000[3] - b_000[1]) / 4.0),
            )
            split_000_0_center = (
                (b_000[2] + b_0[0]) / 2.0,
                b_000[3] - ((b_000[3] - b_000[1]) / 4.0),
            )
            split_0_00_center = (
                overlap_mid(b_0[0], b_0[2], b_00[0], b_00[2], (p_0[0] + p_00[0]) / 2.0),
                (b_00[3] + b_0[1]) / 2.0,
            )
            y_00_0 = split_0_00_center[1]
            # Exact 3-way intersection for 0/1/2 (between rows 2 and 1 on the 0|1 gap line).
            y_trio_2 = (b_2[3] + b_1[1]) / 2.0
            y_trio_3 = (split_0_2_center[1] + split_00_2_center[1]) / 2.0
            # Exact 3-way intersection for 00/2/3 (between rows 3 and 2 on the 00|2 gap line).
            y_trio_4 = (b_3[3] + b_2[1]) / 2.0
            tri_000_00_0_center = (split_000_00_center[0], split_0_00_center[1])

            split_specs = [
                ("split_000_0", "Split 000/0", split_000_0_center),
                ("split_000_00", "Split 000/00", split_000_00_center),
                ("split_0_1", "Split 0/1", split_0_1_center),
                ("split_0_2", "Split 0/2", split_0_2_center),
                ("split_00_2", "Split 00/2", split_00_2_center),
                ("split_00_3", "Split 00/3", split_00_3_center),
            ]
            hidden_marker_spots = {"split_000_0", "split_000_00", "split_0_00", "trio_000_00_0"}
            for spot_id, label, center in split_specs:
                cx, cy = center
                self._draw_bet_marker(cx, cy, visible=(spot_id not in hidden_marker_spots), color="#2563eb")
                self._add_spot(
                    spot_id,
                    label,
                    center,
                    payout="17:1",
                    hit_shape="oval",
                    hit_coords=(cx - 11, cy - 11, cx + 11, cy + 11),
                    has_marker=True,
                )

            zero_pair_specs = [
                ("split_0_00", "Split 0/00", split_0_00_center),
            ]
            for spot_id, label, center in zero_pair_specs:
                cx, cy = center
                self._draw_bet_marker(cx, cy, visible=(spot_id not in hidden_marker_spots), color="#2563eb")
                self._add_spot(
                    spot_id,
                    label,
                    center,
                    payout="17:1",
                    hit_shape="oval",
                    hit_coords=(cx - 12, cy - 12, cx + 12, cy + 12),
                    has_marker=True,
                )

            top_line_center = ((split_0_00_center[0] + gap_x) / 2.0, y_00_0)
            self._add_spot(
                "topline_000_00_0_1_2_3",
                "Top Line 000/00/0/1/2/3",
                top_line_center,
                payout="5:1",
                hit_shape="oval",
                hit_coords=(
                    top_line_center[0] - 11,
                    top_line_center[1] - 11,
                    top_line_center[0] + 11,
                    top_line_center[1] + 11,
                ),
            )

            trio_specs = [
                ("trio_000_00_0", "Trio 000/00/0", tri_000_00_0_center),
                ("trio_0_1_2", "Trio 0/1/2", (gap_x, y_trio_2)),
                ("trio_00_0_2", "Trio 00/0/2", (gap_x, y_trio_3)),
                ("trio_00_2_3", "Trio 00/2/3", (gap_x, y_trio_4)),
            ]
            for spot_id, label, center in trio_specs:
                cx, cy = center
                self._draw_bet_marker(cx, cy, visible=(spot_id not in hidden_marker_spots), color="#d946ef")
                self._add_spot(
                    spot_id,
                    label,
                    center,
                    payout="11:1",
                    hit_shape="oval",
                    hit_coords=(cx - 12, cy - 12, cx + 12, cy + 12),
                    has_marker=True,
                )

            # Center basket on the 0|1 gap line for triple-zero.
            basket_center = (gap_x, marker_gap_y)
            self._draw_bet_marker(basket_center[0], basket_center[1], visible=True, color="#f97316")
            self._add_spot(
                "basket_000_00_0_1_2_3",
                "Basket 000/00/0/1/2/3",
                basket_center,
                payout="5:1",
                hit_shape="oval",
                hit_coords=(basket_center[0] - 13, basket_center[1] - 13, basket_center[0] + 13, basket_center[1] + 13),
                has_marker=True,
            )
            return

        zero_specs = self._zero_pocket_specs()

        # Splits between each zero pocket and the first-number column (3/2/1).
        for spec in zero_specs:
            token = spec["token"]
            for row in range(3):
                row_start = float(row)
                row_end = float(row + 1)
                overlap_start = max(spec["start"], row_start)
                overlap_end = min(spec["end"], row_end)
                if overlap_end <= overlap_start:
                    continue
                y = top + ((overlap_start + overlap_end) / 2.0) * self.cell_h
                number = self._number_at(0, row)
                self._draw_bet_marker(zero_x, y, visible=True, color="#2563eb")
                self._add_spot(
                    f"split_{token}_{number}",
                    f"Split {token}/{number}",
                    (zero_x, y),
                    payout="17:1",
                    hit_shape="oval",
                    hit_coords=(zero_x - 11, y - 11, zero_x + 11, y + 11),
                    has_marker=True,
                )

        # Splits between adjacent zero pockets.
        zero_mid_x = self.zero_cell_x + self.zero_draw_w / 2
        for idx in range(len(zero_specs) - 1):
            token_a = zero_specs[idx]["token"]
            token_b = zero_specs[idx + 1]["token"]
            y = top + zero_specs[idx]["end"] * self.cell_h
            spot_id = self._zero_pair_spot_id(token_a, token_b)
            self._draw_bet_marker(zero_mid_x, y)
            self._add_spot(
                spot_id,
                f"Split {token_a}/{token_b}",
                (zero_mid_x, y),
                payout="17:1",
                hit_shape="oval",
                hit_coords=(zero_mid_x - 12, y - 12, zero_mid_x + 12, y + 12),
                has_marker=True,
            )

        if self._is_american_wheel():
            self._add_spot(
                "topline_0_00_1_2_3",
                "Top Line 0/00/1/2/3",
                (zero_x + 34, top + 1.5 * self.cell_h),
                payout="6:1",
                hit_shape="oval",
                hit_coords=(zero_x + 24, top + 1.5 * self.cell_h - 10, zero_x + 44, top + 1.5 * self.cell_h + 10),
            )

            trio_specs = [
                ("trio_00_2_3", "Trio 00/2/3", top + 1.0 * self.cell_h),
                ("trio_0_2_00", "Trio 0/2/00", top + 1.5 * self.cell_h),
                ("trio_0_1_2", "Trio 0/1/2", top + 2.0 * self.cell_h),
            ]
            for spot_id, label, y in trio_specs:
                self._draw_bet_marker(zero_x, y, visible=True, color="#d946ef")
                self._add_spot(
                    spot_id,
                    label,
                    (zero_x, y),
                    payout="11:1",
                    hit_shape="oval",
                    hit_coords=(zero_x - 12, y - 12, zero_x + 12, y + 12),
                    has_marker=True,
                )

            basket_id = "basket_0_00_1_2_3"
            basket_label = "Basket 0/00/1/2/3"
            basket_payout = "6:1"
        else:
            trio_specs = [
                ("trio_0_2_3", "Trio 0/2/3", top + 1.0 * self.cell_h),
                ("trio_0_1_2", "Trio 0/1/2", top + 2.0 * self.cell_h),
            ]
            for spot_id, label, y in trio_specs:
                self._draw_bet_marker(zero_x, y, visible=True, color="#d946ef")
                self._add_spot(
                    spot_id,
                    label,
                    (zero_x, y),
                    payout="11:1",
                    hit_shape="oval",
                    hit_coords=(zero_x - 12, y - 12, zero_x + 12, y + 12),
                    has_marker=True,
                )

            basket_id = "basket_0_1_2_3"
            basket_label = "Basket 0/1/2/3"
            basket_payout = "8:1"

        self._draw_bet_marker(zero_x, marker_gap_y, visible=True, color="#f97316")
        self._add_spot(
            basket_id,
            basket_label,
            (zero_x, marker_gap_y),
            payout=basket_payout,
            hit_shape="oval",
            hit_coords=(zero_x - 13, marker_gap_y - 13, zero_x + 13, marker_gap_y + 13),
            has_marker=True,
        )

    def _create_outside_bet_spots(self, left, top, num_right, num_bottom):
        for r in range(3):
            y1, y2 = self._segmented_bounds(top, self.cell_h, r, 3, self.outside_box_gap)
            y = (y1 + y2) / 2
            x = num_right + self.column_gap + self.column_bet_w / 2
            label = f"Column {3 - r}"
            self._add_spot(
                f"column_{3 - r}",
                label,
                (x, y),
                payout="2:1",
                hit_shape="rect",
                hit_coords=(
                    num_right + self.column_gap + 6,
                    y1 + 6,
                    num_right + self.column_gap + self.column_bet_w - 6,
                    y2 - 6,
                ),
                has_marker=True,
            )

        dozen_y1 = num_bottom + self.vertical_gap
        dozen_y2 = dozen_y1 + 70
        for i, label in enumerate(["Doz 1", "Doz 2", "Doz 3"]):
            x1, x2 = self._segmented_bounds(left, 4 * self.cell_w, i, 3, self.outside_box_gap)
            self._add_spot(
                f"dozen_{i + 1}",
                label,
                ((x1 + x2) / 2, (dozen_y1 + dozen_y2) / 2),
                payout="2:1",
                hit_shape="rect",
                hit_coords=(x1 + 6, dozen_y1 + 6, x2 - 6, dozen_y2 - 6),
                has_marker=True,
            )

        even_y1 = dozen_y2 + self.vertical_gap
        even_y2 = even_y1 + 72
        outside_specs = [
            ("outside_1_18", "Low (1-18)"),
            ("outside_even", "EVEN"),
            ("outside_red", "RED"),
            ("outside_black", "BLACK"),
            ("outside_odd", "ODD"),
            ("outside_19_36", "High (19-36)"),
        ]
        for i, (spot_id, label) in enumerate(outside_specs):
            x1, x2 = self._segmented_bounds(left, 2 * self.cell_w, i, 6, self.outside_box_gap)
            self._add_spot(
                spot_id,
                label,
                ((x1 + x2) / 2, (even_y1 + even_y2) / 2),
                payout="1:1",
                hit_shape="rect",
                hit_coords=(x1 + 6, even_y1 + 6, x2 - 6, even_y2 - 6),
                has_marker=True,
            )

    def _add_spot(self, spot_id, label, center, payout, hit_shape, hit_coords, has_marker=False):
        if has_marker:
            cx, cy = center
            r = max(8, int(self.marker_hover_radius))
            if hit_shape != "rect":
                hit_coords = (cx - r, cy - r, cx + r, cy + r)

        if hit_shape == "rect":
            hit_id = self.canvas.create_rectangle(*hit_coords, outline="", fill="")
        else:
            hit_id = self.canvas.create_oval(*hit_coords, outline="", fill="")

        self.spots[spot_id] = {
            "label": label,
            "center": center,
            "payout": payout,
            "hit": hit_id,
        }
        if has_marker:
            self.marker_spot_ids.add(spot_id)

        self.canvas.tag_bind(hit_id, "<Button-1>", lambda _e, sid=spot_id: self._place_chip(sid))
        self.canvas.tag_bind(hit_id, "<Enter>", lambda e, sid=spot_id: self._on_spot_enter(sid, e))
        self.canvas.tag_bind(hit_id, "<Leave>", self._on_spot_leave)
        self.canvas.tag_bind(hit_id, "<Motion>", lambda e, sid=spot_id: self._on_spot_motion(sid, e))

    @staticmethod
    def _segmented_bounds(start, segment_size, index, count, gap):
        x1 = start + index * segment_size + (gap / 2 if index > 0 else 0)
        x2 = start + (index + 1) * segment_size - (gap / 2 if index < count - 1 else 0)
        return x1, x2

    def _open_call_bets_popup(self, focus_popup=True):
        if not self._is_french_wheel():
            messagebox.showinfo("French Call Bets", "Select a French wheel option to place French call bets.")
            return
        if self.call_bet_popup is not None and self.call_bet_popup.winfo_exists():
            self._position_call_bet_popup(self.call_bet_popup)
            if focus_popup:
                self.call_bet_popup.lift()
                self.call_bet_popup.focus_force()
            return

        call_bet_names = tuple(self.FRENCH_CALL_BET_OPTIONS)
        self.call_bet_name_var = tk.StringVar(value=call_bet_names[0])
        self.call_bet_amount_var = tk.StringVar(value=str(self.selected_chip.get()))
        self.call_bet_final_digit_var = tk.StringVar(value=self.FRENCH_FINALES_DIGITS[0])

        popup = tk.Toplevel(self.root)
        popup.title("French Call Bets")
        popup.configure(bg="#FFFFFF")
        popup.transient(self.root)
        self.call_bet_popup = popup

        frame = tk.Frame(popup, bg="#FFFFFF", padx=12, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Call Bet", bg="#FFFFFF", fg="#111827", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.call_bet_name_combo = ttk.Combobox(
            frame,
            textvariable=self.call_bet_name_var,
            values=call_bet_names,
            state="readonly",
            width=32,
        )
        self.call_bet_name_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.call_bet_name_combo.bind("<<ComboboxSelected>>", self._sync_call_bet_popup_fields)

        self.call_bet_final_digit_controls = []
        digit_label = tk.Label(
            frame,
            text="Final Digit",
            bg="#FFFFFF",
            fg="#111827",
            font=("Segoe UI", 10, "bold"),
        )
        digit_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        digit_combo = ttk.Combobox(
            frame,
            textvariable=self.call_bet_final_digit_var,
            values=self.FRENCH_FINALES_DIGITS,
            state="readonly",
            width=6,
        )
        digit_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.call_bet_final_digit_controls.append((digit_label, digit_combo))

        tk.Label(frame, text="Unit Amount", bg="#FFFFFF", fg="#111827", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )
        tk.Entry(frame, textvariable=self.call_bet_amount_var, width=12).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0)
        )

        tk.Label(
            frame,
            text="Amount is per unit of the selected French call bet.",
            bg="#FFFFFF",
            fg="#475569",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        buttons = tk.Frame(frame, bg="#FFFFFF")
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(12, 0))
        tk.Button(
            buttons,
            text="Add Bet",
            command=self._submit_call_bet_popup,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=3,
        ).pack(side="left")
        tk.Button(
            buttons,
            text="Close",
            command=self._close_call_bet_popup,
            bg="#e5e7eb",
            fg="#111827",
            font=("Segoe UI", 10),
            padx=10,
            pady=3,
        ).pack(side="left", padx=(8, 0))

        frame.columnconfigure(1, weight=1)
        popup.bind("<Return>", lambda _event: self._submit_call_bet_popup())
        popup.bind("<Escape>", lambda _event: self._close_call_bet_popup())
        popup.protocol("WM_DELETE_WINDOW", self._close_call_bet_popup)
        popup.resizable(False, False)
        self._sync_call_bet_popup_fields()
        self._position_call_bet_popup(popup)
        if focus_popup:
            popup.lift()
            popup.focus_force()

    def _position_call_bet_popup(self, popup):
        if popup is None or not popup.winfo_exists():
            return

        popup.update_idletasks()
        popup_w = popup.winfo_width() or popup.winfo_reqwidth()
        popup_h = popup.winfo_height() or popup.winfo_reqheight()
        anchor = self.call_bets_button if self.call_bets_button is not None else self.root
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 6
        max_x = popup.winfo_screenwidth() - popup_w - 16
        max_y = popup.winfo_screenheight() - popup_h - 48
        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))
        popup.geometry(f"+{x}+{y}")

    def _sync_call_bet_popup_fields(self, _event=None):
        selected_name = self.call_bet_name_var.get() if self.call_bet_name_var is not None else ""
        is_finales = selected_name in {self.FRENCH_FINALES_PLEINES_NAME, self.FRENCH_FINALES_A_CHEVAL_NAME}
        for digit_label, digit_combo in self.call_bet_final_digit_controls:
            if is_finales:
                digit_label.grid()
                digit_combo.grid()
            else:
                digit_label.grid_remove()
                digit_combo.grid_remove()

    def _close_call_bet_popup(self):
        if self.call_bet_popup is not None and self.call_bet_popup.winfo_exists():
            self.call_bet_popup.destroy()
        self.call_bet_popup = None
        self.call_bet_name_combo = None
        self.call_bet_name_var = None
        self.call_bet_amount_var = None
        self.call_bet_final_digit_var = None
        self.call_bet_final_digit_controls = []

    def _submit_call_bet_popup(self):
        if self.call_bet_name_var is None or self.call_bet_amount_var is None:
            return
        bet_name = self.call_bet_name_var.get().strip()
        if bet_name not in self.FRENCH_CALL_BET_OPTIONS:
            messagebox.showerror("Invalid call bet", "Choose a call bet from the dropdown list.")
            return
        unit_amount = self._safe_int(self.call_bet_amount_var.get(), 0)
        if unit_amount <= 0:
            messagebox.showerror("Invalid amount", "Enter a positive unit amount for the call bet.")
            return
        final_digit = None
        if bet_name in {self.FRENCH_FINALES_PLEINES_NAME, self.FRENCH_FINALES_A_CHEVAL_NAME}:
            final_digit = self._safe_int(self.call_bet_final_digit_var.get() if self.call_bet_final_digit_var else None, None)
            if final_digit is None or final_digit < 0 or final_digit > 9:
                messagebox.showerror("Invalid digit", "Choose a final digit from 0 to 9.")
                return
        if self._add_french_call_bet(bet_name, unit_amount, final_digit=final_digit):
            self._close_call_bet_popup()

    def _build_finales_pleines_legs(self, final_digit):
        digit = self._safe_int(final_digit, None)
        if digit is None or digit < 0 or digit > 9:
            return []
        return [{"kind": "straight", "numbers": (n,), "units": 1} for n in range(37) if n % 10 == digit]

    def _build_finales_a_cheval_legs(self, final_digit):
        digit = self._safe_int(final_digit, None)
        if digit is None or digit < 0 or digit > 9:
            return []
        starts = range(0, 37, 10) if digit == 0 else range(digit, 37, 10)
        legs = []
        for start in starts:
            second = start + 3
            if second <= 36:
                legs.append({"kind": "split", "numbers": (start, second), "units": 1})
        return legs

    def _add_french_call_bet(self, bet_name, unit_amount, final_digit=None):
        display_name = bet_name
        if bet_name == self.FRENCH_FINALES_PLEINES_NAME:
            legs = self._build_finales_pleines_legs(final_digit)
            display_name = f"Finales {final_digit}"
        elif bet_name == self.FRENCH_FINALES_A_CHEVAL_NAME:
            legs = self._build_finales_a_cheval_legs(final_digit)
            display_name = f"Finales a Cheval {final_digit}"
        else:
            legs = self.FRENCH_CALL_BETS.get(bet_name)
        if not legs:
            messagebox.showerror("Call bet unavailable", f"Unknown call bet: {bet_name}")
            return False

        target_group = self._call_bet_group_for_name(bet_name)

        placements = []
        unresolved_legs = []
        for leg in legs:
            kind = str(leg.get("kind", "")).strip().lower()
            numbers = tuple(leg.get("numbers", ()))
            units = self._safe_int(leg.get("units"), 1)
            if units <= 0:
                continue
            spot_id = self._resolve_call_bet_spot(kind, numbers)
            if spot_id is None:
                unresolved_legs.append(f"{kind} {numbers}")
                continue
            chips = self._chip_breakdown(unit_amount * units)
            if chips:
                placements.append((spot_id, chips))

        if unresolved_legs:
            details = ", ".join(unresolved_legs)
            messagebox.showerror("Call bet unavailable", f"Could not map these call bet legs: {details}")
            return False
        if not placements:
            messagebox.showerror("Call bet unavailable", "No mappable wager legs were found.")
            return False

        entry_id = self.next_call_bet_id
        self.next_call_bet_id += 1
        touched = set()

        for spot_id, chips in placements:
            sources = self._ensure_spot_source_alignment(spot_id)
            self.bets[spot_id].extend(chips)
            sources.extend([entry_id] * len(chips))
            touched.add(spot_id)

        self.call_bet_entries.append(
            {
                "id": entry_id,
                "name": display_name,
                "source_name": bet_name,
                "group": target_group,
                "unit_amount": unit_amount,
            }
        )

        for spot_id in touched:
            self._redraw_spot_stack(spot_id)
        self._update_total()
        return True

    def _resolve_call_bet_spot(self, kind, numbers):
        if kind == "straight":
            if len(numbers) != 1:
                return None
            raw_value = numbers[0]
            if str(raw_value).strip() == "00":
                token = "00"
            else:
                parsed = self._safe_int(raw_value, None)
                if parsed is None:
                    return None
                token = str(parsed)
            spot_id = f"straight_{token}"
            return spot_id if spot_id in self.spots else None

        if kind == "split":
            if len(numbers) != 2:
                return None
            target = set()
            for raw_value in numbers:
                if str(raw_value).strip() == "00":
                    target.add("00")
                else:
                    parsed = self._safe_int(raw_value, None)
                    if parsed is None:
                        return None
                    target.add(parsed)
            for spot_id in self.spots:
                if not spot_id.startswith("split_"):
                    continue
                if self._spot_numbers(spot_id) == target:
                    return spot_id
        if kind == "trio":
            if len(numbers) != 3:
                return None
            target = set()
            for raw_value in numbers:
                token = str(raw_value).strip()
                if token in {"00", "000"}:
                    target.add(token)
                    continue
                parsed = self._safe_int(raw_value, None)
                if parsed is None:
                    return None
                target.add(parsed)
            for spot_id in self.spots:
                if not spot_id.startswith("trio_"):
                    continue
                if self._spot_numbers(spot_id) == target:
                    return spot_id
        return None

    def _call_bet_amounts_by_id(self):
        totals = defaultdict(int)
        for spot_id, chips in self.bets.items():
            if not chips:
                continue
            sources = self._ensure_spot_source_alignment(spot_id)
            for chip_amount, source_id in zip(chips, sources):
                if source_id is not None:
                    totals[source_id] += chip_amount
        return totals

    def _call_bet_group_for_name(self, bet_name):
        options = tuple(self.FRENCH_CALL_BET_OPTIONS)
        try:
            idx = options.index(bet_name)
        except ValueError:
            idx = 0
        return 1 if idx < 3 else 2

    def _refresh_call_bets_list(self):
        call_bet_totals = self._call_bet_amounts_by_id()
        self.call_bet_entries = [entry for entry in self.call_bet_entries if call_bet_totals.get(entry["id"], 0) > 0]
        if self.call_bets_listbox_left is None or self.call_bets_listbox_right is None:
            self._sync_call_bets_controls()
            return

        self.call_bets_listbox_left.delete(0, tk.END)
        self.call_bets_listbox_right.delete(0, tk.END)
        self.call_bet_entry_ids_left = []
        self.call_bet_entry_ids_right = []
        for entry in self.call_bet_entries:
            amount = call_bet_totals.get(entry["id"], 0)
            if amount <= 0:
                continue
            group = entry.get("group")
            if group not in (1, 2):
                group = self._call_bet_group_for_name(entry.get("source_name", entry["name"]))
                entry["group"] = group
            display = f"{entry['name']}  ${amount:,}"
            if group == 1:
                self.call_bets_listbox_left.insert(tk.END, display)
                self.call_bet_entry_ids_left.append(entry["id"])
            else:
                self.call_bets_listbox_right.insert(tk.END, display)
                self.call_bet_entry_ids_right.append(entry["id"])
        self._sync_call_bets_controls()

    def _on_call_bet_list_click_left(self, _event=None):
        if self.call_bets_listbox_left is None:
            return
        event = _event
        index = self._listbox_index_from_event(self.call_bets_listbox_left, event)
        if index is None or index < 0 or index >= len(self.call_bet_entry_ids_left):
            return
        entry_id = self.call_bet_entry_ids_left[index]
        self.call_bets_listbox_left.selection_set(index)
        self.call_bets_listbox_left.selection_clear(0, tk.END)
        self._remove_call_bet_entry(entry_id)
        return "break"

    def _on_call_bet_list_click_right(self, _event=None):
        if self.call_bets_listbox_right is None:
            return
        event = _event
        index = self._listbox_index_from_event(self.call_bets_listbox_right, event)
        if index is None or index < 0 or index >= len(self.call_bet_entry_ids_right):
            return
        entry_id = self.call_bet_entry_ids_right[index]
        self.call_bets_listbox_right.selection_set(index)
        self.call_bets_listbox_right.selection_clear(0, tk.END)
        self._remove_call_bet_entry(entry_id)
        return "break"

    @staticmethod
    def _listbox_index_from_event(listbox, event):
        if listbox is None:
            return None
        if event is None:
            selection = listbox.curselection()
            return selection[0] if selection else None
        if event.x < 0 or event.x > listbox.winfo_width():
            return None
        index = listbox.nearest(event.y)
        if index < 0 or index >= listbox.size():
            return None
        bbox = listbox.bbox(index)
        if bbox is None:
            return None
        _, y0, _, height = bbox
        if event.y < y0 or event.y > y0 + height:
            return None
        return index

    def _remove_call_bet_entry(self, entry_id):
        touched = set()
        for spot_id in list(self.bets.keys()):
            chips = self.bets[spot_id]
            if not chips:
                continue
            sources = self._ensure_spot_source_alignment(spot_id)
            if entry_id not in sources:
                continue

            kept_chips = []
            kept_sources = []
            for chip_amount, source_id in zip(chips, sources):
                if source_id == entry_id:
                    continue
                kept_chips.append(chip_amount)
                kept_sources.append(source_id)
            self.bets[spot_id] = kept_chips
            self.bet_chip_sources[spot_id] = kept_sources
            touched.add(spot_id)

        for spot_id in touched:
            if self.bets[spot_id]:
                self._redraw_spot_stack(spot_id)
            else:
                if spot_id in self.stack_tags:
                    self.canvas.delete(self.stack_tags[spot_id])
                    self.stack_tags.pop(spot_id, None)
                self.en_prison_pending.discard(spot_id)
        self.call_bet_entries = [entry for entry in self.call_bet_entries if entry["id"] != entry_id]
        self._hide_tooltip()
        self._hide_chip_add_popup()
        self._update_total()

    def _ensure_spot_source_alignment(self, spot_id):
        chips = self.bets[spot_id]
        sources = self.bet_chip_sources[spot_id]
        if len(sources) < len(chips):
            sources.extend([None] * (len(chips) - len(sources)))
        elif len(sources) > len(chips):
            del sources[len(chips) :]
        return sources

    def _nearest_marker_spot(self, event):
        if event is None or not self.marker_spot_ids:
            return None
        x = getattr(event, "x", None)
        y = getattr(event, "y", None)
        if x is None or y is None:
            x_root = getattr(event, "x_root", None)
            y_root = getattr(event, "y_root", None)
            if x_root is not None and y_root is not None:
                x = self.canvas.canvasx(x_root - self.canvas.winfo_rootx())
                y = self.canvas.canvasy(y_root - self.canvas.winfo_rooty())
        if x is None or y is None:
            return None

        radius_sq = float(self.marker_hover_radius) * float(self.marker_hover_radius)
        best_spot = None
        best_dist_sq = None
        for spot_id in self.marker_spot_ids:
            if spot_id not in self.spots:
                continue
            cx, cy = self.spots[spot_id]["center"]
            dx = float(x) - float(cx)
            dy = float(y) - float(cy)
            dist_sq = dx * dx + dy * dy
            if dist_sq > radius_sq:
                continue
            if best_dist_sq is None or dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_spot = spot_id
        return best_spot

    def _resolve_empty_hover_spot(self, spot_id, event):
        if spot_id in self.marker_spot_ids:
            return spot_id
        return self._nearest_marker_spot(event)

    def _cancel_hover_popup_schedule(self):
        if self.hover_popup_after_id is not None:
            try:
                self.root.after_cancel(self.hover_popup_after_id)
            except tk.TclError:
                pass
            self.hover_popup_after_id = None
        self.hover_popup_pending_spot_id = None

    def _schedule_hover_popup(self, spot_id, callback):
        self._cancel_hover_popup_schedule()
        delay = self._popup_delay_ms()
        if delay <= 0:
            callback()
            return

        self.hover_popup_pending_spot_id = spot_id

        def _run():
            self.hover_popup_after_id = None
            if self.hover_popup_pending_spot_id != spot_id:
                return
            callback()

        self.hover_popup_after_id = self.root.after(delay, _run)

    def _show_marker_label_popup(self, spot_id):
        if not self._popup_enabled():
            self._hide_tooltip()
            self._hide_chip_add_popup()
            return
        if spot_id not in self.spots:
            return
        if self.marker_popup_spot_id == spot_id and self.canvas.find_withtag("chip_add_popup"):
            return
        popup_text = self._format_hover_popup_text(spot_id)
        self._schedule_hover_popup(
            spot_id,
            lambda sid=spot_id, text=popup_text: self._show_chip_add_popup(
                sid,
                popup_text=text,
                keep_tooltip=False,
                duration_ms=None,
            ),
        )
        self.marker_popup_spot_id = spot_id

    def _format_hover_popup_text(self, spot_id, spot_total=None):
        if spot_id not in self.spots:
            return ""
        display_name = self.spot_hover_display_names.get(spot_id, self.spots[spot_id]["label"])
        if spot_total is None or spot_total <= 0:
            first_line = f"{display_name} ({self.spots[spot_id]['payout']})"
        else:
            first_line = f"{display_name}  ${spot_total:,}"
        members = self._display_members_text(spot_id)
        if members:
            return f"{first_line}\n{{ {members} }}"
        return first_line

    def _place_chip(self, spot_id):
        chip_amount = self.selected_chip.get()
        self.bets[spot_id].append(chip_amount)
        self.bet_chip_sources[spot_id].append(None)
        self._redraw_spot_stack(spot_id)
        self._update_total()
        self.hover_popup_until_motion = False
        spot_total = sum(self.bets[spot_id])
        self._show_chip_add_popup(spot_id, popup_text=f"${spot_total:,}", duration_ms=500)

    def _on_spot_enter(self, spot_id, event):
        if not self._popup_enabled():
            self._cancel_hover_popup_schedule()
            self._hide_tooltip()
            self._hide_chip_add_popup()
            return
        self._cancel_hover_popup_schedule()
        spot_total = sum(self.bets[spot_id])
        if spot_total <= 0:
            hover_spot = self._resolve_empty_hover_spot(spot_id, event)
            if hover_spot is not None:
                spot_id = hover_spot
                spot_total = sum(self.bets[spot_id])

        if spot_total > 0:
            self.marker_popup_spot_id = None
            self.hover_popup_until_motion = True
            self.hover_popup_origin = (event.x_root, event.y_root)
            popup_text = self._format_hover_popup_text(spot_id, spot_total=spot_total)
            self._schedule_hover_popup(
                spot_id,
                lambda sid=spot_id, text=popup_text: self._show_chip_add_popup(
                    sid,
                    popup_text=text,
                    keep_tooltip=False,
                    duration_ms=None,
                ),
            )
            return
        self.hover_popup_until_motion = False
        self.hover_popup_origin = None
        if spot_id in self.marker_spot_ids:
            self._show_marker_label_popup(spot_id)
        else:
            self._hide_tooltip()
            self._hide_chip_add_popup()

    def _on_spot_motion(self, spot_id, event):
        if not self._popup_enabled():
            self._cancel_hover_popup_schedule()
            self._hide_tooltip()
            self._hide_chip_add_popup()
            return
        if self.hover_popup_until_motion:
            if self.hover_popup_origin is not None:
                dx = abs(event.x_root - self.hover_popup_origin[0])
                dy = abs(event.y_root - self.hover_popup_origin[1])
                if dx < 3 and dy < 3:
                    # Keep the hover popup visible until the user actually moves the mouse.
                    return
            self.hover_popup_until_motion = False
            self.hover_popup_origin = None
            self._cancel_hover_popup_schedule()
            self._hide_chip_add_popup()
        spot_total = sum(self.bets[spot_id])
        if spot_total <= 0:
            hover_spot = self._resolve_empty_hover_spot(spot_id, event)
            if hover_spot is not None:
                spot_id = hover_spot
                spot_total = sum(self.bets[spot_id])

        if spot_total > 0:
            self.marker_popup_spot_id = None
            self._cancel_hover_popup_schedule()
            self._show_spot_tooltip(spot_id, event)
        else:
            if spot_id in self.marker_spot_ids:
                self._show_marker_label_popup(spot_id)
            else:
                self._hide_tooltip()
                self._hide_chip_add_popup()

    def _on_canvas_motion_chip_hover_fallback(self, event):
        if not hasattr(self, "canvas") or self.canvas is None:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        spot_id = self._chip_spot_from_canvas_point(x, y)
        if spot_id is None:
            if self.chip_hover_fallback_spot_id is not None:
                self.chip_hover_fallback_spot_id = None
                self._on_spot_leave(event)
            return
        if self.chip_hover_fallback_spot_id != spot_id:
            self.chip_hover_fallback_spot_id = spot_id
            self._on_spot_enter(spot_id, event)
        else:
            self._on_spot_motion(spot_id, event)

    def _on_canvas_leave_chip_hover_fallback(self, event):
        if self.chip_hover_fallback_spot_id is not None:
            self.chip_hover_fallback_spot_id = None
        self._on_spot_leave(event)

    def _chip_spot_from_canvas_point(self, x, y):
        radius = float(self.placed_chip_radius)
        radius_sq = radius * radius
        best_spot = None
        best_dist_sq = None
        for spot_id, chips in self.bets.items():
            if not chips or spot_id not in self.spots:
                continue
            cx, cy = self.spots[spot_id]["center"]
            visible_count = min(len(chips), 5)
            for idx in range(visible_count):
                chip_y = float(cy) - float(idx * 3)
                dx = float(x) - float(cx)
                dy = float(y) - chip_y
                dist_sq = dx * dx + dy * dy
                if dist_sq > radius_sq:
                    continue
                if best_dist_sq is None or dist_sq < best_dist_sq:
                    best_dist_sq = dist_sq
                    best_spot = spot_id
                break
        return best_spot

    def _pointer_canvas_point(self):
        if not hasattr(self, "canvas") or self.canvas is None:
            return None
        try:
            px = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
            py = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
        except tk.TclError:
            return None
        if px < 0 or py < 0 or px > self.canvas.winfo_width() or py > self.canvas.winfo_height():
            return None
        return (self.canvas.canvasx(px), self.canvas.canvasy(py))

    def _on_spot_leave(self, _event=None):
        pointer = self._pointer_canvas_point()
        if pointer is not None:
            hover_chip_spot = self._chip_spot_from_canvas_point(pointer[0], pointer[1])
            if hover_chip_spot is not None:
                self.chip_hover_fallback_spot_id = hover_chip_spot
                return
        self.chip_hover_fallback_spot_id = None
        self._cancel_hover_popup_schedule()
        self.hover_popup_until_motion = False
        self.hover_popup_origin = None
        self.marker_popup_spot_id = None
        self._hide_tooltip()
        self._hide_chip_add_popup()

    def _redraw_spot_stack(self, spot_id):
        if spot_id in self.stack_tags:
            self.canvas.delete(self.stack_tags[spot_id])

        chips = list(self.bets[spot_id])
        if not chips:
            return

        x, y = self.spots[spot_id]["center"]
        stack_tag = f"stack_{spot_id}"
        self.stack_tags[spot_id] = stack_tag

        # Render at most 5 chips while preserving the full wager total in tooltip/total.
        visible_chips = chips[-5:]
        for i, denom in enumerate(visible_chips):
            stack_y = y - i * 3
            self._draw_chip(
                self.canvas,
                x,
                stack_y,
                self.placed_chip_radius,
                denom,
                top_label=False,
                extra_tags=(stack_tag,),
            )

        self.canvas.tag_bind(stack_tag, "<Button-1>", lambda _e, sid=spot_id: self._place_chip(sid))
        self.canvas.tag_bind(stack_tag, "<Button-3>", lambda _e, sid=spot_id: self._remove_last_chip(sid))
        self.canvas.tag_bind(stack_tag, "<Enter>", lambda e, sid=spot_id: self._on_spot_enter(sid, e))
        self.canvas.tag_bind(stack_tag, "<Motion>", lambda e, sid=spot_id: self._on_spot_motion(sid, e))
        self.canvas.tag_bind(stack_tag, "<Leave>", self._on_spot_leave)

    def _show_spot_tooltip(self, spot_id, event):
        if not self._popup_enabled():
            self._hide_tooltip()
            return
        if spot_id not in self.spots:
            return
        spot_total = sum(self.bets[spot_id])
        display_name = self.spot_hover_display_names.get(spot_id, self.spots[spot_id]["label"])
        header = f"{display_name} ({self.spots[spot_id]['payout']})"

        if spot_total > 0:
            if self._popup_mode() == "compact":
                text = f"{header}\nBet: ${spot_total:,}"
            else:
                text = (
                    f"{header}\n"
                    f"Bet: ${spot_total:,}\n"
                    f"Click adds: +${self.selected_chip.get():,}"
                )
        else:
            text = header
        self.tooltip.configure(text=text)

        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        local_x = event.x_root - root_x + 14
        local_y = event.y_root - root_y + 14
        self.tooltip.place(x=local_x, y=local_y)

    def _hide_tooltip(self):
        self.tooltip.place_forget()

    def _show_chip_add_popup(self, spot_id, chip_amount=None, popup_text=None, keep_tooltip=False, duration_ms=500):
        if not self._popup_enabled():
            return
        if spot_id not in self.spots:
            return
        if popup_text is None:
            if chip_amount is None:
                return
            popup_text = f"+${chip_amount:,} added"

        if not keep_tooltip:
            self._hide_tooltip()
        self._hide_chip_add_popup()
        spot_x, spot_y = self.spots[spot_id]["center"]
        popup_y = int(spot_y - (self.placed_chip_radius + 16))

        font_size = 24 if str(spot_id).startswith("straight_") else 11
        popup_font = ("Segoe UI", font_size, "bold")
        text_ids = []
        odds_match = re.match(r"^(.*?)(\s*\(\d+:\d+\))$", str(popup_text))
        if odds_match:
            label_text = odds_match.group(1)
            odds_text = odds_match.group(2)
            label_fill = self._popup_text_color()
            if str(spot_id).startswith("straight_"):
                label_fill = self._straight_popup_label_color(spot_id)
            elif str(spot_id).startswith(("column_", "dozen_", "outside_")):
                label_fill = self._outside_popup_label_color(spot_id)
            font_metrics = tkfont.Font(family="Segoe UI", size=font_size, weight="bold")
            label_w = font_metrics.measure(label_text)
            odds_w = font_metrics.measure(odds_text)
            start_x = int(spot_x - ((label_w + odds_w) / 2))

            if label_text:
                text_ids.append(
                    self.canvas.create_text(
                        start_x,
                        popup_y,
                        text=label_text,
                        anchor="w",
                        fill=label_fill,
                        font=popup_font,
                        state="disabled",
                        tags=("chip_add_popup",),
                    )
                )
            text_ids.append(
                self.canvas.create_text(
                    start_x + label_w,
                    popup_y,
                    text=odds_text,
                    anchor="w",
                    fill="#2563eb",
                    font=popup_font,
                    state="disabled",
                    tags=("chip_add_popup",),
                )
            )
        else:
            text_ids.append(
                self.canvas.create_text(
                    spot_x,
                    popup_y,
                    text=popup_text,
                    fill=self._popup_text_color(),
                    font=popup_font,
                    justify="center",
                    state="disabled",
                    tags=("chip_add_popup",),
                )
            )

        bboxes = [self.canvas.bbox(text_id) for text_id in text_ids]
        bboxes = [bbox for bbox in bboxes if bbox is not None]
        bbox = None
        if bboxes:
            bbox = (
                min(b[0] for b in bboxes),
                min(b[1] for b in bboxes),
                max(b[2] for b in bboxes),
                max(b[3] for b in bboxes),
            )
        if bbox is not None:
            rect_id = self.canvas.create_rectangle(
                bbox[0] - 6,
                bbox[1] - 3,
                bbox[2] + 6,
                bbox[3] + 3,
                fill=self._popup_background_color(),
                outline=self._popup_border_color(),
                width=1,
                state="disabled",
                tags=("chip_add_popup",),
            )
            for text_id in text_ids:
                self.canvas.tag_raise(text_id, rect_id)

        if duration_ms is not None and duration_ms > 0:
            self.chip_add_popup_after_id = self.root.after(duration_ms, self._expire_chip_add_popup)

    def _expire_chip_add_popup(self):
        self.chip_add_popup_after_id = None
        self.canvas.delete("chip_add_popup")

    def _hide_chip_add_popup(self):
        self._cancel_hover_popup_schedule()
        if self.chip_add_popup_after_id is not None:
            self.root.after_cancel(self.chip_add_popup_after_id)
            self.chip_add_popup_after_id = None
        self.marker_popup_spot_id = None
        self.canvas.delete("chip_add_popup")

    def _remove_last_chip(self, spot_id):
        chips = self.bets.get(spot_id)
        if not chips:
            return

        sources = self._ensure_spot_source_alignment(spot_id)
        chips.pop()
        if sources:
            sources.pop()
        if chips:
            self._redraw_spot_stack(spot_id)
        else:
            if spot_id in self.stack_tags:
                self.canvas.delete(self.stack_tags[spot_id])
                self.stack_tags.pop(spot_id, None)
            self.bets[spot_id] = []
            self.bet_chip_sources[spot_id] = []
            self._hide_tooltip()
            self._hide_chip_add_popup()
        self._update_total()

    def _clear_spot_bet(self, spot_id):
        if spot_id in self.stack_tags:
            self.canvas.delete(self.stack_tags[spot_id])
            self.stack_tags.pop(spot_id, None)
        self.bets[spot_id] = []
        self.bet_chip_sources[spot_id] = []
        self.en_prison_pending.discard(spot_id)
        self._hide_tooltip()
        self._hide_chip_add_popup()
        self._update_total()

    def _clear_bets(self):
        for tag in self.stack_tags.values():
            self.canvas.delete(tag)
        self.bets = defaultdict(list)
        self.bet_chip_sources = defaultdict(list)
        self.stack_tags.clear()
        self.en_prison_pending = set()
        self.call_bet_entries = []
        self._hide_tooltip()
        self._hide_chip_add_popup()
        self._update_total()

    def _update_total(self):
        total = sum(sum(v) for v in self.bets.values())
        self.total_var.set(f"Total Bets: ${total:,}")
        self._refresh_call_bets_list()
        self._refresh_payout_chart()

    def _set_selected_chip(self, denom):
        self.selected_chip.set(denom)
        self._refresh_legend_highlight()
        self._refresh_payout_chart()

    def _draw_bet_marker(self, x, y, radius=4, visible=False, color="#f1f5f9"):
        if not visible:
            return
        self.canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline="#f8fafc",
            width=1,
            fill=color,
        )

    def _refresh_legend_highlight(self):
        current = self.selected_chip.get()
        for denom, canvas in self.legend_canvases.items():
            if denom == current:
                canvas.configure(highlightthickness=3, highlightbackground="#fde047")
            else:
                canvas.configure(highlightthickness=1, highlightbackground="#374151")

    def _draw_chip(self, canvas, cx, cy, radius, denom, top_label=False, extra_tags=()):
        fill, edge, text_color, accent = self.CHIP_COLORS[denom]
        tags = tuple(extra_tags) if extra_tags else ()

        canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill=edge,
            outline="#111827",
            width=1,
            tags=tags,
        )
        canvas.create_oval(
            cx - radius + 3,
            cy - radius + 3,
            cx + radius - 3,
            cy + radius - 3,
            fill=fill,
            outline=accent,
            width=2,
            tags=tags,
        )

        for dx, dy in [(0, -radius + 3), (0, radius - 3), (-radius + 3, 0), (radius - 3, 0)]:
            canvas.create_oval(
                cx + dx - 2,
                cy + dy - 2,
                cx + dx + 2,
                cy + dy + 2,
                fill="#f8fafc",
                outline="",
                tags=tags,
            )

        label = f"${denom if denom < 1000 else '1K'}"
        font_size = 9 if top_label else 7
        canvas.create_text(
            cx,
            cy,
            text=label,
            fill=text_color,
            font=("Segoe UI", font_size, "bold"),
            tags=tags,
        )

    @staticmethod
    def _number_at(col, row):
        return 3 * (col + 1) - row


if __name__ == "__main__":
    root = tk.Tk()
    root.state("zoomed")
    app = RouletteBoardApp(root)
    root.mainloop()




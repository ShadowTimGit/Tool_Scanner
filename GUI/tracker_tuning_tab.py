# GUI/tracker_tuning_tab.py

import os
from pathlib import Path

import yaml

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QToolTip,
)

from GUI.gui_controls import XCheckBox

from PySide6.QtGui import QFont

from GUI.appearance_controller import (
    CONTROL_BG,
    PANEL_BG,
    CARD_BG,
    INPUT_BG,
    BORDER_COLOR,
    TEXT_COLOR,
    MUTED_TEXT,
    ACCENT_COLOR,
    ACCENT_HOVER,
    DANGER_COLOR,
    DANGER_HOVER,
    WHITE_TEXT,
    BLACK_TEXT,
    INVERTED_TEXT,
)



class TrackerTuningTabMixin:

    # =========================================================
    # Tracker Configuration
    # =========================================================

    TRACKER_CONFIG = (
        "Camera/bytetrack_tools.yaml"
    )

    TRACKER_SLIDER_CONFIG = {
        "track_high_thresh": {
            "label": "Track High Threshold",
            "description": (
                "Controls how confident a detection must be to become a strong track. "
                "Higher values reduce weak detections but may cause missed tracks."
            ),
            "minimum": 0,
            "maximum": 100,
            "scale": 100,
            "decimals": 2,
        },

        "track_low_thresh": {
            "label": "Track Low Threshold",
            "description": (
                "Controls the minimum detection confidence considered when recovering "
                "or continuing an existing track. Higher values reduce weak matches."
            ),
            "minimum": 0,
            "maximum": 100,
            "scale": 100,
            "decimals": 2,
        },

        "new_track_thresh": {
            "label": "New Track Threshold",
            "description": (
                "Controls how confident a detection must be before starting a new track. "
                "Higher values prevent more false or short-lived tracks."
            ),
            "minimum": 0,
            "maximum": 100,
            "scale": 100,
            "decimals": 2,
        },

        "track_buffer": {
            "label": "Track Buffer",
            "description": (
                "Controls how long a lost track is kept alive before being removed. "
                "Higher values help maintain identity through brief missed detections."
            ),
            "minimum": 1,
            "maximum": 300,
            "scale": 1,
            "decimals": 0,
        },

        "match_thresh": {
            "label": "Match Threshold",
            "description": (
                "Controls how strictly detections must match existing tracks. "
                "Higher values make association stricter and can reduce identity switches."
            ),
            "minimum": 0,
            "maximum": 100,
            "scale": 100,
            "decimals": 2,
        },
    }

    TRACKER_DEFAULT_CONFIG = (
        "Camera/bytetrack_yaml_default.yaml"
    )

    DEFAULT_TRACKER_SETTINGS = {
        "track_high_thresh": 0.60,
        "track_low_thresh": 0.10,
        "new_track_thresh": 0.50,
        "track_buffer": 50,
        "match_thresh": 0.65,
        "fuse_score": True,
    }

    def _get_color(self, color):
        if isinstance(color, tuple):
            mode = getattr(
                self,
                "appearance_mode",
                "Dark",
            )

            if mode == "Light":
                return color[0]

            return color[1]

        return color

    # =========================================================
    # Create Tracker Tab
    # =========================================================

    def create_tracker_tuning_tab(
        self,
        parent,
    ):
        """
        Create the ByteTrack tuning UI.

        parent should be the QWidget added to the right-panel
        QTabWidget.
        """

        self.tracker_tuning_tab = parent

        QToolTip.setFont(
            QFont(
                "Arial",
                12,
                QFont.Bold,
            )
        )

        self._ensure_tracker_config_files()

        self._tracker_settings = (
            self._load_tracker_settings()
        )

        layout = QVBoxLayout(
            parent
        )

        layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        layout.setSpacing(
            8
        )

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------

        title = QLabel(
            "ByteTrack Tuning"
        )

        self._style_label(
            title,
            TEXT_COLOR,
            size=14,
            bold=True,
        )

        layout.addWidget(
            title
        )

        description = QLabel(
            "Adjust tracking parameters while the camera is running."
        )

        description.setWordWrap(
            True
        )

        self._style_label(
            description,
            MUTED_TEXT,
            size=14,
            bold=False,
        )

        layout.addWidget(
            description
        )

        # ---------------------------------------------------------
        # Settings Card
        # ---------------------------------------------------------

        settings_frame = QFrame(
            parent
        )

        self._style_frame(
            settings_frame,
            CARD_BG,
            BORDER_COLOR,
            radius=8,
        )

        settings_layout = QVBoxLayout(
            settings_frame
        )

        settings_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        settings_layout.setSpacing(
            10
        )

        self._tracker_sliders = {}

        for name, config in (
            self.TRACKER_SLIDER_CONFIG.items()
        ):

            self._create_tracker_slider(
                settings_layout,
                name,
                config,
            )

        # ---------------------------------------------------------
        # Fuse Score
        # ---------------------------------------------------------

        fuse_row = QHBoxLayout()

        fuse_label = QLabel(
            "Fuse Score"
        )

        self._style_label(
            fuse_label,
            TEXT_COLOR,
            size=14,
            bold=True,
        )

        fuse_row.addWidget(
            fuse_label
        )

        fuse_row.addStretch()

        self.tracker_fuse_score_checkbox = XCheckBox()

        self.tracker_fuse_score_checkbox.setChecked(
            bool(
                self._tracker_settings.get(
                    "fuse_score",
                    True,
                )
            )
        )

        self._style_tracker_checkbox(
            self.tracker_fuse_score_checkbox
        )

        self.tracker_fuse_score_checkbox.toggled.connect(
            self._on_fuse_score_changed
        )

        fuse_row.addWidget(
            self.tracker_fuse_score_checkbox
        )

        settings_layout.addLayout(
            fuse_row
        )

        layout.addWidget(
            settings_frame
        )

        # ---------------------------------------------------------
        # Status
        # ---------------------------------------------------------

        self.tracker_status_label = QLabel(
            "Changes apply immediately."
        )

        self.tracker_status_label.setWordWrap(
            True
        )

        self._style_label(
            self.tracker_status_label,
            MUTED_TEXT,
            size=14,
            bold=False,
        )

        layout.addWidget(
            self.tracker_status_label
        )

        # =========================================================
        # Buttons
        # =========================================================

        button_frame = QFrame(
            parent
        )

        self._style_frame(
            button_frame,
            CARD_BG,
            BORDER_COLOR,
            radius=8,
        )

        button_layout = QVBoxLayout(
            button_frame
        )

        button_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        button_layout.setSpacing(
            6
        )

        # self.tracker_reset_button = QPushButton(
        #     "Reset Tracker"
        # )

        # self.tracker_reset_button.setFixedHeight(
        #     34
        # )

        # self._style_tracker_button(
        #     self.tracker_reset_button
        # )

        # self.tracker_reset_button.clicked.connect(
        #     self._reset_tracker_runtime
        # )

        # button_layout.addWidget(
        #     self.tracker_reset_button
        # )

        self.tracker_defaults_button = QPushButton(
            "Load Saved Defaults"
        )

        self.tracker_defaults_button.setFixedHeight(
            34
        )

        self._style_tracker_button(
            self.tracker_defaults_button
        )

        self.tracker_defaults_button.clicked.connect(
            self._load_tracker_defaults
        )

        button_layout.addWidget(
            self.tracker_defaults_button
        )

        self.tracker_overwrite_defaults_button = QPushButton(
            "Save Current Settings as Defaults"
        )

        self.tracker_overwrite_defaults_button.setFixedHeight(
            34
        )

        self._style_tracker_button(
            self.tracker_overwrite_defaults_button
        )

        self.tracker_overwrite_defaults_button.clicked.connect(
            self._save_current_as_tracker_defaults
        )

        button_layout.addWidget(
            self.tracker_overwrite_defaults_button
        )

        self.tracker_reset_defaults_button = QPushButton(
            "Reset Defaults to Factory Values"
        )

        self.tracker_reset_defaults_button.setFixedHeight(
            34
        )

        self._style_tracker_button(
            self.tracker_reset_defaults_button
        )

        self.tracker_reset_defaults_button.clicked.connect(
            self._reset_tracker_defaults_to_factory
        )

        button_layout.addWidget(
            self.tracker_reset_defaults_button
        )

        layout.addWidget(
            button_frame
        )

        layout.addStretch()

    # =========================================================
    # Slider
    # =========================================================

    def _create_tracker_slider(
        self,
        layout,
        name,
        config,
    ):
        """
        Create one labeled tracker slider.
        """

        row = QFrame()

        self._style_frame(
            row,
            PANEL_BG,
            BORDER_COLOR,
            radius=6,
        )

        row_layout = QVBoxLayout(
            row
        )

        row_layout.setContentsMargins(
            8,
            6,
            8,
            6,
        )

        row_layout.setSpacing(
            3
        )

        # ---------------------------------------------------------
        # Label row
        # ---------------------------------------------------------

        label_row = QHBoxLayout()

        label = QLabel(
            config["label"]
        )

        self._style_label(
            label,
            TEXT_COLOR,
            size=14,
            bold=True,
        )

        label_row.addWidget(
            label
        )

        label_row.addStretch()

        value_label = QLabel()

        value_label.setMinimumWidth(
            48
        )

        value_label.setAlignment(
            Qt.AlignRight |
            Qt.AlignVCenter
        )

        self._style_label(
            value_label,
            ACCENT_COLOR,
            size=14,
            bold=True,
        )

        label_row.addWidget(
            value_label
        )

        row_layout.addLayout(
            label_row
        )

        # ---------------------------------------------------------
        # Slider
        # ---------------------------------------------------------

        slider = QSlider(
            Qt.Horizontal
        )

        slider.setMinimum(
            config["minimum"]
        )

        slider.setMaximum(
            config["maximum"]
        )

        slider.setSingleStep(
            1
        )

        slider.setPageStep(
            5
        )

        current_value = self._tracker_settings.get(
            name,
            0,
        )

        slider_value = self._tracker_value_to_slider(
            name,
            current_value,
        )

        slider.setValue(
            slider_value
        )

        self._style_tracker_slider(
            slider
        )

        slider.valueChanged.connect(
            lambda value,
            setting_name=name:
            self._on_tracker_slider_changed(
                setting_name,
                value,
            )
        )

        row_layout.addWidget(
            slider
        )

        self._tracker_sliders[name] = {
            "slider": slider,
            "value_label": value_label,
            "config": config,
        }

        self._update_tracker_slider_label(
            name
        )

        layout.addWidget(
            row
        )

        row.setToolTip(
            config.get(
                "description",
                "",
            )
        )

    # =========================================================
    # Slider Value Conversion
    # =========================================================

    def _tracker_value_to_slider(
        self,
        name,
        value,
    ):
        config = self.TRACKER_SLIDER_CONFIG[
            name
        ]

        scale = config.get(
            "scale",
            1,
        )

        try:
            value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            value = 0.0

        slider_value = int(
            round(
                value * scale
            )
        )

        return max(
            config["minimum"],
            min(
                config["maximum"],
                slider_value,
            ),
        )

    def _tracker_slider_to_value(
        self,
        name,
        slider_value,
    ):
        config = self.TRACKER_SLIDER_CONFIG[
            name
        ]

        scale = config.get(
            "scale",
            1,
        )

        value = (
            float(slider_value)
            / float(scale)
        )

        if config.get(
            "decimals",
            0,
        ) == 0:

            return int(
                round(value)
            )

        return round(
            value,
            config["decimals"],
        )

    # =========================================================
    # Slider Label
    # =========================================================

    def _update_tracker_slider_label(
        self,
        name,
    ):
        control = self._tracker_sliders.get(
            name
        )

        if control is None:
            return

        slider = control["slider"]
        label = control["value_label"]
        config = control["config"]

        value = self._tracker_slider_to_value(
            name,
            slider.value(),
        )

        decimals = config.get(
            "decimals",
            0,
        )

        if decimals == 0:
            label.setText(
                str(
                    int(value)
                )
            )

        else:
            label.setText(
                f"{value:.{decimals}f}"
            )

    # =========================================================
    # Slider Changed
    # =========================================================

    def _on_tracker_slider_changed(
        self,
        name,
        slider_value,
    ):
        value = self._tracker_slider_to_value(
            name,
            slider_value,
        )

        self._tracker_settings[name] = value

        self._update_tracker_slider_label(
            name
        )

        self._apply_tracker_setting(
            name,
            value,
        )

        self._save_tracker_settings(
            show_status=False,
            reset_tracker=True,
        )

    # =========================================================
    # Fuse Score
    # =========================================================

    def _on_fuse_score_changed(
        self,
        checked,
    ):
        self._tracker_settings[
            "fuse_score"
        ] = bool(
            checked
        )

        self._apply_tracker_setting(
            "fuse_score",
            bool(
                checked
            ),
        )

        self._save_tracker_settings(
            show_status=False,
            reset_tracker=True,
        )

    # =========================================================
    # Runtime Apply
    # =========================================================

    def _apply_tracker_setting(self, name, value):
        self._tracker_settings[name] = value

        if self.camera is not None:
            self.camera.set_tracker_setting(
                name,
                value,
            )

            self.tracker_status_label.setText(
                "Tracker settings applied"
            )
        else:
            self.tracker_status_label.setText(
                "Tracker hook not connected"
            )

    # =========================================================
    # Reset Tracker
    # =========================================================

    def _reset_tracker_runtime(self):
        if self.camera is not None:
            self.camera.reset_tracker()

            self.tracker_status_label.setText(
                "Tracker reset"
            )
        else:
            self.tracker_status_label.setText(
                "Tracker hook not connected"
            )


    # =========================================================
    # Load YAML
    # =========================================================

    def _get_tracker_config_path(
        self,
        default=False,
    ):
        """
        Resolve the tracker YAML relative to the project
        working directory.
        """

        config = (
            self.TRACKER_DEFAULT_CONFIG
            if default
            else self.TRACKER_CONFIG
        )

        path = Path(config)

        if path.is_absolute():
            return path

        return Path(os.getcwd()) / path


    def _load_tracker_settings(
        self,
    ):
        """
        Load the current tracker values from the active YAML.

        Missing values fall back to the default YAML.
        """

        default_settings = self._load_tracker_yaml(
            self._get_tracker_config_path(
                default=True
            )
        )

        current_settings = self._load_tracker_yaml(
            self._get_tracker_config_path()
        )

        settings = dict(
            default_settings
        )

        settings.update(
            current_settings
        )

        return settings

    def _load_tracker_yaml(
        self,
        path,
    ):
        """
        Load supported tracker settings from a YAML file.
        """

        settings = {}

        if not path.exists():
            return settings

        try:

            with path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = yaml.safe_load(
                    file
                )

            if not isinstance(
                data,
                dict,
            ):
                return settings

            for name in (
                "track_high_thresh",
                "track_low_thresh",
                "new_track_thresh",
                "track_buffer",
                "match_thresh",
                "fuse_score",
            ):

                if name in data:
                    settings[name] = data[name]

        except Exception as error:

            print(
                "[TrackerTuning] "
                f"Could not load YAML {path}: {error}"
            )

        return settings

    # =========================================================
    # Restore YAML Defaults
    # =========================================================

    def _load_tracker_defaults(
        self,
    ):
        """
        Load the current bytetrack_yaml_default.yaml into the UI
        and runtime tracker.

        The active bytetrack_tools.yaml is not modified.
        """

        default_path = self._get_tracker_config_path(
            default=True
        )

        default_settings = self._load_tracker_yaml(
            default_path
        )

        if not default_settings:
            self.tracker_status_label.setText(
                "Could not load tracker default YAML."
            )
            return

        self._tracker_settings = dict(
            default_settings
        )

        # ---------------------------------------------------------
        # Sliders
        # ---------------------------------------------------------

        for name, control in (
            self._tracker_sliders.items()
        ):

            if name not in self._tracker_settings:
                continue

            slider = control["slider"]

            slider.blockSignals(True)

            slider.setValue(
                self._tracker_value_to_slider(
                    name,
                    self._tracker_settings[name],
                )
            )

            slider.blockSignals(False)

            self._update_tracker_slider_label(
                name
            )

        # ---------------------------------------------------------
        # Fuse score
        # ---------------------------------------------------------

        if "fuse_score" in self._tracker_settings:

            self.tracker_fuse_score_checkbox.blockSignals(
                True
            )

            self.tracker_fuse_score_checkbox.setChecked(
                bool(
                    self._tracker_settings[
                        "fuse_score"
                    ]
                )
            )

            self.tracker_fuse_score_checkbox.blockSignals(
                False
            )

        # ---------------------------------------------------------
        # Apply runtime values
        # ---------------------------------------------------------

        for name, value in (
            self._tracker_settings.items()
        ):

            self._apply_tracker_setting(
                name,
                value,
            )

        if self.camera is not None:
            self.camera.reset_tracker()

            self.tracker_status_label.setText(
                "YAML defaults restored and tracker reset."
            )

        else:
            self.tracker_status_label.setText(
                "YAML defaults loaded. Tracker hook not connected."
            )

    def _ensure_tracker_config_files(
        self,
    ):
        """
        Ensure both tracker YAML files exist.

        The default YAML is created from DEFAULT_TRACKER_SETTINGS
        when missing.

        The active tracker YAML is created from the default YAML
        when missing.
        """

        default_path = self._get_tracker_config_path(
            default=True
        )

        tracker_path = self._get_tracker_config_path()

        # ---------------------------------------------------------
        # Create default YAML if missing
        # ---------------------------------------------------------

        if not default_path.exists():

            try:

                default_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with default_path.open(
                    "w",
                    encoding="utf-8",
                ) as file:

                    yaml.safe_dump(
                        self.DEFAULT_TRACKER_SETTINGS,
                        file,
                        sort_keys=False,
                    )

            except Exception as error:

                print(
                    "[TrackerTuning] "
                    f"Could not create default YAML: {error}"
                )

        # ---------------------------------------------------------
        # Create active YAML if missing
        # ---------------------------------------------------------

        if not tracker_path.exists():

            default_settings = self._load_tracker_yaml(
                default_path
            )

            if not default_settings:
                return

            try:

                tracker_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with tracker_path.open(
                    "w",
                    encoding="utf-8",
                ) as file:

                    yaml.safe_dump(
                        default_settings,
                        file,
                        sort_keys=False,
                    )

            except Exception as error:

                print(
                    "[TrackerTuning] "
                    f"Could not create tracker YAML: {error}"
                )

    # =========================================================
    # Save YAML
    # =========================================================

    def _save_tracker_settings(
        self,
        show_status=True,
        reset_tracker=False,
    ):
        """
        Save the current runtime tracker settings to
        bytetrack_tools.yaml while preserving unrelated fields.
        """

        path = self._get_tracker_config_path()

        try:
            existing = {}

            if path.exists():
                with path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = yaml.safe_load(
                        file
                    )

                if isinstance(
                    data,
                    dict,
                ):
                    existing = data

            for name, value in (
                self._tracker_settings.items()
            ):
                existing[name] = value

            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with path.open(
                "w",
                encoding="utf-8",
            ) as file:

                yaml.safe_dump(
                    existing,
                    file,
                    sort_keys=False,
                )

            if reset_tracker and self.camera is not None:
                self.camera.reset_tracker()

            if show_status:
                self.tracker_status_label.setText(
                    "Tracker settings saved to YAML."
                )

        except Exception as error:

            if show_status:
                self.tracker_status_label.setText(
                    f"Could not save YAML: {error}"
                )

            print(
                "[TrackerTuning] "
                f"Could not save YAML: {error}"
            )


    def _save_current_as_tracker_defaults(
        self,
    ):
        """
        Overwrite bytetrack_yaml_default.yaml with the current
        tracker settings while preserving unrelated YAML fields.
        """

        default_path = self._get_tracker_config_path(
            default=True
        )

        try:
            existing = {}

            if default_path.exists():

                with default_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = yaml.safe_load(
                        file
                    )

                if isinstance(
                    data,
                    dict,
                ):
                    existing = data

            for name, value in (
                self._tracker_settings.items()
            ):
                existing[name] = value

            default_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with default_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                yaml.safe_dump(
                    existing,
                    file,
                    sort_keys=False,
                )

            self.tracker_status_label.setText(
                "Current tracker settings saved as the default YAML."
            )

        except Exception as error:

            self.tracker_status_label.setText(
                f"Could not overwrite default YAML: {error}"
            )

            print(
                "[TrackerTuning] "
                f"Could not overwrite default YAML: {error}"
            )

    def _reset_tracker_defaults_to_factory(
        self,
    ):
        """
        Reset bytetrack_yaml_default.yaml to the values manually
        defined in DEFAULT_TRACKER_SETTINGS.

        Unrelated YAML fields are preserved.
        The UI and runtime tracker are also reset to those defaults.
        """

        default_path = self._get_tracker_config_path(
            default=True
        )

        try:
            existing = {}

            if default_path.exists():

                with default_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = yaml.safe_load(
                        file
                    )

                if isinstance(
                    data,
                    dict,
                ):
                    existing = data

            for name, value in (
                self.DEFAULT_TRACKER_SETTINGS.items()
            ):
                existing[name] = value

            default_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with default_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                yaml.safe_dump(
                    existing,
                    file,
                    sort_keys=False,
                )

            # -----------------------------------------------------
            # Load Python defaults into UI
            # -----------------------------------------------------

            self._tracker_settings = dict(
                self.DEFAULT_TRACKER_SETTINGS
            )

            for name, control in (
                self._tracker_sliders.items()
            ):

                slider = control["slider"]

                slider.blockSignals(True)

                slider.setValue(
                    self._tracker_value_to_slider(
                        name,
                        self._tracker_settings[name],
                    )
                )

                slider.blockSignals(False)

                self._update_tracker_slider_label(
                    name
                )

            self.tracker_fuse_score_checkbox.blockSignals(
                True
            )

            self.tracker_fuse_score_checkbox.setChecked(
                bool(
                    self._tracker_settings[
                        "fuse_score"
                    ]
                )
            )

            self.tracker_fuse_score_checkbox.blockSignals(
                False
            )

            # -----------------------------------------------------
            # Apply defaults to runtime tracker
            # -----------------------------------------------------

            for name, value in (
                self._tracker_settings.items()
            ):

                self._apply_tracker_setting(
                    name,
                    value,
                )

            if self.camera is not None:
                self.camera.reset_tracker()

                self.tracker_status_label.setText(
                    "Default YAML reset and tracker reset."
                )

            else:
                self.tracker_status_label.setText(
                    "Default YAML reset. Tracker hook not connected."
                )

        except Exception as error:

            self.tracker_status_label.setText(
                f"Could not reset default YAML: {error}"
            )

            print(
                "[TrackerTuning] "
                f"Could not reset default YAML: {error}"
            )

    # =========================================================
    # Tracker Button Styling
    # =========================================================

    def _style_tracker_button(
        self,
        button,
    ):
        button.setStyleSheet(
            f"""
            QPushButton {{
                background: {self._get_color(PANEL_BG)};
                color: {self._get_color(TEXT_COLOR)};
                border: 1px solid {self._get_color(ACCENT_COLOR)};
                border-radius: 6px;
                padding: 4px 10px;
            }}

            QPushButton:hover {{
                background: {self._get_color(ACCENT_HOVER)};
                color: {self._get_color(WHITE_TEXT)};
                border: 1px solid {self._get_color(ACCENT_COLOR)};
            }}

            QPushButton:pressed {{
                background: {self._get_color(ACCENT_COLOR)};
                color: {self._get_color(WHITE_TEXT)};
            }}
            """
        )

    # =========================================================
    # Tracker Checkbox Styling
    # =========================================================

    def _style_tracker_checkbox(
        self,
        checkbox,
    ):
        checkbox.setStyleSheet(
            f"""
            QCheckBox {{
                color: {self._get_color(TEXT_COLOR)};
                spacing: 6px;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {self._get_color(ACCENT_COLOR)};
                background: {self._get_color(INPUT_BG)};
            }}

            QCheckBox::indicator:hover {{
                border: 1px solid {self._get_color(ACCENT_COLOR)};
            }}

            QCheckBox::indicator:checked {{
                background: {self._get_color(ACCENT_COLOR)};
                border: 1px solid {self._get_color(ACCENT_COLOR)};
                image: url(:/qt-project.org/styles/commonstyle/images/checkbox_checked.png);
            }}
            """
        )

    # =========================================================
    # Slider Styling
    # =========================================================

    def _style_tracker_slider(
        self,
        slider,
    ):
        slider.setStyleSheet(
            f"""
            QSlider {{
                background: transparent;
            }}

            QSlider::groove:horizontal {{
                height: 5px;
                background: {self._get_color(BORDER_COLOR)};
                border-radius: 2px;
            }}

            QSlider::handle:horizontal {{
                width: 16px;
                height: 16px;
                margin: -6px 0;
                background: {self._get_color(ACCENT_COLOR)};
                border: none;
                border-radius: 8px;
            }}

            QSlider::handle:horizontal:hover {{
                background: {self._get_color(ACCENT_HOVER)};
            }}

            QSlider::sub-page:horizontal {{
                background: {self._get_color(ACCENT_COLOR)};
                border-radius: 2px;
            }}

            QSlider::add-page:horizontal {{
                background: {self._get_color(BORDER_COLOR)};
                border-radius: 2px;
            }}
            """
        )


    # =========================================================
    # Theme Refresh
    # =========================================================

    def refresh_tracker_tuning_theme(
        self,
    ):
        """
        Refresh the tracker tab after the application's
        appearance mode changes.
        """

        if not hasattr(
            self,
            "tracker_tuning_tab",
        ):
            return

        # ---------------------------------------------------------
        # Main tab
        # ---------------------------------------------------------

        self.tracker_tuning_tab.setStyleSheet(
            f"""
            QWidget {{
                background-color: {self._get_color(PANEL_BG)};
                color: {self._get_color(TEXT_COLOR)};
            }}

            """
        )

        # ---------------------------------------------------------
        # Labels
        # ---------------------------------------------------------

        for widget in (
            self.tracker_tuning_tab.findChildren(
                QLabel
            )
        ):

            self._style_label(
                widget,
                TEXT_COLOR,
                size=max(
                    10,
                    widget.font().pointSize(),
                ),
                bold=widget.font().bold(),
            )

        # ---------------------------------------------------------
        # Frames
        # ---------------------------------------------------------

        for widget in (
            self.tracker_tuning_tab.findChildren(
                QFrame
            )
        ):

            self._style_frame(
                widget,
                CARD_BG,
                BORDER_COLOR,
                radius=8,
            )

        # ---------------------------------------------------------
        # Sliders
        # ---------------------------------------------------------

        for control in (
            self._tracker_sliders.values()
        ):

            self._style_tracker_slider(
                control["slider"]
            )

        # ---------------------------------------------------------
        # Checkbox
        # ---------------------------------------------------------

        if hasattr(
            self,
            "tracker_fuse_score_checkbox",
        ):

            self._style_tracker_checkbox(
                self.tracker_fuse_score_checkbox
            )

        # ---------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------

        for button in (
            getattr(
                self,
                "tracker_defaults_button",
                None,
            ),
            getattr(
                self,
                "tracker_overwrite_defaults_button",
                None,
            ),
            getattr(
                self,
                "tracker_reset_defaults_button",
                None,
            ),
        ):

            if button is not None:
                self._style_tracker_button(
                    button
                )
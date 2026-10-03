from fractions import Fraction

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QPushButton,
    QGridLayout,
    QWidget,
    QSizePolicy,
    QLabel,
)

from GUI.appearance_controller import (
    INPUT_BG,
    PANEL_BG,
    BORDER_COLOR,
    TEXT_COLOR,
)


class FractionDropdown(QFrame):

    value_changed = Signal(str)

    def __init__(
        self,
        parent=None,
        textvariable=None,
        command=None,
        width=25,
        measurement="SAE",
        dual_measurement=None,
        appearance_mode="Dark",
        **kwargs,
    ):
        super().__init__(parent)

        # __init__
        self.appearance_mode = appearance_mode
        self.textvariable = textvariable
        self.command = command
        self.width = width
        self.measurement = measurement
        self.dual_measurement = dual_measurement

        self._value = ""

        self.popup = None
        self.values = []

        self.setFixedHeight(36)

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {INPUT_BG[1]};
                border: 1px solid {BORDER_COLOR[1]};
                border-radius: 8px;
            }}
            """
        )

        self.create_gui()

    def get_color(self, color):
        if isinstance(color, tuple):
            return color[0] if self.appearance_mode == "Light" else color[1]
        return color

    def set_appearance_mode(self, mode):
        self.appearance_mode = mode.capitalize()

        if self.appearance_mode not in (
            "Light",
            "Dark",
        ):
            self.appearance_mode = "Dark"

        self.refresh_dropdown_theme()

        if self.popup is not None:
            self.close_popup()

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):

        self.button = QPushButton()

        self.button_label = QLabel(
            self.get_current_value()
        )

        self.button_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        self.button_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.button.setCursor(
            Qt.PointingHandCursor
        )

        self.button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {INPUT_BG[1]};
                color: {TEXT_COLOR[1]};
                border: none;
                border-radius: 7px;
                padding: 0px;
            }}

            QPushButton:hover {{
                background-color: {BORDER_COLOR[1]};
            }}
            """
        )

        self.button_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: transparent;
                color: {TEXT_COLOR[1]};
                border: none;
                padding-left: 8px;
                padding-right: 8px;
            }}
            """
        )

        self.button.clicked.connect(
            self.toggle_dropdown
        )

        self.arrow_button = QPushButton(
            "▼"
        )

        self.arrow_button.setFixedWidth(
            28
        )

        self.arrow_button.setCursor(
            Qt.PointingHandCursor
        )

        self.arrow_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {INPUT_BG[1]};
                color: {TEXT_COLOR[1]};
                border: none;
                border-radius: 7px;
                font-size: 10px;
            }}

            QPushButton:hover {{
                background-color: {BORDER_COLOR[1]};
            }}
            """
        )

        self.arrow_button.clicked.connect(
            self.toggle_dropdown
        )

        from PySide6.QtWidgets import QHBoxLayout

        button_layout = QHBoxLayout(
            self.button
        )

        button_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        button_layout.setSpacing(0)

        button_layout.addWidget(
            self.button_label
        )

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            1,
            1,
            1,
            1,
        )

        layout.setSpacing(0)

        layout.addWidget(
            self.button,
            1,
        )

        layout.addWidget(
            self.arrow_button
        )




    # =========================================================
    # Theme
    # =========================================================


    def refresh_dropdown_theme(self):

        input_bg = self.get_color(INPUT_BG)
        panel_bg = self.get_color(PANEL_BG)
        border = self.get_color(BORDER_COLOR)
        text = self.get_color(TEXT_COLOR)


        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {panel_bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            """
        )

        self.button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {panel_bg};
                color: {text};
                border: none;
                border-radius: 7px;
                padding-left: 8px;
                padding-right: 8px;
                text-align: left;
            }}

            QPushButton:hover {{
                background-color: {border};
            }}
            """
        )

        self.arrow_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {panel_bg};
                color: {text};
                border: none;
                border-radius: 7px;
                font-size: 10px;
            }}

            QPushButton:hover {{
                background-color: {border};
            }}
            """
        )

        self.button_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: transparent;
                color: {text};
                border: none;
                padding-left: 8px;
                padding-right: 8px;
            }}
            """
        )


    # =========================================================
    # Value Variable Compatibility
    # =========================================================

    def get_current_value(self):

        if self.textvariable is None:
            return self._value

        if hasattr(
            self.textvariable,
            "value",
        ):
            return str(
                self.textvariable.value
            )

        if callable(self.textvariable):
            return str(
                self.textvariable()
            )

        return str(
            self.textvariable
        )

    def set_current_value(self, value):

        value = str(value)

        self._value = value

        if self.textvariable is not None:

            if hasattr(
                self.textvariable,
                "set",
            ):
                self.textvariable.set(value)

            elif hasattr(
                self.textvariable,
                "value",
            ):
                self.textvariable.value = value

        self.button_label.setText(value)

    # =========================================================
    # Measurement
    # =========================================================

    def set_measurement(
        self,
        measurement,
        dual_measurement=None,
    ):
        self.measurement = measurement
        self.dual_measurement = dual_measurement

        if self.popup is not None:
            self.close_popup()

    # =========================================================
    # Values
    # =========================================================

    def set_values(self, values):

        self.values = list(values)

        if self.popup is not None:
            self.close_popup()

    # =========================================================
    # Dropdown
    # =========================================================

    def toggle_dropdown(self):

        if self.popup is not None:
            self.close_popup()
            return

        if (
            not self.values
            and self.measurement != "Other"
        ):
            return

        panel_bg = self.get_color(PANEL_BG)
        border = self.get_color(BORDER_COLOR)
        text = self.get_color(TEXT_COLOR)

        self.popup = QWidget(
            None,
            Qt.Tool | Qt.FramelessWindowHint,
        )

        self.popup.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.popup.setStyleSheet(
            "background: transparent;"
        )

        x = self.mapToGlobal(
            self.rect().bottomLeft()
        ).x()

        y = self.mapToGlobal(
            self.rect().bottomLeft()
        ).y()

        frame = QFrame(
            self.popup
        )

        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {panel_bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            """
        )

        layout = QGridLayout(frame)

        layout.setContentsMargins(
            4,
            4,
            4,
            4,
        )

        layout.setHorizontalSpacing(3)
        layout.setVerticalSpacing(2)

        # =====================================================
        # OTHER / METRIC
        # =====================================================

        if (
            self.measurement == "Other"
            or self.measurement == "Metric"
            or (
                self.measurement == "DUAL"
                and self.dual_measurement == "Metric"
            )
        ):

            columns = 3

            if not self.values:
                self.close_popup()
                return

            rows = (
                len(self.values)
                + columns
                - 1
            ) // columns

            for index, value in enumerate(
                self.values
            ):

                column = index // rows
                row = index % rows

                button = self.create_option_button(
                    value
                )

                layout.addWidget(
                    button,
                    row,
                    column,
                )

        # =====================================================
        # SAE
        # =====================================================

        else:

            def parse_sae(value):

                value = str(value).strip()

                if value.endswith('"'):
                    value = value[:-1].strip()

                try:

                    # Mixed fraction
                    if "-" in value:

                        whole, fraction = (
                            value.split(
                                "-",
                                1,
                            )
                        )

                        whole = int(whole)
                        fraction = Fraction(
                            fraction
                        )

                        return {
                            "value": value,
                            "numeric": (
                                Fraction(whole)
                                + fraction
                            ),
                            "numerator": (
                                fraction.numerator
                            ),
                            "denominator": (
                                fraction.denominator
                            ),
                            "whole": whole,
                            "is_mixed": True,
                        }

                    # Simple fraction
                    if "/" in value:

                        fraction = Fraction(
                            value
                        )

                        return {
                            "value": value,
                            "numeric": fraction,
                            "numerator": (
                                fraction.numerator
                            ),
                            "denominator": (
                                fraction.denominator
                            ),
                            "whole": 0,
                            "is_mixed": False,
                        }

                    # Whole number
                    whole = int(value)

                    return {
                        "value": value,
                        "numeric": Fraction(
                            whole
                        ),
                        "numerator": 0,
                        "denominator": 1,
                        "whole": whole,
                        "is_mixed": False,
                    }

                except (
                    ValueError,
                    ZeroDivisionError,
                ):
                    return None

            # =================================================
            # SEPARATE VALUES INTO PHASES
            # =================================================

            na_value = None
            fraction_groups = {}
            mixed_groups = {}

            one_value = None
            whole_numbers = []

            for value in self.values:

                if (
                    str(value)
                    .strip()
                    .upper()
                    == "NA"
                ):

                    na_value = {
                        "value": str(value),
                        "numeric": Fraction(0),
                        "numerator": 0,
                        "denominator": 1,
                        "whole": 0,
                        "is_mixed": False,
                    }

                    continue

                parsed = parse_sae(value)

                if parsed is None:
                    continue

                numeric = parsed["numeric"]
                denominator = parsed[
                    "denominator"
                ]

                # Fractions less than 1
                if numeric < 1:

                    fraction_groups.setdefault(
                        denominator,
                        [],
                    ).append(parsed)

                    continue

                # Exactly 1
                if numeric == 1:

                    one_value = parsed

                    continue

                # Mixed fractions greater than 1
                if parsed["is_mixed"]:

                    mixed_groups.setdefault(
                        denominator,
                        [],
                    ).append(parsed)

                    continue

                # Whole numbers greater than 1
                whole_numbers.append(parsed)

            # =================================================
            # SORT FRACTION GROUPS
            # =================================================

            for denominator in fraction_groups:

                fraction_groups[
                    denominator
                ].sort(
                    key=lambda item: item[
                        "numeric"
                    ]
                )

            # =================================================
            # SORT MIXED FRACTION GROUPS
            # =================================================

            for denominator in mixed_groups:

                mixed_groups[
                    denominator
                ].sort(
                    key=lambda item: item[
                        "numeric"
                    ]
                )

            # =================================================
            # CREATE ORDERED GROUPS
            # =================================================

            ordered_groups = []

            if na_value is not None:

                ordered_groups.append(
                    [na_value]
                )

            for denominator in sorted(
                fraction_groups
            ):

                ordered_groups.append(
                    fraction_groups[
                        denominator
                    ]
                )

            if one_value is not None:

                ordered_groups.append(
                    [one_value]
                )

            for denominator in sorted(
                mixed_groups
            ):

                ordered_groups.append(
                    mixed_groups[
                        denominator
                    ]
                )

            # =================================================
            # WHOLE NUMBERS
            # =================================================

            whole_numbers.sort(
                key=lambda item: item[
                    "numeric"
                ]
            )

            if whole_numbers:

                ordered_groups.append(
                    whole_numbers
                )

            # =================================================
            # BUILD COLUMNS
            # =================================================

            columns = []
            current_column = []

            MAX_OPTIONS_PER_COLUMN = 10

            for group in ordered_groups:

                for item in group:

                    current_column.append(
                        item
                    )

                    if (
                        len(current_column)
                        >= MAX_OPTIONS_PER_COLUMN
                    ):

                        columns.append(
                            current_column
                        )

                        current_column = []

            if current_column:

                columns.append(
                    current_column
                )

            # =================================================
            # DISPLAY COLUMNS
            # =================================================

            for (
                column_index,
                column_items,
            ) in enumerate(columns):

                for row, item in enumerate(
                    column_items
                ):

                    value = item["value"]

                    if (
                        str(value)
                        .strip()
                        .upper()
                        == "NA"
                    ):

                        display_value = value

                    elif (
                        self.measurement
                        == "DUAL"
                        and self.dual_measurement
                        == "SAE"
                    ):

                        display_value = (
                            f'{value}"'
                        )

                    elif (
                        self.measurement
                        == "SAE"
                    ):

                        display_value = (
                            f'{value}"'
                            if not value.endswith(
                                '"'
                            )
                            else value
                        )

                    else:

                        display_value = value

                    button = (
                        self.create_option_button(
                            display_value,
                            width=70,
                        )
                    )

                    layout.addWidget(
                        button,
                        row,
                        column_index,
                    )

        self.popup.adjustSize()

        frame.adjustSize()

        self.popup.resize(
            frame.sizeHint()
        )

        frame.setGeometry(
            0,
            0,
            frame.sizeHint().width(),
            frame.sizeHint().height(),
        )

        self.popup.move(
            x,
            y,
        )

        self.popup.show()

        self.popup.activateWindow()
        self.popup.setFocus()

    # =========================================================
    # Option Button
    # =========================================================

    def create_option_button(
        self,
        value,
        width=100,
    ):

        border = self.get_color(BORDER_COLOR)
        text = self.get_color(TEXT_COLOR)

        button = QPushButton(
            str(value)
        )

        button.setFixedSize(
            width,
            30,
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {text};
                border: none;
                border-radius: 5px;
                padding: 2px;
            }}

            QPushButton:hover {{
                background-color: {border};
            }}
            """
        )

        button.clicked.connect(
            lambda checked=False, v=value:
            self.select(v)
        )

        return button

    # =========================================================
    # Selection
    # =========================================================

    def select(self, value):

        self.set_current_value(
            value
        )

        self.close_popup()

        self.value_changed.emit(
            str(value)
        )

        if self.command is not None:
            self.command()

    # =========================================================
    # Close
    # =========================================================

    def close_popup(self):

        if self.popup is not None:

            self.popup.close()
            self.popup.deleteLater()

            self.popup = None

    # =========================================================
    # Set / Get
    # =========================================================

    def set(self, value):

        self.set_current_value(
            value
        )

    def get(self):

        return self.get_current_value()
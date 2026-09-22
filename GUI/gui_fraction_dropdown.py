import tkinter as tk
from fractions import Fraction


class FractionDropdown(tk.Frame):

    def __init__(
        self,
        parent,
        textvariable,
        command=None,
        width=25,
        measurement="SAE",
        dual_measurement=None,
        **kwargs,
    ):
        super().__init__(
            parent,
            bd=1,
            relief="solid",
            **kwargs,
        )

        self.textvariable = textvariable
        self.command = command
        self.width = width
        self.measurement = measurement
        self.dual_measurement = dual_measurement

        self.button = tk.Button(
            self,
            textvariable=self.textvariable,
            anchor="w",
            relief="flat",
            bd=0,
            width=width,
            command=self.toggle_dropdown,
        )

        self.button.pack(
            fill=tk.X,
            padx=2,
            pady=2,
        )

        self.popup = None
        self.values = []

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
            self.popup.destroy()
            self.popup = None

    # =========================================================
    # Dropdown
    # =========================================================

    def toggle_dropdown(self):

        if self.popup is not None:
            self.close_popup()
            return

        if not self.values and self.measurement != "Other":
            return

        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        self.popup.geometry(
            f"+{x}+{y}"
        )

        frame = tk.Frame(
            self.popup,
            bd=1,
            relief="solid",
            bg="white",
        )

        frame.pack()

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
                return

            rows = (
                len(self.values) + columns - 1
            ) // columns

            for index, value in enumerate(
                self.values
            ):

                column = index // rows
                row = index % rows

                button = tk.Button(
                    frame,
                    text=value,
                    width=12,
                    anchor="center",
                    relief="flat",
                    bg="white",
                    command=lambda v=value: self.select(v),
                )

                button.grid(
                    row=row,
                    column=column,
                    padx=2,
                    pady=1,
                    sticky="ew",
                )


        # =====================================================
        # METRIC
        # =====================================================

        elif (
            self.measurement == "Metric"
            or (
                self.measurement == "DUAL"
                and self.dual_measurement == "Metric"
            )
        ):

            columns = 3

            rows = (
                len(self.values) + columns - 1
            ) // columns

            for index, value in enumerate(
                self.values
            ):

                column = index // rows
                row = index % rows

                button = tk.Button(
                    frame,
                    text=value,
                    width=8,
                    anchor="center",
                    relief="flat",
                    bg="white",
                    command=lambda v=value: self.select(v),
                )

                button.grid(
                    row=row,
                    column=column,
                    padx=2,
                    pady=1,
                    sticky="ew",
                )

        # =====================================================
        # SAE
        # =====================================================

        else:

            def parse_sae(value):

                value = str(value).strip()

                # -------------------------------------------------
                # Remove trailing double quote from SAE sizes.
                #
                # Example:
                # 1/4" -> 1/4
                # 1-1/4" -> 1-1/4
                # 1" -> 1
                #
                # This keeps the " from interfering with parsing
                # while the original value is still displayed.
                # -------------------------------------------------

                if value.endswith('"'):
                    value = value[:-1].strip()

                try:

                    # -------------------------------------------------
                    # Mixed fraction
                    # Example: 1-5/8
                    # -------------------------------------------------

                    if "-" in value:

                        whole, fraction = value.split(
                            "-",
                            1,
                        )

                        whole = int(whole)
                        fraction = Fraction(fraction)

                        return {
                            "value": value,
                            "numeric": (
                                Fraction(whole)
                                + fraction
                            ),
                            "numerator": fraction.numerator,
                            "denominator": fraction.denominator,
                            "whole": whole,
                            "is_mixed": True,
                        }

                    # -------------------------------------------------
                    # Simple fraction
                    # Example: 5/8
                    # -------------------------------------------------

                    if "/" in value:

                        fraction = Fraction(value)

                        return {
                            "value": value,
                            "numeric": fraction,
                            "numerator": fraction.numerator,
                            "denominator": fraction.denominator,
                            "whole": 0,
                            "is_mixed": False,
                        }

                    # -------------------------------------------------
                    # Whole number
                    # Example: 1
                    # -------------------------------------------------

                    whole = int(value)

                    return {
                        "value": value,
                        "numeric": Fraction(whole),
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

            # =====================================================
            # SEPARATE VALUES INTO PHASES
            # =====================================================

            na_value = None
            fraction_groups = {}
            mixed_groups = {}

            one_value = None
            whole_numbers = []

            for value in self.values:

                if str(value).strip().upper() == "NA":
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
                denominator = parsed["denominator"]

                # -------------------------------------------------
                # Fractions less than 1
                # -------------------------------------------------

                if numeric < 1:

                    fraction_groups.setdefault(
                        denominator,
                        [],
                    ).append(parsed)

                    continue

                # -------------------------------------------------
                # Exactly 1
                # -------------------------------------------------

                if numeric == 1:

                    one_value = parsed

                    continue

                # -------------------------------------------------
                # Mixed fractions greater than 1
                # -------------------------------------------------

                if parsed["is_mixed"]:

                    mixed_groups.setdefault(
                        denominator,
                        [],
                    ).append(parsed)

                    continue

                # -------------------------------------------------
                # Whole numbers greater than 1
                # -------------------------------------------------

                whole_numbers.append(parsed)

            # =====================================================
            # SORT FRACTION GROUPS
            # =====================================================

            for denominator in fraction_groups:

                fraction_groups[denominator].sort(
                    key=lambda item: item["numeric"]
                )

            # =====================================================
            # SORT MIXED FRACTION GROUPS
            # =====================================================

            for denominator in mixed_groups:

                mixed_groups[denominator].sort(
                    key=lambda item: item["numeric"]
                )

            # =====================================================
            # CREATE ORDERED GROUPS
            # =====================================================

            ordered_groups = []

            # -----------------------------------------------------
            # NA
            # -----------------------------------------------------

            if na_value is not None:
                ordered_groups.append(
                    [na_value]
                )

            # -----------------------------------------------------
            # Fractions below 1
            # -----------------------------------------------------

            for denominator in sorted(
                fraction_groups
            ):

                ordered_groups.append(
                    fraction_groups[denominator]
                )

            # -----------------------------------------------------
            # Exactly 1
            # -----------------------------------------------------

            if one_value is not None:

                ordered_groups.append(
                    [one_value]
                )

            # -----------------------------------------------------
            # Mixed fractions
            # -----------------------------------------------------

            for denominator in sorted(
                mixed_groups
            ):

                ordered_groups.append(
                    mixed_groups[denominator]
                )

            # =====================================================
            # WHOLE NUMBERS
            # =====================================================

            whole_numbers.sort(
                key=lambda item: item["numeric"]
            )

            if whole_numbers:

                ordered_groups.append(
                    whole_numbers
                )

            # =====================================================
            # BUILD COLUMNS
            # =====================================================

            columns = []
            current_column = []

            MAX_OPTIONS_PER_COLUMN = 10

            for group in ordered_groups:

                for item in group:

                    current_column.append(item)

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

            # =====================================================
            # DISPLAY COLUMNS
            # =====================================================

            for (
                column_index,
                column_items,
            ) in enumerate(columns):

                for row, item in enumerate(
                    column_items
                ):

                    value = item["value"]

                    # -------------------------------------------------
                    # Restore the double quote for display.
                    #
                    # The stored/configured value remains:
                    #     1/4"
                    #
                    # But parsing above safely removes it first.
                    # -------------------------------------------------

                    if str(value).strip().upper() == "NA":
                        display_value = value

                    elif (
                        self.measurement == "DUAL"
                        and self.dual_measurement == "SAE"
                    ):
                        display_value = f'{value}"'

                    elif self.measurement == "SAE":
                        display_value = (
                            f'{value}"'
                            if not value.endswith('"')
                            else value
                        )

                    else:
                        display_value = value

                    button = tk.Button(
                        frame,
                        text=display_value,
                        width=8,
                        anchor="center",
                        relief="flat",
                        bg="white",
                        command=lambda v=display_value: self.select(v),
)
                    button.grid(
                        row=row,
                        column=column_index,
                        padx=2,
                        pady=1,
                        sticky="ew",
                    )

        self.popup.bind(
            "<FocusOut>",
            lambda event: self.close_popup(),
        )

        self.popup.focus_set()

    # =========================================================
    # Selection
    # =========================================================

    def select(self, value):

        self.textvariable.set(
            value
        )

        self.close_popup()

        if self.command is not None:
            self.command()

    # =========================================================
    # Close
    # =========================================================

    def close_popup(self):

        if self.popup is not None:

            self.popup.destroy()
            self.popup = None

    # =========================================================
    # Set / Get
    # =========================================================

    def set(self, value):
        self.textvariable.set(
            value
        )

    def get(self):
        return self.textvariable.get()
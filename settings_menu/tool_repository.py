import json
import os



SETTINGS_DIR = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "settings",
)

SETTINGS_FILE = os.path.join(
    SETTINGS_DIR,
    "tools.json",
)

DEFAULT_TOOLS = {
    "Socket": [],
    "Adapter": [],
    "Crowfoot": [],
    "Extension": [],
    "Wrench": [],
    "Pliers": [],
    "Brake Tool": [],
    "Screwdriver": [],
    "Breaker Bar": [],
    "Ratchet": [],
    "Punch": [],
    "Feeler Gauge": [],
    "Tool Holder": [],
    "Torque Wrench": [],
    "Allen Key": [],
    "Torx Key": [],
    "Hammer": [],
    "Pick": [],
}


class ToolRepository:

    @staticmethod
    def normalize_tools(data):
        if not isinstance(data, dict) or not data:
            return {"NA": ["NA"]}

        normalized_tools = {}

        for tool_name, sizes in data.items():
            if not isinstance(tool_name, str):
                continue

            if not isinstance(sizes, list):
                continue

            cleaned_sizes = [value for value in sizes if value not in (None, "", "NA")]

            if not cleaned_sizes:
                normalized_tools[tool_name] = ["NA"]
            else:
                normalized_tools[tool_name] = cleaned_sizes

        if not normalized_tools:
            return {"NA": ["NA"]}

        return normalized_tools

    @staticmethod
    def load_tools():
        if not os.path.exists(SETTINGS_FILE):
            return {
                tool: list(sizes)
                for tool, sizes in DEFAULT_TOOLS.items()
            }

        try:
            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            return ToolRepository.normalize_tools(data)

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {"NA": ["NA"]}

    @staticmethod
    def save_tools(tools):
        try:
            os.makedirs(
                SETTINGS_DIR,
                exist_ok=True,
            )

            with open(
                SETTINGS_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    tools,
                    file,
                    indent=4,
                )

            return True

        except OSError:
            return False
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

            if not isinstance(data, dict):
                return {}

            normalized_tools = {}

            for tool_name, sizes in data.items():

                if not isinstance(tool_name, str):
                    return {}

                if not isinstance(sizes, list):
                    return {}

                normalized_tools[tool_name] = []

            return normalized_tools

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

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
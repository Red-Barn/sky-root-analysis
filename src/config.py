from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # sky-root-analysis
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

# API_KEYS
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# PATHS
RESULT_INPUT_PATH = os.getenv("RESULT_INPUT_PATH")
ROUTE_OUTPUT_PATH = os.getenv("ROUTE_OUTPUT_PATH")
REGION_OUTPUT_PATH = os.getenv("REGION_OUTPUT_PATH")
SENSITIVITY_OUTPUT_PATH = os.getenv("SENSITIVITY_OUTPUT_PATH")
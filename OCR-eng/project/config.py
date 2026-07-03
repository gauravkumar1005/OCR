"""
==========================================================================
Enterprise Medical IDP Configuration
==========================================================================
"""

import os

from dotenv import load_dotenv

# ==========================================================================
# PROJECT ROOT (Resolves paths relative to 'New folder2')
# ==========================================================================

# Base directory of this configure.py file (C:\...\New folder2\project)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up exactly one level to step out of 'project/' and hit 'New folder2/' base root
BASE_DIR = os.path.dirname(PROJECT_DIR)

# Points to C:\...\New folder2\result
RESULT_DIR = os.path.join(BASE_DIR, "RESULT/MEDSAVE")

# ==========================================================================
# API
# ==========================================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY environment variable is missing. Set it in OCR-eng/.env before starting the OCR engine."
    )

MODEL_NAME = "llama-3.3-70b-versatile"

PROMPT_VERSION = "v1.2.0"

# ==========================================================================
# REQUESTS
# ==========================================================================

MAX_RETRIES = 5

INITIAL_BACKOFF = 2

REQUEST_TIMEOUT = 120


# ==========================================================
# LLM OUTPUT
# ==========================================================

MAX_OUTPUT_TOKENS = 4000


# ==========================================================================
# RATE LIMIT
# ==========================================================================

MAX_REQUESTS_PER_MINUTE = 30

API_PACING_DELAY = 60 / MAX_REQUESTS_PER_MINUTE

# ==========================================================================
# OCR
# ==========================================================================

MAX_CHARS = 25000

MIN_PAGE_CHARACTERS = 15

# ==========================================================================
# INPUT (Points directly to C:\...\New folder2\result\05_ocr)
# ==========================================================================

MERGED_DOCUMENT_DIR = os.path.join(
    RESULT_DIR,
    "08_merged_documents"
)

# ==========================================================================
# OUTPUT (Points directly to C:\...\New folder2\result\06_llm_json)
# ==========================================================================

PARSED_DIR = os.path.join(RESULT_DIR, "09_llm_json")

# ==========================================================================
# LOGGING
# ==========================================================================

LOG_DIR = os.path.join(BASE_DIR, "logs")

LOG_FILE = os.path.join(LOG_DIR, "llm_parser.log")

# ==========================================================================
# TEMP FILES
# ==========================================================================

TEMP_DIR = os.path.join(BASE_DIR, "temp")

# ==========================================================================
# JSON
# ==========================================================================

JSON_INDENT = 4

JSON_ENCODING = "utf-8"

ENSURE_ASCII = False

# ==========================================================================
# FILE NAMING
# ==========================================================================

INPUT_EXTENSION = "_raw.txt"

OUTPUT_EXTENSION = ".json"

TEMP_EXTENSION = ".tmp"

RAW_SUFFIX = "_raw"

# ==========================================================================
# EXTRACTION
# ==========================================================================

STRICT_JSON_MODE = True

IGNORE_HANDWRITTEN = True

ALLOW_NULL_FIELDS = True

PRESERVE_TABLE_LAYOUT = True

# ==========================================================================
# MEMORY
# ==========================================================================

ENABLE_GARBAGE_COLLECTION = True

DELETE_INTERMEDIATE_OBJECTS = True

# ==========================================================================
# DOCUMENT TYPES
# ==========================================================================

SUPPORTED_DOCUMENT_TYPES = [
    "Hospital Bill",
    "Itemized Invoice",
    "Insurance Claim Form",
    "Cashless Authorization",
    "Discharge Summary",
    "Laboratory Report",
    "Radiology Report",
    "Pharmacy Receipt",
    "Prescription",
    "Medical Certificate",
    "Patient Registration Form",
    "Consent Form",
    "Unknown"
]

# ==========================================================================
# CREATE DIRECTORIES
# ==========================================================================

os.makedirs(PARSED_DIR, exist_ok=True)

os.makedirs(LOG_DIR, exist_ok=True)

os.makedirs(TEMP_DIR, exist_ok=True)

# ==========================================================================
# VALIDATION
# ==========================================================================

if not os.path.isdir(MERGED_DOCUMENT_DIR):
    raise FileNotFoundError(
        f"OCR folder not found:\n{MERGED_DOCUMENT_DIR}"
    )

# ==========================================================================
# CONFIGURATION SUMMARY
# ==========================================================================

print("=" * 70)
print("Enterprise Medical IDP Configuration (Updated File Architecture)")
print("=" * 70)
print(f"Model              : {MODEL_NAME}")
print(f"Prompt Version     : {PROMPT_VERSION}")
print(f"OCR Input Folder   : {MERGED_DOCUMENT_DIR}")
print(f"JSON Output Folder : {PARSED_DIR}")
print(f"Logs               : {LOG_FILE}")
print(f"API Delay          : {API_PACING_DELAY:.2f} sec")
print("=" * 70)

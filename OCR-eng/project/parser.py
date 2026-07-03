# import os
# import gc
# import json
# import time
# import logging
# import re
# import sys
# from datetime import datetime

# import config
# import prompt
# import utils
# import llm_client

# from pathlib import Path

# # def extract_page_number(file_name: str) -> int:
# #     """Extracts the numeric page sequence from filenames like 'page_0.txt' or 'raw_1.txt'."""
# #     numbers = re.findall(r'\d+', file_name)
# #     return int(numbers) if numbers else 0


# # ==========================================================================
# # GET ALL MERGED OCR DOCUMENTS
# # ==========================================================================

# def get_merged_documents():
#     """
#     Returns every merged OCR document.

#     Example

#     08_merged_documents/
#         insurance_form/
#             insurance_form_001_raw.txt
#             insurance_form_002_raw.txt

#         discharge_summary/
#             discharge_summary_001_raw.txt
#     """

#     return sorted(

#         Path(
#             config.MERGED_DOCUMENT_DIR
#         ).rglob("*_raw.txt")

#     )

# # def extract_page_number(file_name: str) -> int:
# #     """Extracts the numeric page sequence from filenames like 'page_0.txt' or 'raw_1.txt'."""
# #     numbers = re.findall(r'\d+', file_name)
# #     # FIX: Select the first element in the numbers list before passing to int()
# #     return int(numbers[0]) if numbers else 0


# def get_user_routing_choice() -> bool:
#     """Displays an interactive menu inside the terminal window to route processing behavior."""
#     print("\n" + "=" * 50)
#     print("  Enterprise Pipeline Processing Mode Selection")
#     print("=" * 50)
#     print(" [1] CONTINUE   - Skip existing JSON files, pick up where it stopped.")
#     print(" [2] RE-EXTRACT - Wipe old data and process everything from Page 1.")
#     print("=" * 50)
    
#     while True:
#         choice = input("Please enter your choice option (1 or 2): ").strip()
#         if choice == "1":
#             print("\n>>> Selected Selection: CONTINUE (Idempotency mode enabled)\n")
#             return False  # Do NOT force reprocessing (respect skip guards)
#         elif choice == "2":
#             confirm = input("Are you absolutely sure you want to overwrite previous runs? (y/n): ").strip().lower()
#             if confirm == "y":
#                 print("\n>>> Selected Selection: RE-EXTRACT (Overwriting old files)\n")
#                 return True  # Force reprocessing (bypass skip guards)
#             else:
#                 print("\nOperation cancelled. Please select option again.")
#         else:
#             print("Invalid input. Please enter exactly 1 or 2.")

# def process_pipeline():
#     # 1. Trigger interactive terminal gateway options
#     force_reprocess_active = get_user_routing_choice()

#     logging.info("======= Commencing Production Medical IDP Pipeline =======")
    
#     # if not os.path.exists(config.RAW_DIR):
#     #     logging.error(f"Input OCR Directory not found at: {config.RAW_DIR}")
#     #     return
    
#     if not os.path.exists(config.MERGED_DOCUMENT_DIR):
#         logging.error(
#             f"Merged OCR Directory not found at: {config.MERGED_DOCUMENT_DIR}"
#         )
#         return

#     # raw_files = sorted([f for f in os.listdir(config.RAW_DIR) if f.endswith(config.INPUT_EXTENSION)])

#     raw_files = sorted(
#         Path(config.MERGED_DOCUMENT_DIR).rglob(f"*{config.INPUT_EXTENSION}")
#     )
#     total_files = len(raw_files)
    
#     logging.info(f"Identified {total_files} text files ready for parsing processing.")

#     for idx, file_name in enumerate(raw_files):
#         output_name = file_name.stem.replace("_raw", "")
        
#         # Output layout: result/06_llm_json/raw_json_page_no.json
#         # final_output_path = os.path.join(config.PARSED_DIR, f"raw_json_{output_name}{config.OUTPUT_EXTENSION}")


#         final_output_path = os.path.join(
#             config.PARSED_DIR,
#             output_name + config.OUTPUT_EXTENSION
#         )

#         # input_txt_path = os.path.join(config.RAW_DIR, file_name)
#         input_txt_path = str(file_name)
        
#         # 2. Dynamic Routing Logic Selection Checks
#         if os.path.exists(final_output_path):
#             if not force_reprocess_active:
#                 # Option 1: Continue mode (Skip files already present)
#                 logging.info(f"[{idx+1}/{total_files}] Page {output_name} already processed. Skipping.")
#                 continue
#             else:
#                 # Option 2: Re-extract mode (Overwrite existing files)
#                 logging.info(f"[{idx+1}/{total_files}] Force re-parsing Page {output_name} (Overwriting old run)...")
#         else:
#             # logging.info(f"[{idx+1}/{total_files}] Processing file: {file_name} -> target page {page_num}...")
#             logging.info(
#                 f"[{idx+1}/{total_files}] Processing {file_name.name}"
#             )
        
#         # 3. Read Content asset strings
#         with open(input_txt_path, "r", encoding=config.JSON_ENCODING) as f:
#             raw_text = f.read()
            
#         # 4. Empty Page Protection Check
#         if utils.is_page_blank(raw_text):
#             logging.info(f"Page {output_name} validation confirmed blank page conditions. Writing metadata placeholder.")
#             # blank_json = utils.create_blank_page_json(output_name)
#             blank_json = {
#                 "document_name": output_name,
#                 "status": "blank_document"
#             }
#             utils.save_json_atomically(final_output_path, blank_json)
#             continue
            
#         # 5. Token Bounds Truncation Protection
#         if len(raw_text) > config.MAX_CHARS:
#             logging.warning(f"Page {output_name} data ceiling exceeded. Applying safe structural truncation updates.")
#             raw_text = raw_text[:config.MAX_CHARS] + "\n[DATA CEILING TRUNCATION APPLIED]"

#         with open(input_txt_path, "r", encoding=config.JSON_ENCODING) as f:
#             raw_text = f.read()


#         # 6. Prompt Injection setup
#         # user_prompt = prompt.get_user_prompt(output_name, raw_text)
#         document_type = file_name.parent.name

#         pages_match = re.search(
#             r"PAGES INCLUDED\s*:\s*(\[.*?\])",
#             raw_text
#         )

#         if pages_match:
#             pages_processed = pages_match.group(1)
#         else:
#             pages_processed = "Unknown"

#         pages_processed = []
#         user_prompt = prompt.get_user_prompt(
#             document_type=document_type,
#             pages_processed=pages_processed,
#             merged_text=raw_text
#         )
        
#         # 7. Execute resilient call loops
#         try:
#             api_start = time.time()
#             api_response = llm_client.call_groq_with_resilience(prompt.SYSTEM_PROMPT, user_prompt)
#             raw_json_string = api_response.choices[0].message.content
            
#             # Check parsing parameters
#             parsed_payload = json.loads(raw_json_string)
            
#             # Add audit trails
#             parsed_payload["model"] = config.MODEL_NAME
#             parsed_payload["prompt_version"] = config.PROMPT_VERSION
#             parsed_payload["processed_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
#             parsed_payload["usage"] = {
#                 "prompt_tokens": api_response.usage.prompt_tokens,
#                 "completion_tokens": api_response.usage.completion_tokens
#             }
            
#             # 8. Commit data atomically
#             utils.save_json_atomically(final_output_path, parsed_payload)
#             # logging.info(f"Successfully finalized page tracking array index {output_name} in {round(time.time() - api_start, 2)}s.")
#             logging.info(
#                 f"Successfully extracted JSON for {output_name} "
#                 f"in {round(time.time()-api_start,2)} seconds."
#             )


#         except json.JSONDecodeError:
#             logging.error(f"❌ Core Formatting Exception: Invalid structural text string returned on Document {output_name}.")
#         except Exception as loop_fault:
#             logging.error(f"❌ System Exception fault detected on Document {output_name}: {loop_fault}")
            
#         # 9. Garbage Collection cleanup rules matching config boundaries
#         if config.DELETE_INTERMEDIATE_OBJECTS:
#             try:
#                 del raw_text
#                 del user_prompt
#                 del api_response
#                 del raw_json_string
#                 del parsed_payload
#             except NameError:
#                 pass
                
#         if config.ENABLE_GARBAGE_COLLECTION:
#             gc.collect()
            
#         # 10. Execute API delay loop window
#         time.sleep(config.API_PACING_DELAY)

#     logging.info("======= Enterprise Medical IDP Pipeline Complete =======")

# if __name__ == "__main__":
#     process_pipeline()




import os
import gc
import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path

from . import (
    config,
    prompt,
    utils,
    llm_client
)


def get_merged_documents():
    """Returns every merged OCR document path sequentially."""
    return sorted(Path(config.MERGED_DOCUMENT_DIR).rglob("*_raw.txt"))

def get_user_routing_choice() -> bool:
    """Displays an interactive menu inside the terminal window to route processing behavior."""
    print("\n" + "=" * 50)
    print("  Enterprise Pipeline Processing Mode Selection")
    print("=" * 50)
    print(" [1] CONTINUE   - Skip existing JSON files, pick up where it stopped.")
    print(" [2] RE-EXTRACT - Wipe old data and process everything from Page 1.")
    print("=" * 50)
    
    while True:
        choice = input("Please enter your choice option (1 or 2): ").strip()
        if choice == "1":
            print("\n>>> Selected Selection: CONTINUE (Idempotency mode enabled)\n")
            return False  
        elif choice == "2":
            confirm = input("Are you absolutely sure you want to overwrite previous runs? (y/n): ").strip().lower()
            if confirm == "y":
                print("\n>>> Selected Selection: RE-EXTRACT (Overwriting old files)\n")
                return True  
            else:
                print("\nOperation cancelled. Please select option again.")
        else:
            print("Invalid input. Please enter exactly 1 or 2.")

def run_extraction_pipeline(force_reprocess_active: bool = None):
    """
    Core IDP processing module designed to be executed directly 
    or called programmatically by a master coordinator script.
    """
    # If not passed programmatically by main.py, trigger terminal fallback menu
    if force_reprocess_active is None:
        force_reprocess_active = get_user_routing_choice()

    logging.info("======= Commencing Production Medical IDP Pipeline =======")
    
    if not os.path.exists(config.MERGED_DOCUMENT_DIR):
        logging.error(f"Merged OCR Directory not found at: {config.MERGED_DOCUMENT_DIR}")
        return

    raw_files = get_merged_documents()
    total_files = len(raw_files)
    
    logging.info(f"Identified {total_files} text files ready for parsing processing.")

    for idx, file_name in enumerate(raw_files):
        output_name = file_name.stem.replace("_raw", "")
        final_output_path = os.path.join(config.PARSED_DIR, output_name + config.OUTPUT_EXTENSION)
        input_txt_path = str(file_name)
        
        # 2. Dynamic Routing Logic Selection Checks
        if os.path.exists(final_output_path):
            if not force_reprocess_active:
                logging.info(f"[{idx+1}/{total_files}] Page {output_name} already processed. Skipping.")
                continue
            else:
                logging.info(f"[{idx+1}/{total_files}] Force re-parsing Page {output_name} (Overwriting old run)...")
        else:
            logging.info(f"[{idx+1}/{total_files}] Processing {file_name.name}")
        
        # 3. Read Content asset strings
        with open(input_txt_path, "r", encoding=config.JSON_ENCODING) as f:
            raw_text = f.read()
            
        # 4. Empty Page Protection Check
        if utils.is_page_blank(raw_text):
            logging.info(f"Page {output_name} validation confirmed blank conditions. Writing placeholder.")
            blank_json = {
                "document_name": output_name,
                "status": "blank_document"
            }
            utils.save_json_atomically(final_output_path, blank_json)
            continue
            
        # 5. Token Bounds Truncation Protection
        if len(raw_text) > config.MAX_CHARS:
            logging.warning(f"Page {output_name} data ceiling exceeded. Applying safe truncation updates.")
            raw_text = raw_text[:config.MAX_CHARS] + "\n[DATA CEILING TRUNCATION APPLIED]"
            
        # 6. Prompt Injection setup
        document_type = file_name.parent.name

        # Regular Expression to dynamically capture array elements
        pages_match = re.search(r"PAGES INCLUDED\s*:\s*\[(.*?)\]", raw_text)
        if pages_match:
            # Split items by comma, remove whitespace and quotes to build a clean numeric array
            pages_processed = [int(p.strip()) for p in pages_match.group(1).split(",") if p.strip().isdigit()]
        else:
            pages_processed = []

        user_prompt = prompt.get_user_prompt(
            document_type=document_type,
            pages_processed=pages_processed,
            merged_text=raw_text
        )
        
        # 7. Execute resilient call loops
        try:
            api_start = time.time()
            api_response = llm_client.call_groq_with_resilience(prompt.SYSTEM_PROMPT, user_prompt)
            
            # FIX: Use dot-notation access to standard choices attributes to prevent TypeErrors
            raw_json_string = api_response.choices[0].message.content
            
            # Check parsing parameters
            parsed_payload = json.loads(raw_json_string)
            
            # Add audit trails
            parsed_payload["model"] = config.MODEL_NAME
            parsed_payload["prompt_version"] = config.PROMPT_VERSION
            parsed_payload["processed_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            parsed_payload["usage"] = {
                "prompt_tokens": api_response.usage.prompt_tokens,
                "completion_tokens": api_response.usage.completion_tokens
            }
            
            # 8. Commit data atomically
            utils.save_json_atomically(final_output_path, parsed_payload)
            logging.info(f"Successfully extracted JSON for {output_name} in {round(time.time() - api_start, 2)} seconds.")

        except json.JSONDecodeError:
            logging.error(f"❌ Core Formatting Exception: Invalid structural text string returned on Document {output_name}.")
        except Exception as loop_fault:
            logging.error(f"❌ System Exception fault detected on Document {output_name}: {loop_fault}")
            
    logging.info("======= Enterprise Medical IDP Pipeline Complete =======")

# Retain ability to run independently by hitting this execution entrypoint block directly
if __name__ == "__main__":
    run_extraction_pipeline()

# # =========================================================
# # main.py
# # UNIVERSAL HEALTHCARE IDP PLATFORM
# # =========================================================

# import os
# import json
# import traceback

# from OCR_Extraction_folder.pdf_converter         import convert_pdf_to_images
# from OCR_Extraction_folder.image_preprocessing   import preprocess_image
# from OCR_Extraction_folder.multimodal_extractor  import multimodal_extract
# from OCR_Extraction_folder.layout_block_detection import detect_layout
# from OCR_Extraction_folder.text_cleaner          import clean_ocr_text
# from Entity_KV_JSON.document_classifier   import classify_document
# from Entity_KV_JSON.entity_extractor      import extract_entities
# from Entity_KV_JSON.document_grouper      import group_document_pages
# from OCR_Extraction_folder.ocr_merge_engine      import build_structured_document
# from Entity_KV_JSON.entity_validator      import validate_entities
# from OCR_Extraction_folder.ocr_merge_engine      import merge_page_blocks_ocr
# from core.entity_consolidator import consolidate_entities

# from OCR_Extraction_folder.table_grid_detector import (
#     detect_table_cells,
#     assign_ocr_to_cells
# )

# # from Entity_KV_JSON.document_template_engine import apply_document_template
# from Entity_KV_JSON.confidence_engine        import build_confidence_report
# from Entity_KV_JSON.entity_postprocessor     import postprocess_entities

# from Entity_KV_JSON.review_engine import (
#     needs_human_review,
#     build_review_record,
#     save_review_record
# )

# from Entity_KV_JSON.learning_engine import (
#     load_learning_data,
#     apply_learning_corrections,
#     save_learning_data,
#     update_learning_data
# )

# from extraction.kv_mapper import map_key_values
# from core.semantic_normalizer import normalize_kv_pairs
# from futher_addition.word_exporter import save_to_word
# from Entity_KV_JSON.document_builder import build_master_record



# # =========================================================
# # CONFIGURATION
# # =========================================================

# PDF_PATH              = "TEST_PDF/20260408B007GH00802.pdf"
# TEST_MODE             = True
# MAX_PAGES             = 1
# ENABLE_LAYOUT_DETECTION  = True
# ENABLE_FULL_PAGE_OCR     = True


# # =========================================================
# # PDF NAME + OUTPUT PATHS
# # =========================================================

# pdf_name = os.path.splitext(os.path.basename(PDF_PATH))[0]

# BASE_OUTPUT = os.path.join("RESULT", pdf_name)

# FOLDERS = {
#     "images":         os.path.join(BASE_OUTPUT, "01_images"),
#     "enhanced":       os.path.join(BASE_OUTPUT, "02_enhanced"),
#     "layout":         os.path.join(BASE_OUTPUT, "03_layout"),
#     "regions":        os.path.join(BASE_OUTPUT, "04_regions"),
#     "ocr":            os.path.join(BASE_OUTPUT, "05_ocr"),
#     "structured":     os.path.join(BASE_OUTPUT, "06_structured"),
#     "cleaned":        os.path.join(BASE_OUTPUT, "07_cleaned"),
#     "merge_output":   os.path.join(BASE_OUTPUT, "08_merge_output"),
#     "classification": os.path.join(BASE_OUTPUT, "09_classification"),
#     "entities":       os.path.join(BASE_OUTPUT, "10_entities"),
#     "final":          os.path.join(BASE_OUTPUT, "11_final"),
#     "reviews":        os.path.join(BASE_OUTPUT, "12_reviews"),
#     "learning":       os.path.join(BASE_OUTPUT, "13_learning"),
#     "word":           os.path.join(BASE_OUTPUT, "14_word")
# }

# for folder in FOLDERS.values():
#     os.makedirs(folder, exist_ok=True)


# # =========================================================
# # LOAD LEARNING DATA
# # =========================================================

# LEARNING_FILE = os.path.join(
#     FOLDERS["learning"], "learning_data.json"
# )

# learning_data = load_learning_data(LEARNING_FILE)


# # =========================================================
# # STEP 1 → PDF TO IMAGES
# # =========================================================

# print("\nConverting PDF to Images...\n")

# image_paths = convert_pdf_to_images(
#     pdf_path=PDF_PATH,
#     output_folder=FOLDERS["images"]
# )

# if TEST_MODE:
#     image_paths = image_paths[:MAX_PAGES]


# # =========================================================
# # PROCESS EACH PAGE
# # =========================================================

# processed_pages = []

# for idx, image_path in enumerate(image_paths):

#     page_no = idx + 1

#     print("\n" + "=" * 70)
#     print(f"PROCESSING PAGE {page_no}")
#     print("=" * 70)

#     try:

#         # =============================================
#         # STEP 2 → PREPROCESS
#         # =============================================

#         print("\nSTEP 2 → PREPROCESSING")

#         enhanced_image = preprocess_image(
#             image_path=image_path,
#             output_folder=FOLDERS["enhanced"]
#         )

#         # =============================================
#         # STEP 3 → LAYOUT DETECTION
#         # =============================================

#         region_outputs = []

#         if ENABLE_LAYOUT_DETECTION:

#             print("\nSTEP 3 → LAYOUT DETECTION")

#             layout_result = detect_layout(
#                 image_path=enhanced_image,
#                 layout_output_folder=FOLDERS["layout"],
#                 cropped_output_folder=FOLDERS["regions"]
#             )

#             cropped_regions = layout_result["cropped_regions"]

#         else:
#             cropped_regions = []

#         # =============================================
#         # STEP 4 → REGION OCR
#         # =============================================

#         print("\nSTEP 4 → REGION OCR")

#         for region in cropped_regions:

#             region_path = region["path"]
#             region_type = region["type"]

#             if region_type.lower() == "figure":
#                 continue

#             print(f"\nOCR → {region_type} → {region_path}")

#             ocr_result = multimodal_extract(
#                 image_path=region_path,
#                 output_folder=FOLDERS["ocr"]
#             )

#             parsed_table = None

#             if region_type.lower() == "table":
#                 try:
#                     cells = detect_table_cells(region_path)
#                     structured_cells = assign_ocr_to_cells(
#                         cells, ocr_result["ocr_data"]
#                     )
#                     parsed_table = structured_cells
#                 except Exception as e:
#                     print(f"Table Error: {e}")

#             region_outputs.append({
#                 "type":         region_type,
#                 "image_path":   region_path,
#                 "ocr":          ocr_result,
#                 "parsed_table": parsed_table
#             })

#         # =============================================
#         # STEP 5 → FULL PAGE OCR
#         # =============================================

#         full_page_ocr = None

#         if ENABLE_FULL_PAGE_OCR:
#             print("\nSTEP 5 → FULL PAGE OCR")
#             full_page_ocr = multimodal_extract(
#                 image_path=enhanced_image,
#                 output_folder=FOLDERS["ocr"]
#             )

#         page_name = os.path.splitext(
#             os.path.basename(image_path)
#         )[0]

#         # =============================================
#         # STEP 6 → BUILD STRUCTURED DOCUMENT
#         # =============================================

#         print("\nSTEP 6 → STRUCTURED DOCUMENT")

#         structured_document = build_structured_document(
#             page_name=page_name,
#             region_outputs=region_outputs,
#             output_folder=FOLDERS["structured"],
#             fallback_ocr=full_page_ocr
#         )

#         indexed_tokens = structured_document.get(
#             "indexed_tokens", []
#         )

#         # =============================================
#         # KV MAPPING — pass page_no for tracking
#         # =============================================

#         kv_pairs = map_key_values(
#             indexed_tokens,
#             page=page_no          # ← page number now flows in
#         )

#         # =============================================
#         # SEMANTIC NORMALIZATION
#         # =============================================

#         print("\n========================")
#         print("RAW KV PAIRS")
#         print("========================")

#         for kv in kv_pairs:
#             print(kv)

#         print("========================")

#         print("\n========================")
#         print("\nRAW KV LABELS")
#         print("========================")

#         for kv in kv_pairs:
#             print(
#                 kv.get("field"),
#                 "=>",
#                 kv.get("value")
#             )


            
#         normalized_kv_pairs = normalize_kv_pairs(kv_pairs)

#         for kv in normalized_kv_pairs[:3]:
#             print(kv)


#         print("\nFIRST NORMALIZED KV")

#         for kv in normalized_kv_pairs[:5]:
#             print(kv)

#         # print("\n========================")
#         # print("NORMALIZED KV PAIRS")
#         # print("========================")

#         # for kv in normalized_kv_pairs:

#         #     print(
#         #         kv.get("normalized_label"),
#         #         "=>",
#         #         kv.get("value")
#         #     )

#         # =============================================
#         # OCR TEXT
#         # =============================================

#         if full_page_ocr is not None:
#             raw_text = full_page_ocr["text"]
#         else:
#             raw_text = structured_document["full_page_ocr"]["text"]

#         if len(raw_text.strip()) < 50 and full_page_ocr is not None:
#             raw_text = full_page_ocr["text"]

#         page_blocks_ocr = merge_page_blocks_ocr(region_outputs)

#         merge_file = os.path.join(
#             FOLDERS["merge_output"], f"page_{page_no}.txt"
#         )

#         with open(merge_file, "w", encoding="utf-8") as f:
#             f.write(page_blocks_ocr["text"])

#         # =============================================
#         # STEP 7 → CLEAN TEXT
#         # =============================================

#         print("\nSTEP 7 → CLEAN OCR TEXT")

#         cleaned_text = clean_ocr_text(raw_text)

#         cleaned_file = os.path.join(
#             FOLDERS["cleaned"], f"page_{page_no}.txt"
#         )

#         with open(cleaned_file, "w", encoding="utf-8") as f:
#             f.write(cleaned_text)

#         word_file = os.path.join(
#             FOLDERS["word"], f"page_{page_no}.docx"
#         )

#         save_to_word(
#             text=cleaned_text,
#             output_path=word_file,
#             document_title=f"Page {page_no}"
#         )

#         # =============================================
#         # STEP 8 → DOCUMENT CLASSIFICATION
#         # =============================================

#         print("\nSTEP 8 → DOCUMENT CLASSIFICATION")

#         classification  = classify_document(cleaned_text)

#         # print("\nCLASSIFICATION RESULT")
#         # print(json.dumps(classification, indent=2))

#         document_type   = classification["document_type"]

#         classification_file = os.path.join(
#             FOLDERS["classification"], f"page_{page_no}.json"
#         )

#         with open(classification_file, "w", encoding="utf-8") as f:
#             json.dump(classification, f, indent=4, ensure_ascii=False)

        

#         # =============================================
#         # STEP 9 → ENTITY EXTRACTION
#         # =============================================
#         print("\nSTEP 9 → ENTITY EXTRACTION")

#         print("\n===== NORMALIZED KV PAIRS =====")

#         for kv in normalized_kv_pairs:

#             if kv.get("field") == "tpa_name":
#                 print(kv)

#         print("===============================")

#         from NEW_VERSION.universal_entity_extractor import (
#             extract_entities_universal
#         )

#         # ------------------------------------------------
#         # DOCUMENT TEMPLATE EXTRACTION
#         # ------------------------------------------------

#         template_entities = extract_entities(
#             cleaned_text,
#             document_type,
#             normalized_kv_pairs,
#             page=page_no
#         )

#         from Entity_KV_JSON.entity_resolver import resolve_context_entities

#         # ------------------------------------------------
#         # UNIVERSAL FALLBACK EXTRACTION
#         # ------------------------------------------------

#         entities = template_entities.copy()

#         universal_entities = {}

#         universal_entities = extract_entities_universal(
#             text=cleaned_text,
#             kv_pairs=normalized_kv_pairs,
#             page=page_no
#         )


#         print("\nSTEP 1 - AFTER EXTRACTION")
#         print(entities.get("helpline_number"))


#         print("\n===== UNIVERSAL ENTITIES =====")

#         for field, obj in universal_entities.items():

#             print(
#                 f"{field} = {obj['value']}"
#             )

#         print("=============================\n")

#         # # Context Resolver fill
#         # for field, obj in context_entities.items():

#         #     if field not in entities:
#         #         entities[field] = obj

#         # ------------------------------------------------
#         # FINAL MERGE
#         # Template always wins
#         # Universal fills missing fields
#         # ------------------------------------------------

#         entities = template_entities.copy()

#         for field, obj in universal_entities.items():

#             if field not in entities:

#                 entities[field] = obj

#         print(
#             f"Template Fields: {len(template_entities)} | "
#             f"Universal Fields: {len(universal_entities)} | "
#             f"Final Fields: {len(entities)}"
#         )

#         print("\nFINAL ENTITY KEYS")

#         from core.template_json_builder import (
#             build_template_json
#         )

#         print("\nSTEP 2 - BEFORE TEMPLATE")
#         print(entities.get("helpline_number"))

#         structured_entities, extra_entities = (

#             build_template_json(

#                 document_type=document_type,
#                 entities=entities

#             )
#         )

#         print("\nSTEP 3 - AFTER TEMPLATE")
#         print(structured_entities.get("helpline_number"))

#         # for k in structured_entities.keys():
#         #     print(k)

#         print("\nSTRUCTURED ENTITIES")
#         print(type(structured_entities))

#         if isinstance(structured_entities, dict):
#             print("COUNT =", len(structured_entities))
#             print("KEYS =", list(structured_entities.keys())[:20])

#         print("\nEXTRA ENTITIES")
#         print(type(extra_entities))

#         print("\nEXTRA ENTITY KEYS")

#         for k in extra_entities.keys():
#             print(k)

#         if isinstance(extra_entities, dict):
#             print("COUNT =", len(extra_entities))

#         entities = structured_entities


#         print("\nDEBUG STEP 9")

#         for k, v in entities.items():

#             print(
#                 k,
#                 type(v)
#             )

#             if isinstance(v, dict):
#                 print("VALUE TYPE:", type(v.get("value")))
    

#         # =============================================
#         # VALIDATION
#         # =============================================
#         print("\nSTEP 4 - BEFORE VALIDATION")
#         print(entities.get("helpline_number"))


#         validation_results = validate_entities(
#             {
#                 k: (
#                     v.get("value")
#                     if isinstance(v, dict)
#                     else v
#                 )
#                 for k, v in entities.items()
#             }
#         )
#         print("\nTPA AFTER MAIN VALIDATION")
#         print(entities.get("tpa_name"))


#         for result in validation_results:
#             field = result["field"]

#             if (
#                 field in entities
#                 and isinstance(entities[field], dict)
#             ):
#                 entities[field]["status"] = result["status"]
#                 entities[field]["message"] = result["message"]
            

#         print("\nVALIDATION RESULT FOR TPA")

#         for r in validation_results:

#             if r["field"] == "tpa_name":
#                 print(r)

#         entities = postprocess_entities(
#             entities,
#             document_type
#         )

#         print("\nSTEP 5 - AFTER VALIDATION")
#         print(entities.get("helpline_number"))

#         # =============================================
#         # POST PROCESSING
#         # =============================================

#         entities = postprocess_entities(
#             entities, document_type
#         )

#         print("\nAFTER POSTPROCESS")

#         for k, v in entities.items():

#             print(
#                 k,
#                 type(v)
#             )

        
        
        

    
#         # =============================================
#         # LEARNING ENGINE
#         # =============================================

#         learning_data = update_learning_data(
#             learning_data=learning_data,
#             document_type=document_type,
#             entities={
#                 k: v.get("value") if isinstance(v, dict) else v
#                 for k, v in entities.items()
#             },
#             kv_pairs=normalized_kv_pairs
#         )

#         print("\nBEFORE SAVE")

#         print(
#             entities.get("claim_number")
#         )

#         print(
#             type(
#                 entities.get("claim_number")
#             )
#         )

#         save_learning_data(LEARNING_FILE, learning_data)

#         # entities = apply_learning_corrections(
#         #     document_type=document_type,
#         #     entities=entities,
#         #     learning_data=learning_data
#         # )

#         print("\nAFTER LEARNING")

#         # for k, v in entities.items():

#         #     print(
#         #         k,
#         #         type(v)
#         #     )

#         #     if isinstance(v, dict):
#         #         print("VALUE =", v.get("value"))

#         # =============================================
#         # CONFIDENCE REPORT
#         # =============================================

#         confidence_report = build_confidence_report(
#             metadata=[],
#             entities=entities,
#             classification_result=classification,
#             validation_result=validation_results
#         )

#         print(
#             "\nDOCUMENT CONFIDENCE:",
#             confidence_report["final_confidence"]
#         )

#         # =============================================
#         # HUMAN REVIEW CHECK
#         # =============================================

#         review_required = needs_human_review(confidence_report)
#         review_record   = None

#         if review_required:

#             print("\nLOW CONFIDENCE → HUMAN REVIEW REQUIRED")

#             review_record = build_review_record(
#                 page_number=page_no,
#                 document_type=document_type,
#                 confidence_report=confidence_report,
#                 entities=entities,
#                 cleaned_text=cleaned_text
#             )

#             review_path = save_review_record(
#                 review_record, FOLDERS["reviews"]
#             )

#             print(f"Review File Saved → {review_path}")

#         # =============================================
#         # REMOVE EMPTY ENTITIES
#         # =============================================
#         print("\nSTEP 6 - BEFORE FILTER")
#         print(entities.get("helpline_number"))


#         filtered_entities = {
#             k: v
#             for k, v in entities.items()
#             if not (
#                 isinstance(v, dict)
#                 and v.get("value") is None
#             )
#         }

#         print("\nBEFORE FILTER =", len(entities))
#         print("AFTER FILTER =", len(filtered_entities))

#         print("\nSTEP 7 - AFTER FILTER")
#         print(filtered_entities.get("helpline_number"))

        
#         # =============================================
#         # SAVE ENTITIES
#         # =============================================

#         entity_file = os.path.join(
#             FOLDERS["entities"], f"page_{page_no}.json"
#         )

#         with open(entity_file, "w", encoding="utf-8") as f:
#             json.dump(
#                 filtered_entities,
#                 f,
#                 indent=4,
#                 ensure_ascii=False
#             )

#         print(f"\nEntities Saved → {entity_file}")

#         # =============================================
#         # STEP 10 → PER-PAGE FINAL OUTPUT
#         # =============================================

#         print("\nSTEP 10 → PER-PAGE FINAL OUTPUT")

#         final_output = {
#             "page_number":        page_no,
#             "document_type":      document_type,
#             "classification":     classification,
#             "entities":           entities,       # full field objects
#             "extra_entities": extra_entities,
#             "raw_text":           raw_text,
#             "cleaned_text":       cleaned_text,
#             "confidence_report":  confidence_report,
#             "structured_document": structured_document,
#             "review_required":    review_required,
#             "review_record":      review_record
#         }

#         final_json_path = os.path.join(
#             FOLDERS["final"], f"page_{page_no}_final.json"
#         )

#         processed_pages.append(final_output)

#         with open(final_json_path, "w", encoding="utf-8") as f:
#             json.dump(
#                 final_output, f, indent=4, ensure_ascii=False
#             )

#         print(f"\nPER-PAGE JSON SAVED → {final_json_path}")


#     except Exception as e:
#         print(f"\nERROR ON PAGE {page_no}")
#         traceback.print_exc()


# # =========================================================
# # STEP 11 → GROUP PAGES BY DOCUMENT TYPE
# # =========================================================

# print("\nSTEP 11 → GROUPING DOCUMENT PAGES")

# grouped_documents = group_document_pages(processed_pages)

# grouped_output_path = os.path.join(
#     FOLDERS["final"], "grouped_documents.json"
# )

# with open(grouped_output_path, "w", encoding="utf-8") as f:
#     json.dump(
#         grouped_documents, f, indent=4, ensure_ascii=False
#     )

# print(f"\nGrouped Documents Saved → {grouped_output_path}")


# # =========================================================
# # STEP 12 → ENTITY CONSOLIDATION
# # =========================================================

# print("\nSTEP 12 → CONSOLIDATING ENTITIES")

# final_documents = consolidate_entities(grouped_documents)

# consolidated_output_path = os.path.join(
#     FOLDERS["final"], "consolidated_documents.json"
# )

# with open(consolidated_output_path, "w", encoding="utf-8") as f:
#     json.dump(
#         final_documents, f, indent=4, ensure_ascii=False
#     )

# print(f"\nConsolidated Documents Saved → {consolidated_output_path}")


# # =========================================================
# # STEP 13 → BUILD UNIVERSAL HEALTHCARE JSON
# # =========================================================

# print("\nSTEP 13 → BUILDING MASTER RECORD")

# master_record = build_master_record(
#     final_documents,
#     source_file=PDF_PATH
# )

# master_record_path = os.path.join(
#     FOLDERS["final"],
#     "master_document_record.json"
# )

# with open(
#     master_record_path,
#     "w",
#     encoding="utf-8"
# ) as f:

#     json.dump(
#         master_record,
#         f,
#         indent=4,
#         ensure_ascii=False
#     )

# print(
#     f"\nMASTER RECORD SAVED → "
#     f"{master_record_path}"
# )



# # # =========================================================
# # # STEP 14 → Build Frontend Documents
# # # =========================================================


# # print("\nSTEP 14 → BUILDING FRONTEND DOCUMENTS")

# # from Entity_KV_JSON.form_template_mapper import (
# #     map_all_documents
# # )

# # frontend_documents = map_all_documents(
# #     final_documents
# # )

# # frontend_json_path = os.path.join(
# #     FOLDERS["final"],
# #     "frontend_documents.json"
# # )

# # with open(
# #     frontend_json_path,
# #     "w",
# #     encoding="utf-8"
# # ) as f:

# #     json.dump(
# #         frontend_documents,
# #         f,
# #         indent=4,
# #         ensure_ascii=False
# #     )

# # print(
# #     f"\nFRONTEND DOCUMENTS SAVED → "
# #     f"{frontend_json_path}"
# # )

# # # ─────────────────────────────────────────────────────────
# # # Save master_patient_record.json
# # # This is the single output the frontend consumes.
# # # Every template tab reads from this one file.
# # # ─────────────────────────────────────────────────────────

# # master_record_path = os.path.join(
# #     FOLDERS["final"], "master_patient_record.json"
# # )

# # with open(master_record_path, "w", encoding="utf-8") as f:
# #     json.dump(
# #         master_record, f, indent=4, ensure_ascii=False
# #     )

# # print(f"\nMASTER PATIENT RECORD SAVED → {master_record_path}")

# # # Also save as claim_case.json for backward compatibility
# # claim_case_path = os.path.join(
# #     FOLDERS["final"], "claim_case.json"
# # )

# # with open(claim_case_path, "w", encoding="utf-8") as f:
# #     json.dump(
# #         master_record, f, indent=4, ensure_ascii=False
# #     )

# # =========================================================
# # PIPELINE SUMMARY
# # =========================================================

# summary = master_record.get("_extraction_summary", {})

# print("\n" + "=" * 70)
# print("UNIVERSAL HEALTHCARE IDP PIPELINE COMPLETE")
# print("=" * 70)
# print(f"Source PDF:          {PDF_PATH}")
# print(f"Pages Processed:     {len(processed_pages)}")
# print(f"Document Types Found:{len(final_documents)}")
# print(f"Fields Filled:       {summary.get('filled_fields', 'N/A')}")
# print(f"Fields Missing:      {summary.get('missing_fields', 'N/A')}")
# print(f"Completion:          {summary.get('completion_percent', 'N/A')}%")
# print(f"Low Confidence:      {summary.get('low_confidence', 'N/A')}")
# print(f"\nOUTPUT → {master_record_path}")
# print("=" * 70)






















# # # =========================================================
# # # main.py
# # # UNIVERSAL HEALTHCARE IDP PLATFORM
# # # =========================================================

# # import os
# # import json
# # import traceback

# # from OCR_Extraction_folder.pdf_converter         import convert_pdf_to_images
# # from OCR_Extraction_folder.image_preprocessing   import preprocess_image
# # from OCR_Extraction_folder.multimodal_extractor  import multimodal_extract
# # from OCR_Extraction_folder.layout_block_detection import detect_layout
# # from OCR_Extraction_folder.text_cleaner          import clean_ocr_text
# # from Entity_KV_JSON.document_classifier   import classify_document
# # from Entity_KV_JSON.entity_extractor      import extract_entities
# # from Entity_KV_JSON.document_grouper      import group_document_pages
# # from OCR_Extraction_folder.ocr_merge_engine      import build_structured_document
# # from Entity_KV_JSON.entity_validator      import validate_entities
# # from OCR_Extraction_folder.ocr_merge_engine      import merge_page_blocks_ocr
# # from core.entity_consolidator import consolidate_entities

# # from OCR_Extraction_folder.table_grid_detector import (
# #     detect_table_cells,
# #     assign_ocr_to_cells
# # )

# # # from Entity_KV_JSON.document_template_engine import apply_document_template
# # from Entity_KV_JSON.confidence_engine        import build_confidence_report
# # from Entity_KV_JSON.entity_postprocessor     import postprocess_entities

# # from Entity_KV_JSON.review_engine import (
# #     needs_human_review,
# #     build_review_record,
# #     save_review_record
# # )

# # from Entity_KV_JSON.learning_engine import (
# #     load_learning_data,
# #     apply_learning_corrections,
# #     save_learning_data,
# #     update_learning_data
# # )

# # from extraction.kv_mapper import map_key_values
# # from core.semantic_normalizer import normalize_kv_pairs
# # from futher_addition.word_exporter import save_to_word
# # from Entity_KV_JSON.document_builder import build_master_record



# # # =========================================================
# # # CONFIGURATION
# # # =========================================================

# # PDF_PATH              = "TEST_PDF/20260408B007GH00802.pdf"
# # TEST_MODE             = True
# # MAX_PAGES             = 1
# # ENABLE_LAYOUT_DETECTION  = True
# # ENABLE_FULL_PAGE_OCR     = True


# # # =========================================================
# # # PDF NAME + OUTPUT PATHS
# # # =========================================================

# # pdf_name = os.path.splitext(os.path.basename(PDF_PATH))[0]

# # BASE_OUTPUT = os.path.join("RESULT", pdf_name)

# # FOLDERS = {
# #     "images":         os.path.join(BASE_OUTPUT, "01_images"),
# #     "enhanced":       os.path.join(BASE_OUTPUT, "02_enhanced"),
# #     "layout":         os.path.join(BASE_OUTPUT, "03_layout"),
# #     "regions":        os.path.join(BASE_OUTPUT, "04_regions"),
# #     "ocr":            os.path.join(BASE_OUTPUT, "05_ocr"),
# #     "structured":     os.path.join(BASE_OUTPUT, "06_structured"),
# #     "cleaned":        os.path.join(BASE_OUTPUT, "07_cleaned"),
# #     "merge_output":   os.path.join(BASE_OUTPUT, "08_merge_output"),
# #     "classification": os.path.join(BASE_OUTPUT, "09_classification"),
# #     "entities":       os.path.join(BASE_OUTPUT, "10_entities"),
# #     "final":          os.path.join(BASE_OUTPUT, "11_final"),
# #     "reviews":        os.path.join(BASE_OUTPUT, "12_reviews"),
# #     "learning":       os.path.join(BASE_OUTPUT, "13_learning"),
# #     "word":           os.path.join(BASE_OUTPUT, "14_word")
# # }

# # for folder in FOLDERS.values():
# #     os.makedirs(folder, exist_ok=True)


# # # =========================================================
# # # LOAD LEARNING DATA
# # # =========================================================

# # LEARNING_FILE = os.path.join(
# #     FOLDERS["learning"], "learning_data.json"
# # )

# # learning_data = load_learning_data(LEARNING_FILE)


# # # =========================================================
# # # STEP 1 → PDF TO IMAGES
# # # =========================================================

# # print("\nConverting PDF to Images...\n")

# # image_paths = convert_pdf_to_images(
# #     pdf_path=PDF_PATH,
# #     output_folder=FOLDERS["images"]
# # )

# # if TEST_MODE:
# #     image_paths = image_paths[:MAX_PAGES]


# # # =========================================================
# # # PROCESS EACH PAGE
# # # =========================================================

# # processed_pages = []

# # for idx, image_path in enumerate(image_paths):

# #     page_no = idx + 1

# #     print("\n" + "=" * 70)
# #     print(f"PROCESSING PAGE {page_no}")
# #     print("=" * 70)

# #     try:

# #         # =============================================
# #         # STEP 2 → PREPROCESS
# #         # =============================================

# #         print("\nSTEP 2 → PREPROCESSING")

# #         enhanced_image = preprocess_image(
# #             image_path=image_path,
# #             output_folder=FOLDERS["enhanced"]
# #         )

# #         # =============================================
# #         # STEP 3 → LAYOUT DETECTION
# #         # =============================================

# #         region_outputs = []

# #         if ENABLE_LAYOUT_DETECTION:

# #             print("\nSTEP 3 → LAYOUT DETECTION")

# #             layout_result = detect_layout(
# #                 image_path=enhanced_image,
# #                 layout_output_folder=FOLDERS["layout"],
# #                 cropped_output_folder=FOLDERS["regions"]
# #             )

# #             cropped_regions = layout_result["cropped_regions"]

# #         else:
# #             cropped_regions = []

# #         # =============================================
# #         # STEP 4 → REGION OCR
# #         # =============================================

# #         print("\nSTEP 4 → REGION OCR")

# #         for region in cropped_regions:

# #             region_path = region["path"]
# #             region_type = region["type"]

# #             if region_type.lower() == "figure":
# #                 continue

# #             print(f"\nOCR → {region_type} → {region_path}")

# #             ocr_result = multimodal_extract(
# #                 image_path=region_path,
# #                 output_folder=FOLDERS["ocr"]
# #             )

# #             parsed_table = None

# #             if region_type.lower() == "table":
# #                 try:
# #                     cells = detect_table_cells(region_path)
# #                     structured_cells = assign_ocr_to_cells(
# #                         cells, ocr_result["ocr_data"]
# #                     )
# #                     parsed_table = structured_cells
# #                 except Exception as e:
# #                     print(f"Table Error: {e}")

# #             region_outputs.append({
# #                 "type":         region_type,
# #                 "image_path":   region_path,
# #                 "ocr":          ocr_result,
# #                 "parsed_table": parsed_table
# #             })

# #         # =============================================
# #         # STEP 5 → FULL PAGE OCR
# #         # =============================================

# #         full_page_ocr = None

# #         if ENABLE_FULL_PAGE_OCR:
# #             print("\nSTEP 5 → FULL PAGE OCR")
# #             full_page_ocr = multimodal_extract(
# #                 image_path=enhanced_image,
# #                 output_folder=FOLDERS["ocr"]
# #             )

# #         page_name = os.path.splitext(
# #             os.path.basename(image_path)
# #         )[0]

# #     except Exception as e:
# #         print(f"An error occurred: {e}")

# # print("\n" + "=" * 70)
# # print("UNIVERSAL HEALTHCARE IDP PIPELINE COMPLETE")
# # print("=" * 70)
# # print(f"Source PDF:          {PDF_PATH}")

















# =========================================================
# main.py
# UNIVERSAL HEALTHCARE IDP PLATFORM (OCR PIPELINE ONLY)
# =========================================================

import os
import sys
import traceback
import cv2
import json

# Dynamically add the current workspace directory to prevent ModuleNotFoundErrors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from OCR_Extraction_folder.pdf_converter         import convert_pdf_to_images
from OCR_Extraction_folder.image_preprocessing   import preprocess_image
from OCR_Extraction_folder.multimodal_extractor  import multimodal_extract
from OCR_Extraction_folder.layout_block_detection import detect_layout

from quality_assessment.analyzer import LayoutAwareQualityAnalyzer, RoutingDecision
# Ensure the path matches where you put your async fallback manager class
# from quality_assessment.fallback_manager import IDPOcrFallbackManager 



# =========================================================
# CONFIGURATION
# =========================================================

PDF_PATH                 = "TEST_PDF/MEDSAVE.pdf"
TEST_MODE                = True
# MAX_PAGES                = 10
# TEST_PAGES               = []
ENABLE_FULL_PAGE_OCR     = True
ENABLE_LAYOUT_DETECTION  = True


# =========================================================
# PDF NAME + OUTPUT PATHS
# =========================================================

pdf_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
BASE_OUTPUT = os.path.join("RESULT", pdf_name)

FOLDERS = {
    "images":         os.path.join(BASE_OUTPUT, "01_images"),
    "enhanced":       os.path.join(BASE_OUTPUT, "02_enhanced"),
    "ocr":            os.path.join(BASE_OUTPUT, "05_ocr"),
    "layout":         os.path.join(BASE_OUTPUT, "03_layout"),
    "regions":        os.path.join(BASE_OUTPUT, "04_regions"),
    "classification": os.path.join(BASE_OUTPUT, "06_document_classification"),
}

for folder in FOLDERS.values():
    os.makedirs(folder, exist_ok=True)


# =========================================================
# STEP 1 → PDF TO IMAGES
# =========================================================

print("\nConverting PDF to Images...\n")

image_paths = convert_pdf_to_images(
    pdf_path=PDF_PATH,
    output_folder=FOLDERS["images"]
)

# if TEST_MODE:
#     image_paths = image_paths[:MAX_PAGES]


# # =========================================================
# # TEST PAGES ONLY
# # =========================================================

# selected_pages = [

#     (
#         page_no - 1,     # idx
#         page_no,         # actual page number
#         image_paths[page_no - 1]
#     )

#     for page_no in TEST_PAGES

#     if page_no <= len(image_paths)

# ]


# =========================================================
# PROCESS EACH PAGE
# =========================================================

processed_pages = []

analyzer = LayoutAwareQualityAnalyzer()

for idx, image_path in enumerate(image_paths):
# for idx, page_no, image_path in selected_pages:

    page_no = idx + 1

    print("\n" + "=" * 70)
    print(f"PROCESSING PAGE {page_no}")
    print("=" * 70)

    try:

        # =============================================
        # STEP 2 → PREPROCESS
        # =============================================

        print("\nSTEP 2 → PREPROCESSING")

        enhanced_image = preprocess_image(
            image_path=image_path,
            output_folder=FOLDERS["enhanced"]
        )

        # # =============================================
        # # STEP 3 → LAYOUT DETECTION
        # # =============================================

        # region_outputs = []

        # if ENABLE_LAYOUT_DETECTION:

        #     print("\nSTEP 3 → LAYOUT DETECTION")

        #     layout_result = detect_layout(
        #         image_path=enhanced_image,
        #         layout_output_folder=FOLDERS["layout"],
        #         cropped_output_folder=FOLDERS["regions"]
        #     )

        #     cropped_regions = layout_result["cropped_regions"]

        # else:
        #     cropped_regions = []

        # # =============================================
        # # STEP 5 → FULL PAGE OCR
        # # =============================================

        # if ENABLE_FULL_PAGE_OCR:
        #     print("\nSTEP 5 → FULL PAGE OCR")
            
        #     full_page_ocr = multimodal_extract(
        #         image_path=enhanced_image,
        #         output_folder=FOLDERS["ocr"]
        #     )
            
        #     # Extract raw string text from the engine's output dictionary
        #     # Safely falls back to extracting via standard dictionary keys 
        #     raw_text = ""
        #     if isinstance(full_page_ocr, dict):
        #         raw_text = full_page_ocr.get("text", full_page_ocr.get("ocr_text", str(full_page_ocr)))
        #     else:
        #         raw_text = str(full_page_ocr)

        #     # Define the final txt destination path
        #     page_name = os.path.splitext(os.path.basename(image_path))[0]
        #     txt_output_path = os.path.join(FOLDERS["ocr"], f"{page_name}_raw.txt")
            
        #     # Save the clean raw text to file
        #     with open(txt_output_path, "w", encoding="utf-8") as f:
        #         f.write(raw_text)
                
        #     print(f"✅ Success! Raw OCR text saved directly to:\n   {txt_output_path}")







        # =============================================
        # STEP 3 → LAYOUT DETECTION
        # =============================================
        region_outputs = []
        layout_result = None

        if ENABLE_LAYOUT_DETECTION:
            print("\nSTEP 3 → LAYOUT DETECTION")
            layout_result = detect_layout(
                image_path=enhanced_image,
                layout_output_folder=FOLDERS["layout"],
                cropped_output_folder=FOLDERS["regions"]
            )
            cropped_regions = layout_result.get("cropped_regions", [])
        else:
            cropped_regions = []

        # =============================================
        # STEP 4 → IMAGE QUALITY ROUTING ENGINE (FIXED)
        # =============================================

        

        print("\nSTEP 4 → IMAGE QUALITY ASSESSMENT ENGINE")
        
        # 1. Run your mathematical evaluation package module
        quality_report = analyzer.analyze(
            image_path=enhanced_image,
            layout_result=layout_result
        )
        
        print(f"→ Overall Weighted Score: {quality_report.overall_score}/100")
        print(f"→ Module Internal Recommendation: {quality_report.recommendation.value}")

        # Reset all state control flags for this page loop iteration
        should_run_ocr = False
        should_run_text_llm = False
        should_run_vision_llm = False

        # --- THE PRODUCTION POINT OVERRIDE FILTER GATE ---
        # Isolate individual scores from the report object before checking the overall score
        is_too_noisy = quality_report.noise.normalized_score < 50.0
        is_blurry = quality_report.blur.normalized_score < 60.0
        is_soft_edges = quality_report.edge_sharpness.normalized_score < 60.0

        if quality_report.is_blank:
            print("→ [ROUTE: BLANK_PAGE] Empty page. Bypassing processing chains.")
            page_json_output = {"page_number": page_num, "document_type_classified": "blank_page", "extracted_data": {}}

        elif is_too_noisy or is_blurry or is_soft_edges:
            # CRITICAL FAILURE DETECTED: Force vision routing immediately and bypass PaddleOCR entirely!
            print("→ [ROUTE: VISION_LLM OVERRIDE] Specific metric point failure detected!")
            if is_too_noisy: print("  ⚠️ Point Failure: Image contains excessive background noise.")
            if is_blurry: print("  ⚠️ Point Failure: Image text is too blurry.")
            if is_soft_edges: print("  ⚠️ Point Failure: Text edge definition is too soft.")
            
            should_run_vision_llm = True

        else:
            # ALL CHECKS PASSED: Safe to follow standard high-speed PaddleOCR pathway
            print(f"→ [ROUTE: OCR STANDARD] Quality verified ({quality_report.overall_score}). Activating OCR pathway.")
            should_run_ocr = True

        # =============================================
        # STEP 5 → FULL PAGE OCR (ONLY RUNS IF ALL POINTS ARE VALID)
        # =============================================
        raw_text = ""
        
        if ENABLE_FULL_PAGE_OCR and should_run_ocr:
            print("\nSTEP 5 → FULL PAGE OCR")
            full_page_ocr = multimodal_extract(
                image_path=enhanced_image,
                output_folder=FOLDERS["ocr"]
            )
            
            if isinstance(full_page_ocr, dict):
                raw_text = full_page_ocr.get("text", full_page_ocr.get("ocr_text", str(full_page_ocr)))
            else:
                raw_text = str(full_page_ocr)

            page_name = os.path.splitext(os.path.basename(image_path))[0]
            txt_output_path = os.path.join(FOLDERS["ocr"], f"{page_name}_raw.txt")
            
            with open(txt_output_path, "w", encoding="utf-8") as f:
                f.write(raw_text)
                
            # --- SECONDARY POST-OCR BACKUP QUALITY GATES ---
            alphanumeric_chars = sum(1 for char in raw_text if char.isalnum())
            total_chars = max(1, len(raw_text.strip()))
            alphanumeric_ratio = alphanumeric_chars / total_chars

            if len(raw_text.strip()) < 45 or alphanumeric_ratio < 0.40:
                print(f"[OCR CHECK FAILURE] String has a poor alphanumeric ratio ({round(alphanumeric_ratio, 2)}). Text is corrupted noise.")
                print("→ Rerouting page execution flow directly to local Vision LLM fallback.")
                should_run_vision_llm = True
                should_run_text_llm = False
            else:
                print("[OCR QUALITY CHECK] Healthy alphanumeric text output validated.")
                should_run_text_llm = True



        # # =============================================
        # # STEP 5 → FULL PAGE OCR (ONLY RUNS IF ALL POINTS ARE VALID)
        # # =============================================
        # raw_text = ""
        
        # if ENABLE_FULL_PAGE_OCR and should_run_ocr:
        #     print("\nSTEP 5 → FULL PAGE OCR")
        #     full_page_ocr = multimodal_extract(
        #         image_path=enhanced_image,
        #         output_folder=FOLDERS["ocr"]
        #     )
            
        #     if isinstance(full_page_ocr, dict):
        #         raw_text = full_page_ocr.get("text", full_page_ocr.get("ocr_text", str(full_page_ocr)))
        #     else:
        #         raw_text = str(full_page_ocr)

        #     page_name = os.path.splitext(os.path.basename(image_path))[0]
        #     txt_output_path = os.path.join(FOLDERS["ocr"], f"{page_name}_raw.txt")
            
        #     # --- SECONDARY POST-OCR BACKUP QUALITY GATES (GENERIC METHOD) ---
        #     import re
            
        #     cleaned_text_strip = raw_text.strip()
        #     total_chars = max(1, len(cleaned_text_strip))
            
        #     # 1. Total character character density variance check
        #     alphanumeric_chars = sum(1 for char in cleaned_text_strip if char.isalnum())
        #     alphanumeric_ratio = alphanumeric_chars / total_chars

        #     # 2. Structural language text density verification (Letters ratio)
        #     alphabetic_chars = sum(1 for char in cleaned_text_strip if char.isalpha())
        #     alphabetic_ratio = alphabetic_chars / total_chars

        #     # 3. Dynamic regex artifact scanning layer
        #     has_heavy_junk_patterns = len(re.findall(r'[\+\-\.\:]{2,}', cleaned_text_strip)) > 1

        #     # HARDENED DATA INTEGRITY GATE RE-ROUTING RULE
        #     if len(cleaned_text_strip) < 65 or alphanumeric_ratio < 0.45 or alphabetic_ratio < 0.15 or has_heavy_junk_patterns:
        #         print(f"⚠️ [OCR CHECK FAILURE] Corrupted or fragmented data layer detected via linguistic metrics!")
        #         print(f"  → Telemetry: Length: {len(cleaned_text_strip)} | Alphanumeric Ratio: {round(alphanumeric_ratio, 2)} | Alphabetic Letters Ratio: {round(alphabetic_ratio, 2)}")
        #         print("→ Rerouting page execution flow directly to local Vision LLM fallback.")
                
        #         # Turn off text processing flags, elevate vision safety path routing tokens
        #         should_run_vision_llm = True
        #         should_run_text_llm = False
        #     else:
        #         print("✅ [OCR QUALITY CHECK] Healthy alphanumeric and alphabetic text structure validated.")
        #         should_run_text_llm = True
                
        #         with open(txt_output_path, "w", encoding="utf-8") as f:
        #             f.write(raw_text)



        # =============================================
        # STEP 6 → ENTITY PROCESSING ROUTER LAYERS
        # =============================================
        # if should_run_text_llm:
        #     print("\nSTEP 6 → RUNNING HIGH-SPEED TEXT LLM EXTRACTION")
        #     # page_json_output = await IDPOcrFallbackManager.extract_via_standard_text_llm(raw_text, TARGET_SCHEMA)
            
        # elif should_run_vision_llm:
        #     print("\nSTEP 6 → RUNNING PIXEL-BASED VISION LLM FALLBACK EXTRACTION")
        #     # page_json_output = await IDPOcrFallbackManager.extract_directly_from_image_pixels(enhanced_image, TARGET_SCHEMA)

        
        
        
        
        # =============================================
        # STEP 6 → ENTITY PROCESSING ROUTER LAYERS (TEXT OUTPUT)
        # =============================================
        import asyncio
        final_raw_text_output = ""

        if should_run_text_llm:
            print("\nSTEP 6 → PROCESSING STANDARD PATHWAY TEXT")
            # Standard Path: Directly use the healthy raw text string extracted by PaddleOCR
            final_raw_text_output = raw_text
            
        elif should_run_vision_llm:
            print("\nSTEP 6 → RUNNING PIXEL-BASED LOCAL VISION TEXT RECONSTRUCTION")
            
            # GENERIC SYSTEM PROMPT: Instructs QWEN to act as an advanced visual OCR engine.
            # It reads text straight through ink noise without needing to know the document type.
            GENERIC_VISION_OCR_PROMPT = """
            You are an advanced Intelligent Document Processing vision engine.
            Analyze the provided image document carefully. 
            Transcribe all visible text, numbers, headings, and tabular data exactly as they appear in the visual layout.
            
            Return ONLY the raw transcribed text. Do not wrap it in markdown code blocks, do not include conversational words, and do not explain your actions.
            """

            print()
 
            print("IMAGE =", image_path)

            img = cv2.imread(image_path)

            print(img.shape)
            
            # Execute Local Qwen Vision to extract raw text directly from the pixel layout
            vision_response = asyncio.run(
                analyzer.extract_via_vision_llm(
                    image_path=enhanced_image,
                    target_prompt=GENERIC_VISION_OCR_PROMPT
                )
            )
            
            # Unpack the response string cleanly (safeguards against model type variations)
            if isinstance(vision_response, dict):
                final_raw_text_output = vision_response.get("text", vision_response.get("raw_output", str(vision_response)))
            else:
                final_raw_text_output = str(vision_response)
                
            print("→ [SUCCESS] Local QWEN has reconstructed clean text directly from the image layout.")

            # --- THE HARDWARE MEMORY COOLING PAUSE ---
            # Gives your local GPU 2 seconds to flush pixel caches out of VRAM safely
            import time
            print("→ [SYSTEM LOG] Cooling GPU VRAM memory states for 2 seconds...")
            time.sleep(2.0)

        # =============================================
        # STEP 7 → SAVE THE FINAL RAW TXT FILE TO DISK
        # =============================================
        if final_raw_text_output.strip():
            page_name = os.path.splitext(os.path.basename(image_path))[0]
            txt_output_path = os.path.join(FOLDERS["ocr"], f"{page_name}_raw.txt")
            
            with open(txt_output_path, "w", encoding="utf-8") as f:
                f.write(final_raw_text_output.strip())
                
            print(f"→ [FILE WRITER] Clean raw text saved successfully to: {txt_output_path}")
            print("→ Ready for your downstream JSON processing function.")
            

        # from document_classifier.classifier import classify_document

        # doc_type = classify_document(page_no, raw_text, output_dir=FOLDERS["classification"])

        from document_classify_it import classify_document

        classification = classify_document( raw_text )

        document_type = classification[ "document_type" ]

        classification_file = os.path.join( FOLDERS["classification"], f"page_{page_no}.json" )

        with open( classification_file, "w", encoding="utf-8" ) as file:

            json.dump(classification, file, indent=4, ensure_ascii=False )


    except Exception as e:
        print(f"❌ Error processing Page {page_no}:")
        traceback.print_exc()

# ─────────────── THE FOR LOOP ENDS HERE ───────────────
print("\n🎉 Individual page extraction and classification loop completed successfully.")


# ==========================================================================
# STEP 9 → LOGICAL DOCUMENT MERGER ENGINE (OUTSIDE THE LOOP)
# ==========================================================================
print("\n" + "=" * 80)
print("STEP 9 → RUNNING PRODUCTION LOGICAL DOCUMENT MERGER")
print("=" * 80)

# Import the core grouping framework from your package
from document_grouper.merger import run_merger

# Run the merger tool. It scans FOLDERS["ocr"] and FOLDERS["classification"] to bundle files
merger_result = run_merger()

if merger_result:
    print(f"→ Successfully Grouped Document Types : {merger_result.get('document_types')}")
    print(f"→ Total Compiled Raw Text Pages       : {merger_result.get('pages')}")
    print(f"→ Output Target Storage Directory      : {merger_result.get('output_directory')}")
else:
    print("⚠️ Warning: Merger completed execution loop but returned empty output matrices.")

print("=" * 80 + "\n")



# ==========================================================================
# STEP 10 → ENTERPRISE COGNITIVE EXTRACTOR PIPELINE (OUTSIDE THE LOOP)
# ==========================================================================
print("\n" + "=" * 80)
print("STEP 10 → RUNNING HIGH-DENSITY COGNITIVE LLM PASS")
print("=" * 80)

# Ingest your newly optimized, rate-safe, and token-budgeted parser engine
from project import parser  

try:
    # Trigger the line-by-line high recall structural parser.
    # Passes 'force_reprocess_active' to respect skip choices made at boot.
    parser.run_extraction_pipeline(force_reprocess_active=True)
    print("\n✅ Success: Enterprise Universal Healthcare IDP Platform execution finalized completely.")
except Exception as pipeline_error:
    print(f"\n❌ Error encountered during text restructuring stage: {pipeline_error}")

print("=" * 80)

print("\nPipeline stopped successfully after Full Page OCR.")
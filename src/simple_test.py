logger.info("Starting simple test...")

try:
    logger.info("Testing import...")
    from case_name_extraction_core import extract_case_name_and_date
    logger.info("Import successful!")
    
    logger.info("Testing extraction...")
    result = extract_case_name_and_date("Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).", "200 Wn.2d 72")
    logger.info(f"Result: {result}")
    
except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()

logger.info("Test complete!") 
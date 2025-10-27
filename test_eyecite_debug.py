import sys
import os
import logging

# Add the parent directory to sys.path to allow importing src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from eyecite import get_citations

# Configure logging for visibility
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_eyecite_extraction():
    logger.info("🔍 Testing eyecite extraction...")

    test_text = (
        "A & G Constr. Co. v. Reid Bros. Logging Co., 547 P.2d 1207 (1976). \n"
        "    State v. Bayer Corp., 32 So. 3d 496 (2010).\n"
    )
    logger.info(f"Test text: {test_text}")

    # Extract citations using eyecite
    citations = get_citations(test_text)
    
    logger.info(f"\n📊 Eyecite found {len(citations)} citations:")

    for i, cit in enumerate(citations):
        logger.info(f"\nEyecite Citation {i+1}:")
        logger.info(f"  Citation: {cit.matched_text()}")
        logger.info(f"  Case Name: {cit.metadata.plaintiff} v. {cit.metadata.defendant}")
        logger.info(f"  Date: {cit.metadata.year}")
        logger.info(f"  Span: {cit.span}")
        logger.info(f"  Type: {type(cit)}")
        
        # Show the actual text that eyecite matched
        start, end = cit.span()
        matched_text = test_text[start:end]
        logger.info(f"  Matched Text: '{matched_text}'")
        
        # Show context around the match
        context_start = max(0, start - 20)
        context_end = min(len(test_text), end + 20)
        context = test_text[context_start:context_end]
        logger.info(f"  Context: '{context}'")

if __name__ == "__main__":
    test_eyecite_extraction()

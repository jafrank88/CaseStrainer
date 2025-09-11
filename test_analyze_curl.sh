#!/bin/bash

# Test the /api/analyze endpoint with curl
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). The goal of statutory interpretation is to give effect to the legislature\'s intentions. DeSean, 2 Wn.3d at 335. In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820.",
    "options": {
      "extract_case_names": true,
      "extract_dates": true
    }
  }' \
  | python -m json.tool

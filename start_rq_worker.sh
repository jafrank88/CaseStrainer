#!/bin/bash

# Add src to Python path
export PYTHONPATH="/app/src:$PYTHONPATH"

# Start the RQ worker
python -m src.rq_worker

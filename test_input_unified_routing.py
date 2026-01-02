#!/usr/bin/env python3
"""
Integration-style test to confirm UnifiedInputProcessor routes immediate/sync
processing through the unified pipeline.

This test monkeypatches:
- CitationService.should_process_immediately -> True
- unified_processing_pipeline.process_citations_unified -> canned async result

It then calls UnifiedInputProcessor.process_any_input and asserts the response
structure and that the unified pipeline's output flows through.
"""

import sys
import os
import types

# Ensure src is on path
ROOT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.unified_input_processor import UnifiedInputProcessor  # noqa: E402


def main() -> None:
    # Monkeypatch CitationService.should_process_immediately to force sync path
    from src.api.services.citation_service import CitationService

    original_should_process = CitationService.should_process_immediately
    CitationService.should_process_immediately = lambda self, *_args, **_kwargs: True

    # Monkeypatch unified processing function to return canned data
    import src.unified_processing_pipeline as upp

    async def fake_process_citations_unified(text: str, processing_mode: str = "enhanced_sync", **_kwargs):
        return {
            'citations': [
                {
                    'citation': '543 P.3d 1059',
                    'verified': True,
                    'true_by_parallel': True,
                    'start_index': 10,
                    'end_index': 22
                }
            ],
            'clusters': [],
            'metadata': {
                'processing_mode': processing_mode,
                'stages_completed': ['extraction', 'verification', 'parallel_verification', 'formatting', 'completed']
            }
        }

    original_pipeline_fn = upp.process_citations_unified
    upp.process_citations_unified = fake_process_citations_unified

    try:
        processor = UnifiedInputProcessor()
        req_id = 'TEST-UNIFIED-ROUTING'
        text = 'Gresser v. Banner Health, 2023 COA 108, 543 P.3d 1059.'

        result = processor.process_any_input(text, 'text', req_id, source_name='text_input', force_mode='sync')

        assert isinstance(result, dict), 'Result should be a dict'
        assert result.get('success') is True, 'Success should be True'
        assert isinstance(result.get('citations'), list) and len(result['citations']) == 1, 'Should carry citations from pipeline'
        assert result['citations'][0].get('true_by_parallel') is True, 'Parallel flag should pass through'
        assert result.get('metadata', {}).get('processing_strategy') == 'unified_processing_pipeline', 'Should reflect unified pipeline strategy'
        print('✅ UnifiedInputProcessor routes immediate path through unified pipeline')
    finally:
        # Restore monkeypatches
        CitationService.should_process_immediately = original_should_process
        upp.process_citations_unified = original_pipeline_fn


if __name__ == '__main__':
    main()




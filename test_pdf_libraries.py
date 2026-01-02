#!/usr/bin/env python3
"""
Test and compare different PDF libraries for URL and file handling
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test URLs - various PDF sources that might cause issues
TEST_URLS = [
    "https://www.courts.wa.gov/opinions/pdf/1031351.pdf",  # Washington Court
    "https://www.courts.wa.gov/opinions/pdf/1033940.pdf",  # Larger PDF
    "https://www.supremecourt.gov/opinions/22pdf/21-1473_k6f8.pdf",  # Supreme Court
    "https://www.ca2.uscourts.gov/decisions/isysquery/13f8c5a8-2a1b-4e2b-9b6d-7e8f9a0b1c2d/summary.pdf",  # Federal Appeals
]

class PDFLibraryTester:
    """Test different PDF libraries for performance and reliability"""
    
    def __init__(self):
        self.results = []
        
    async def test_all_libraries(self):
        """Test all available PDF libraries on test URLs"""
        print("=" * 80)
        print("PDF LIBRARY COMPARISON TEST")
        print("=" * 80)
        
        for url in TEST_URLS:
            print(f"\n[PDF] Testing URL: {url}")
            print("-" * 60)
            
            # Download PDF to temp file
            temp_file = await self.download_pdf(url)
            if not temp_file:
                print(f"❌ Failed to download PDF")
                continue
                
            # Test each library
            await self.test_pdf_with_all_libraries(temp_file, url)
            
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass
    
    async def download_pdf(self, url: str) -> Optional[str]:
        """Download PDF to temporary file"""
        try:
            print(f"  [DOWNLOAD] Downloading PDF...")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                return f.name
        except Exception as e:
            print(f"  [ERROR] Download failed: {e}")
            return None
    
    async def test_pdf_with_all_libraries(self, pdf_path: str, url: str):
        """Test PDF with all available libraries"""
        
        # Test libraries in order
        libraries = [
            ("PyMuPDF (fitz)", self.test_fitz),
            ("pdfplumber", self.test_pdfplumber),
            ("PyPDF", self.test_pypdf),
            ("PDFMiner", self.test_pdfminer),
        ]
        
        results = {}
        
        for lib_name, test_func in libraries:
            print(f"\n  📚 Testing {lib_name}:")
            try:
                start_time = time.time()
                text, success, error = await test_func(pdf_path)
                elapsed = time.time() - start_time
                
                if success:
                    quality = self.assess_quality(text)
                    print(f"    ✅ Success in {elapsed:.2f}s")
                    print(f"    📊 Text: {len(text):,} chars")
                    print(f"    📈 Quality: {quality:.2f}")
                    results[lib_name] = {
                        'success': True,
                        'time': elapsed,
                        'chars': len(text),
                        'quality': quality,
                        'text_sample': text[:200] + "..." if len(text) > 200 else text
                    }
                else:
                    print(f"    ❌ Failed: {error}")
                    results[lib_name] = {
                        'success': False,
                        'error': error
                    }
            except Exception as e:
                print(f"    ❌ Exception: {e}")
                results[lib_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Store results
        self.results.append({
            'url': url,
            'results': results
        })
        
        # Summary for this PDF
        print(f"\n  📋 Summary for {Path(url).name}:")
        successful = [(k, v) for k, v in results.items() if v.get('success')]
        if successful:
            print(f"    ✅ Successful libraries: {len(successful)}")
            # Sort by quality then time
            successful.sort(key=lambda x: (-x[1]['quality'], x[1]['time']))
            for i, (lib, data) in enumerate(successful[:3], 1):
                print(f"      {i}. {lib}: quality={data['quality']:.2f}, time={data['time']:.2f}s")
        else:
            print(f"    ❌ No libraries succeeded")
    
    async def test_fitz(self, pdf_path: str) -> Tuple[str, bool, str]:
        """Test PyMuPDF (fitz)"""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            text = ""
            
            # Test with different extraction methods
            for page_num in range(min(5, len(doc))):  # Test first 5 pages
                page = doc.load_page(page_num)
                # Method 1: Simple text extraction
                page_text = page.get_text()
                text += page_text + "\n"
            
            doc.close()
            return text, len(text.strip()) > 100, ""
        except ImportError:
            return "", False, "PyMuPDF not installed"
        except Exception as e:
            return "", False, str(e)
    
    async def test_pdfplumber(self, pdf_path: str) -> Tuple[str, bool, str]:
        """Test pdfplumber"""
        try:
            import pdfplumber
            text = ""
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages[:5]):  # Test first 5 pages
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text, len(text.strip()) > 100, ""
        except ImportError:
            return "", False, "pdfplumber not installed"
        except Exception as e:
            return "", False, str(e)
    
    async def test_pypdf(self, pdf_path: str) -> Tuple[str, bool, str]:
        """Test PyPDF"""
        try:
            import pypdf
            text = ""
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page_num in range(min(5, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text + "\n"
            
            return text, len(text.strip()) > 100, ""
        except ImportError:
            return "", False, "PyPDF not installed"
        except Exception as e:
            return "", False, str(e)
    
    async def test_pdfminer(self, pdf_path: str) -> Tuple[str, bool, str]:
        """Test PDFMiner"""
        try:
            from pdfminer.high_level import extract_text
            from pdfminer.layout import LAParams
            
            # Configure for better extraction
            laparams = LAParams(
                line_margin=0.5,
                word_margin=0.1,
                char_margin=2.0,
                detect_vertical=True,
                all_texts=True
            )
            
            text = extract_text(pdf_path, laparams=laparams)
            
            # Limit to first few pages for comparison
            lines = text.split('\n')
            # Rough estimation of first 5 pages
            text = '\n'.join(lines[:1000])  # Approximate first 5 pages
            
            return text, len(text.strip()) > 100, ""
        except ImportError:
            return "", False, "PDFMiner not installed"
        except Exception as e:
            return "", False, str(e)
    
    def assess_quality(self, text: str) -> float:
        """Assess quality of extracted text"""
        if not text or len(text.strip()) < 50:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # Legal indicators (most important)
        legal_indicators = ['court', 'v.', 'f.', 'u.s.', 'p.', 'supp', 'plaintiff', 'defendant', 'citation']
        legal_matches = sum(1 for ind in legal_indicators if ind in text_lower)
        score += min(legal_matches / len(legal_indicators), 1.0) * 0.5
        
        # Text structure
        period_ratio = text.count('.') / len(text) if text else 0
        if 0.01 < period_ratio < 0.15:
            score += 0.2
        
        # Word variety
        unique_words = len(set(text.split()))
        total_words = len(text.split())
        if total_words > 0:
            word_variety = unique_words / total_words
            score += word_variety * 0.2
        
        # Length penalty for very short text
        if len(text) < 500:
            score *= 0.5
        
        # Bonus for case citations
        import re
        citation_patterns = [
            r'\d+\s+F\.\d+',
            r'\d+\s+U\.\S\.',
            r'\d+\s+Wn\.\d+',
            r'\d+\s+S\.\Ct\.'
        ]
        citation_matches = sum(1 for pattern in citation_patterns if re.search(pattern, text))
        if citation_matches > 0:
            score += min(citation_matches * 0.1, 0.1)
        
        return min(score, 1.0)
    
    def print_summary(self):
        """Print overall summary"""
        print("\n" + "=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)
        
        library_scores = {}
        
        for result in self.results:
            url = result['url']
            print(f"\n📄 {Path(url).name}:")
            
            for lib_name, data in result['results'].items():
                if data.get('success'):
                    if lib_name not in library_scores:
                        library_scores[lib_name] = []
                    library_scores[lib_name].append(data['quality'])
                    print(f"  ✅ {lib_name}: quality={data['quality']:.2f}, time={data['time']:.2f}s")
                else:
                    print(f"  ❌ {lib_name}: {data.get('error', 'Failed')}")
        
        print("\n🏆 LIBRARY RANKINGS:")
        if library_scores:
            # Calculate average quality for each library
            avg_scores = [(lib, sum(scores)/len(scores)) for lib, scores in library_scores.items()]
            avg_scores.sort(key=lambda x: x[1], reverse=True)
            
            for i, (lib, avg_quality) in enumerate(avg_scores, 1):
                success_rate = len(library_scores[lib]) / len(self.results) * 100
                print(f"  {i}. {lib}: avg_quality={avg_quality:.2f}, success_rate={success_rate:.0f}%")
        else:
            print("  ❌ No libraries succeeded on any PDFs")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if library_scores:
            best_lib = max(library_scores.items(), key=lambda x: sum(x[1])/len(x[1]))
            print(f"  🥇 Best overall: {best_lib[0]}")
            print(f"  📊 Success rate: {len(best_lib[1])}/{len(self.results)} PDFs")
            print(f"  📈 Average quality: {sum(best_lib[1])/len(best_lib[1]):.2f}")
            
            # Check for URL-specific issues
            url_failures = []
            for result in self.results:
                if not any(data.get('success') for data in result['results'].values()):
                    url_failures.append(result['url'])
            
            if url_failures:
                print(f"  ⚠️  URLs that failed with all libraries:")
                for url in url_failures:
                    print(f"    - {url}")

async def main():
    """Run the PDF library comparison test"""
    tester = PDFLibraryTester()
    await tester.test_all_libraries()
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())

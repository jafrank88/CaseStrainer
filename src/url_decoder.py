import re
import urllib.parse
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class URLDecoder:
    """Handles various URL encoding formats including Microsoft Defender URLs."""
    
    @staticmethod
    def decode_microsoft_defender_url(url: str) -> Optional[str]:
        """
        Decode Microsoft Defender encoded URLs.
        
        Microsoft Defender URLs have the format:
        https://urldefense.com/v3/__{original_url}__;{hash}${hash}
        
        Args:
            url: The encoded URL string
            
        Returns:
            The decoded URL if successful, None otherwise
        """
        try:
            # Pattern for Microsoft Defender URLs
            pattern = r'https://urldefense\.com/v3/__([^_]+)__;([^$]+)\$'
            match = re.search(pattern, url)
            
            if match:
                encoded_url = match.group(1)
                # The URL might be base64 encoded or have additional encoding
                # Try to decode it
                try:
                    # First, try URL decoding
                    decoded_url = urllib.parse.unquote(encoded_url)
                    logger.info(f"Successfully decoded Microsoft Defender URL: {url[:100]}... -> {decoded_url[:100]}...")
                    return decoded_url
                except Exception as e:
                    logger.warning(f"Failed to decode Microsoft Defender URL: {e}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error processing Microsoft Defender URL: {e}")
            return None
    
    @staticmethod
    def decode_google_safe_browsing_url(url: str) -> Optional[str]:
        """
        Decode Google Safe Browsing URLs.
        
        Google Safe Browsing URLs have the format:
        https://safebrowsing.google.com/safebrowsing/diagnostic?site={original_url}
        
        Args:
            url: The encoded URL string
            
        Returns:
            The decoded URL if successful, None otherwise
        """
        try:
            # Pattern for Google Safe Browsing URLs
            pattern = r'https://safebrowsing\.google\.com/safebrowsing/diagnostic\?site=([^&]+)'
            match = re.search(pattern, url)
            
            if match:
                encoded_url = match.group(1)
                decoded_url = urllib.parse.unquote(encoded_url)
                logger.info(f"Successfully decoded Google Safe Browsing URL: {url[:100]}... -> {decoded_url[:100]}...")
                return decoded_url
            return None
        except Exception as e:
            logger.error(f"Error processing Google Safe Browsing URL: {e}")
            return None
    
    @staticmethod
    def decode_office365_url(url: str) -> Optional[str]:
        """
        Decode Office 365/Outlook encoded URLs.
        
        Office 365 URLs often have additional encoding for security.
        
        Args:
            url: The encoded URL string
            
        Returns:
            The decoded URL if successful, None otherwise
        """
        try:
            # Pattern for Office 365 URLs with encoding
            patterns = [
                r'https://[^/]+\.safelinks\.protection\.outlook\.com/\?url=([^&]+)',
                r'https://[^/]+\.safelinks\.protection\.outlook\.com/\?data=([^&]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    encoded_url = match.group(1)
                    decoded_url = urllib.parse.unquote(encoded_url)
                    logger.info(f"Successfully decoded Office 365 URL: {url[:100]}... -> {decoded_url[:100]}...")
                    return decoded_url
            return None
        except Exception as e:
            logger.error(f"Error processing Office 365 URL: {e}")
            return None
    
    @staticmethod
    def decode_duckduckgo_url(url: str) -> Optional[str]:
        """
        Decode DuckDuckGo redirect URLs to extract the underlying website URL.
        
        DuckDuckGo URLs have formats like:
        https://duckduckgo.com/l/?uddg=https%3A%2F%2Fcase-law.vlex.com%2F...&rut=...
        
        Args:
            url: The DuckDuckGo redirect URL
            
        Returns:
            The decoded underlying URL if successful, None otherwise
        """
        try:
            # Pattern for DuckDuckGo redirect URLs
            patterns = [
                r'https://duckduckgo\.com/l/\?uddg=([^&]+)',
                r'https://duckduckgo\.com//duckduckgo\.com/l/\?uddg=([^&]+)',  # Double slash format
                r'https://[^/]*duckduckgo[^/]*/l/\?uddg=([^&]+)',  # Generic DuckDuckGo format
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    encoded_url = match.group(1)
                    decoded_url = urllib.parse.unquote(encoded_url)
                    logger.info(f"Successfully decoded DuckDuckGo URL: {url[:100]}... -> {decoded_url[:100]}...")
                    return decoded_url
            return None
        except Exception as e:
            logger.error(f"Error processing DuckDuckGo URL: {e}")
            return None
    
    @staticmethod
    def decode_bing_url(url: str) -> Optional[str]:
        """
        Decode Bing redirect URLs to extract the underlying website URL.
        
        Bing URLs often have formats like:
        https://www.bing.com/ck/a?!&&p=...&u=a1aHR0cHM6Ly93d3cuZXhhbXBsZS5jb20%3d
        
        Args:
            url: The Bing redirect URL
            
        Returns:
            The decoded underlying URL if successful, None otherwise
        """
        try:
            # Pattern for Bing redirect URLs
            patterns = [
                r'https://[^/]*bing[^/]*/ck/a\?[^&]*&u=([^&]+)',
                r'https://[^/]*bing[^/]*/[^?]*\?[^&]*&u=([^&]+)',
                r'https://[^/]*bing[^/]*/[^?]*\?[^&]*url=([^&]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    encoded_url = match.group(1)
                    # Bing often uses base64 encoding
                    try:
                        import base64
                        decoded_bytes = base64.b64decode(encoded_url + '==')  # Add padding if needed
                        decoded_url = decoded_bytes.decode('utf-8')
                        logger.info(f"Successfully decoded Bing URL: {url[:100]}... -> {decoded_url[:100]}...")
                        return decoded_url
                    except:
                        # Fall back to URL decoding
                        decoded_url = urllib.parse.unquote(encoded_url)
                        logger.info(f"Successfully decoded Bing URL (fallback): {url[:100]}... -> {decoded_url[:100]}...")
                        return decoded_url
            return None
        except Exception as e:
            logger.error(f"Error processing Bing URL: {e}")
            return None
    
    @staticmethod
    def decode_google_redirect_url(url: str) -> Optional[str]:
        """
        Decode Google redirect URLs to extract the underlying website URL.
        
        Google URLs often have formats like:
        https://www.google.com/url?q=https://example.com&sa=U&ved=...
        
        Args:
            url: The Google redirect URL
            
        Returns:
            The decoded underlying URL if successful, None otherwise
        """
        try:
            # Pattern for Google redirect URLs
            patterns = [
                r'https://[^/]*google[^/]*/url\?[^&]*q=([^&]+)',
                r'https://[^/]*google[^/]*/[^?]*\?[^&]*url=([^&]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    encoded_url = match.group(1)
                    decoded_url = urllib.parse.unquote(encoded_url)
                    logger.info(f"Successfully decoded Google redirect URL: {url[:100]}... -> {decoded_url[:100]}...")
                    return decoded_url
            return None
        except Exception as e:
            logger.error(f"Error processing Google redirect URL: {e}")
            return None
    
    @staticmethod
    def decode_url(url: str) -> Tuple[str, bool]:
        """
        Attempt to decode various types of encoded URLs.
        
        Args:
            url: The URL string to decode
            
        Returns:
            Tuple of (decoded_url, was_decoded)
        """
        original_url = url.strip()
        
        # Try DuckDuckGo redirect decoding first (most common in search results)
        decoded = URLDecoder.decode_duckduckgo_url(original_url)
        if decoded:
            return decoded, True
        
        # Try Google redirect decoding
        decoded = URLDecoder.decode_google_redirect_url(original_url)
        if decoded:
            return decoded, True
        
        # Try Bing redirect decoding
        decoded = URLDecoder.decode_bing_url(original_url)
        if decoded:
            return decoded, True
        
        # Try Microsoft Defender decoding
        decoded = URLDecoder.decode_microsoft_defender_url(original_url)
        if decoded:
            return decoded, True
        
        # Try Google Safe Browsing decoding
        decoded = URLDecoder.decode_google_safe_browsing_url(original_url)
        if decoded:
            return decoded, True
        
        # Try Office 365 decoding
        decoded = URLDecoder.decode_office365_url(original_url)
        if decoded:
            return decoded, True
        
        # If no special decoding needed, return original URL
        return original_url, False
    
    @staticmethod
    def is_encoded_url(url: str) -> bool:
        """
        Check if a URL appears to be encoded by security services or search engine redirects.
        
        Args:
            url: The URL string to check
            
        Returns:
            True if the URL appears to be encoded, False otherwise
        """
        url_lower = url.lower()
        
        # Check for common security service domains and search engine redirects
        redirect_patterns = [
            'urldefense.com',
            'safebrowsing.google.com',
            'safelinks.protection.outlook.com',
            'protection.outlook.com',
            'safelinks.protection.office.com',
            'duckduckgo.com/l/',
            'duckduckgo.com//duckduckgo.com/l/',
            'google.com/url?',
            'bing.com/ck/a?'
        ]
        
        return any(pattern in url_lower for pattern in redirect_patterns)
    
    @staticmethod
    def clean_url(url: str) -> str:
        """
        Clean and normalize a URL for processing.
        
        Args:
            url: The URL string to clean
            
        Returns:
            The cleaned URL
        """
        # Remove leading/trailing whitespace
        url = url.strip()
        
        # Remove common prefixes that might be added by email clients
        prefixes_to_remove = [
            'http://',
            'https://',
            'www.',
            'mailto:'
        ]
        
        # Only remove if they're at the very beginning
        for prefix in prefixes_to_remove:
            if url.lower().startswith(prefix):
                url = url[len(prefix):]
                break
        
        # Ensure it has a protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url

def decode_and_clean_url(url: str) -> Tuple[str, bool, str]:
    """
    Convenience function to decode and clean a URL.
    
    Args:
        url: The URL string to process
        
    Returns:
        Tuple of (cleaned_url, was_decoded, original_url)
    """
    original_url = url
    decoded_url, was_decoded = URLDecoder.decode_url(url)
    cleaned_url = URLDecoder.clean_url(decoded_url)
    
    return cleaned_url, was_decoded, original_url 
"""
Type annotations and static type checking improvements for citation processing.

This module provides enhanced type annotations and type checking utilities.
"""

from typing import (
    List, Dict, Any, Optional, Union, Tuple, Set, 
    Callable, Awaitable, TypeVar, Generic, Protocol,
    runtime_checkable, get_type_hints
)
from typing_extensions import TypedDict, Literal
from dataclasses import dataclass
from abc import ABC, abstractmethod
import inspect
import logging

logger = logging.getLogger(__name__)

# Type aliases for better readability
CitationText = str
CaseNameText = str
DateText = str
UrlText = str
ConfidenceScore = float  # 0.0 to 1.0
ProcessingMethod = Literal["regex", "eyecite", "api", "landmark", "cache"]
VerificationStatus = Literal["verified", "unverified", "pending", "error"]

# Generic type variables
T = TypeVar('T')
ResultType = TypeVar('ResultType')


class CitationDict(TypedDict, total=False):
    """Typed dictionary for citation data."""
    citation: CitationText
    extracted_case_name: Optional[CaseNameText]
    extracted_date: Optional[DateText]
    canonical_name: Optional[CaseNameText]
    canonical_date: Optional[DateText]
    verified: bool
    confidence: ConfidenceScore
    method: ProcessingMethod
    pattern: Optional[str]
    context: Optional[str]
    start_index: int
    end_index: int
    parallel_citations: List[CitationText]
    court: Optional[str]
    docket_number: Optional[str]
    url: Optional[UrlText]
    source: Optional[str]
    metadata: Dict[str, Any]


class ClusterDict(TypedDict, total=False):
    """Typed dictionary for citation cluster data."""
    cluster_id: str
    canonical_name: Optional[CaseNameText]
    canonical_date: Optional[DateText]
    extracted_case_name: Optional[CaseNameText]
    extracted_date: Optional[DateText]
    size: int
    citations: List[CitationDict]
    confidence: ConfidenceScore
    verification_status: VerificationStatus


class ProcessingResultDict(TypedDict):
    """Typed dictionary for processing results."""
    success: bool
    citations: List[CitationDict]
    clusters: List[ClusterDict]
    summary: Dict[str, Union[int, float]]
    processing_info: Dict[str, Any]
    error: Optional[str]
    message: Optional[str]


class ConfigDict(TypedDict, total=False):
    """Typed dictionary for configuration."""
    debug_mode: bool
    use_eyecite: bool
    api_timeout: float
    max_retries: int
    cache_ttl: int
    rate_limit_delay: float
    courtlistener_api_key: Optional[str]


@runtime_checkable
class Extractable(Protocol):
    """Protocol for objects that can extract citations."""
    
    def extract_citations(self, text: str) -> List['CitationResult']:
        """Extract citations from text."""
        ...


@runtime_checkable
class Verifiable(Protocol):
    """Protocol for objects that can verify citations."""
    
    async def verify_citations(self, citations: List['CitationResult']) -> List['CitationResult']:
        """Verify citations."""
        ...


@runtime_checkable
class Clusterable(Protocol):
    """Protocol for objects that can cluster citations."""
    
    def cluster_citations(self, citations: List['CitationResult']) -> List[ClusterDict]:
        """Cluster citations."""
        ...


@dataclass
class TypedCitationResult:
    """Strongly typed citation result with validation."""
    citation: CitationText
    start_index: int
    end_index: int
    method: ProcessingMethod
    confidence: ConfidenceScore
    verified: bool = False
    extracted_case_name: Optional[CaseNameText] = None
    extracted_date: Optional[DateText] = None
    canonical_name: Optional[CaseNameText] = None
    canonical_date: Optional[DateText] = None
    pattern: Optional[str] = None
    context: Optional[str] = None
    parallel_citations: Optional[List[CitationText]] = None
    court: Optional[str] = None
    docket_number: Optional[str] = None
    url: Optional[UrlText] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate fields after initialization."""
        self._validate_confidence()
        self._validate_indices()
        self._validate_method()
    
    def _validate_confidence(self) -> None:
        """Validate confidence score is between 0 and 1."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
    
    def _validate_indices(self) -> None:
        """Validate start and end indices."""
        if self.start_index < 0:
            raise ValueError(f"Start index must be non-negative, got {self.start_index}")
        if self.end_index < self.start_index:
            raise ValueError(f"End index ({self.end_index}) must be >= start index ({self.start_index})")
    
    def _validate_method(self) -> None:
        """Validate processing method."""
        valid_methods = {"regex", "eyecite", "api", "landmark", "cache"}
        if self.method not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}, got {self.method}")
    
    def to_dict(self) -> CitationDict:
        """Convert to dictionary format."""
        return CitationDict(
            citation=self.citation,
            extracted_case_name=self.extracted_case_name,
            extracted_date=self.extracted_date,
            canonical_name=self.canonical_name,
            canonical_date=self.canonical_date,
            verified=self.verified,
            confidence=self.confidence,
            method=self.method,
            pattern=self.pattern,
            context=self.context,
            start_index=self.start_index,
            end_index=self.end_index,
            parallel_citations=self.parallel_citations or [],
            court=self.court,
            docket_number=self.docket_number,
            url=self.url,
            source=self.source,
            metadata=self.metadata or {}
        )


class TypeValidator:
    """Utility class for runtime type validation."""
    
    @staticmethod
    def validate_citation_list(citations: Any) -> List['CitationResult']:
        """Validate and convert citation list."""
        if not isinstance(citations, list):
            raise TypeError(f"Expected list, got {type(citations)}")
        
        # Import here to avoid circular imports
        from ..models import CitationResult
        
        validated = []
        for i, citation in enumerate(citations):
            if not isinstance(citation, CitationResult):
                raise TypeError(f"Citation {i} is not a CitationResult, got {type(citation)}")
            validated.append(citation)
        
        return validated
    
    @staticmethod
    def validate_text_input(text: Any) -> str:
        """Validate text input."""
        if not isinstance(text, str):
            raise TypeError(f"Expected string, got {type(text)}")
        
        if not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        
        return text
    
    @staticmethod
    def validate_config(config: Any) -> Dict[str, Any]:
        """Validate configuration dictionary."""
        if not isinstance(config, dict):
            raise TypeError(f"Expected dict, got {type(config)}")
        
        # Validate known config keys
        valid_keys = {
            'debug_mode', 'use_eyecite', 'api_timeout', 'max_retries',
            'cache_ttl', 'rate_limit_delay', 'courtlistener_api_key'
        }
        
        for key in config:
            if key not in valid_keys:
                logger.warning(f"Unknown config key: {key}")
        
        return config


def type_checked(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for runtime type checking based on type annotations.
    """
    def wrapper(*args, **kwargs) -> T:
        # Get function signature and type hints
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Validate arguments
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        for param_name, value in bound_args.arguments.items():
            if param_name in type_hints:
                expected_type = type_hints[param_name]
                if not _is_instance_of_type(value, expected_type):
                    raise TypeError(
                        f"Parameter '{param_name}' expected {expected_type}, "
                        f"got {type(value)} with value {value}"
                    )
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Validate return type
        if 'return' in type_hints:
            return_type = type_hints['return']
            if not _is_instance_of_type(result, return_type):
                raise TypeError(
                    f"Return value expected {return_type}, "
                    f"got {type(result)} with value {result}"
                )
        
        return result
    
    return wrapper


def _is_instance_of_type(value: Any, expected_type: type) -> bool:
    """Check if value is instance of expected type, handling generics."""
    try:
        # Handle basic types
        if hasattr(expected_type, '__origin__'):
            origin = expected_type.__origin__
            
            # Handle Optional (Union[T, None])
            if origin is Union:
                args = expected_type.__args__
                if len(args) == 2 and type(None) in args:
                    # This is Optional[T]
                    if value is None:
                        return True
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    return isinstance(value, non_none_type)
                else:
                    # Regular Union
                    return any(isinstance(value, arg) for arg in args)
            
            # Handle List, Dict, etc.
            elif origin in (list, List):
                return isinstance(value, list)
            elif origin in (dict, Dict):
                return isinstance(value, dict)
            elif origin in (tuple, Tuple):
                return isinstance(value, tuple)
            elif origin in (set, Set):
                return isinstance(value, set)
        
        # Handle regular types
        return isinstance(value, expected_type)
        
    except Exception:
        # If type checking fails, assume it's valid
        return True


class TypedServiceMixin:
    """Mixin class providing type checking capabilities to services."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enable_type_checking = True
    
    def _validate_input(self, value: Any, expected_type: type, param_name: str) -> Any:
        """Validate input parameter type."""
        if not self._enable_type_checking:
            return value
        
        if not _is_instance_of_type(value, expected_type):
            raise TypeError(
                f"Parameter '{param_name}' expected {expected_type}, "
                f"got {type(value)}"
            )
        
        return value
    
    def _validate_output(self, value: Any, expected_type: type, operation: str) -> Any:
        """Validate output type."""
        if not self._enable_type_checking:
            return value
        
        if not _is_instance_of_type(value, expected_type):
            raise TypeError(
                f"Operation '{operation}' expected to return {expected_type}, "
                f"got {type(value)}"
            )
        
        return value


# Export commonly used types for convenience
__all__ = [
    'CitationText', 'CaseNameText', 'DateText', 'UrlText', 
    'ConfidenceScore', 'ProcessingMethod', 'VerificationStatus',
    'CitationDict', 'ClusterDict', 'ProcessingResultDict', 'ConfigDict',
    'Extractable', 'Verifiable', 'Clusterable',
    'TypedCitationResult', 'TypeValidator', 'TypedServiceMixin',
    'type_checked'
]

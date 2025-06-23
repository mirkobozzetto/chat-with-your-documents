# src/security/input_sanitizer.py
import re
import html
from typing import Any, Dict, List, Optional, Union


class InputSanitizer:
    """Comprehensive input sanitization for security and data validation"""

    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'data:text/html',
        r'eval\s*\(',
        r'expression\s*\(',
    ]

    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b|\bSELECT\b|\bFROM\b|\bWHERE\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bDROP\b)',
        r'(--|#|/\*|\*/)',
        r'(\bOR\b|\bAND\b)\s+[\d\w\'\"]+\s*=\s*[\d\w\'\"]+',
        r'[\'\";]\s*(\bOR\b|\bAND\b)',
        r'(\bEXEC\b|\bEXECUTE\b)\s*\(',
        r'\bxp_\w+',
        r'\bsp_\w+',
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.',
        r'\/\.\.',
        r'\.\.\/',
        r'%2e%2e',
        r'%252e',
        r'%c0%ae',
        r'%c1%9c',
    ]

    COMMAND_INJECTION_PATTERNS = [
        r'[\|&;`\$\(\)\{\}\[\]<>]',
        r'(^|[^\\])(\$\{|\$\()',
        r'(rm|cat|ls|ps|kill|chmod|sudo|su)\s',
        r'(nc|netcat|wget|curl|ping)\s',
        r'(python|perl|ruby|php|node|bash|sh)\s',
    ]

    def __init__(self):
        self.xss_regex = re.compile('|'.join(self.XSS_PATTERNS), re.IGNORECASE | re.DOTALL)
        self.sql_regex = re.compile('|'.join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE)
        self.path_regex = re.compile('|'.join(self.PATH_TRAVERSAL_PATTERNS), re.IGNORECASE)
        self.cmd_regex = re.compile('|'.join(self.COMMAND_INJECTION_PATTERNS), re.IGNORECASE)

    def sanitize_string(
        self,
        input_str: str,
        max_length: Optional[int] = None,
        allow_html: bool = False,
        strip_whitespace: bool = True
    ) -> str:
        """Sanitize string input with various security checks"""
        if not isinstance(input_str, str):
            input_str = str(input_str)

        if strip_whitespace:
            input_str = input_str.strip()

        if max_length and len(input_str) > max_length:
            input_str = input_str[:max_length]

        if not allow_html:
            input_str = html.escape(input_str)

        input_str = self._remove_null_bytes(input_str)
        input_str = self._normalize_unicode(input_str)

        return input_str

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks"""
        if not filename:
            raise ValueError("Filename cannot be empty")

        filename = self.sanitize_string(filename, max_length=255)

        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

        name_without_ext = filename.rsplit('.', 1)[0].upper()
        if name_without_ext in reserved_names:
            filename = f"safe_{filename}"

        if filename.startswith('.'):
            filename = f"file{filename}"

        return filename

    def sanitize_user_query(self, query: str, max_length: int = 2000) -> str:
        """Sanitize user query for RAG system"""
        if not query:
            raise ValueError("Query cannot be empty")

        query = self.sanitize_string(query, max_length=max_length, strip_whitespace=True)

        if self._detect_injection_attempts(query):
            raise ValueError("Query contains potentially dangerous content")

        query = self._normalize_whitespace(query)

        return query

    def sanitize_dict(
        self,
        input_dict: Dict[str, Any],
        allowed_keys: Optional[List[str]] = None,
        max_value_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sanitize dictionary input"""
        if not isinstance(input_dict, dict):
            raise ValueError("Input must be a dictionary")

        sanitized = {}

        for key, value in input_dict.items():
            clean_key = self.sanitize_string(str(key), max_length=100)

            if allowed_keys and clean_key not in allowed_keys:
                continue

            if isinstance(value, str):
                clean_value = self.sanitize_string(value, max_length=max_value_length)
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            elif isinstance(value, dict):
                clean_value = self.sanitize_dict(value, max_value_length=max_value_length)
            elif isinstance(value, list):
                clean_value = [self.sanitize_string(str(item)) for item in value]
            else:
                clean_value = self.sanitize_string(str(value), max_length=max_value_length)

            sanitized[clean_key] = clean_value

        return sanitized

    def validate_secure_input(self, input_str: str, input_type: str = "general") -> Dict[str, Any]:
        """Comprehensive input validation with security analysis"""
        result = {
            'valid': True,
            'sanitized_value': '',
            'security_issues': [],
            'warnings': []
        }

        try:
            if not input_str:
                result['valid'] = False
                result['security_issues'].append("Empty input not allowed")
                return result

            sanitized = self.sanitize_string(input_str)
            result['sanitized_value'] = sanitized

            security_checks = self._perform_security_checks(input_str)

            if security_checks['has_issues']:
                result['valid'] = False
                result['security_issues'] = security_checks['issues']

            if security_checks['has_warnings']:
                result['warnings'] = security_checks['warnings']

            type_validation = self._validate_input_type(sanitized, input_type)
            if not type_validation['valid']:
                result['valid'] = False
                result['security_issues'].extend(type_validation['errors'])

        except Exception as e:
            result['valid'] = False
            result['security_issues'].append(f"Validation error: {str(e)}")

        return result

    def _detect_injection_attempts(self, input_str: str) -> bool:
        """Detect various injection attempt patterns"""
        lower_input = input_str.lower()

        if self.xss_regex.search(input_str):
            return True

        if self.sql_regex.search(lower_input):
            return True

        if self.path_regex.search(input_str):
            return True

        if self.cmd_regex.search(input_str):
            return True

        return False

    def _perform_security_checks(self, input_str: str) -> Dict[str, Any]:
        """Perform comprehensive security checks on input"""
        result = {
            'has_issues': False,
            'has_warnings': False,
            'issues': [],
            'warnings': []
        }

        if self.xss_regex.search(input_str):
            result['has_issues'] = True
            result['issues'].append("Potential XSS attack detected")

        if self.sql_regex.search(input_str.lower()):
            result['has_issues'] = True
            result['issues'].append("Potential SQL injection detected")

        if self.path_regex.search(input_str):
            result['has_issues'] = True
            result['issues'].append("Path traversal attempt detected")

        if self.cmd_regex.search(input_str):
            result['has_issues'] = True
            result['issues'].append("Command injection attempt detected")

        if len(input_str.encode('utf-8')) != len(input_str):
            result['has_warnings'] = True
            result['warnings'].append("Non-ASCII characters detected")

        if re.search(r'[^\x20-\x7E\n\r\t]', input_str):
            result['has_warnings'] = True
            result['warnings'].append("Special characters detected")

        return result

    def _validate_input_type(self, input_str: str, input_type: str) -> Dict[str, Any]:
        """Validate input based on expected type"""
        result = {'valid': True, 'errors': []}

        if input_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, input_str):
                result['valid'] = False
                result['errors'].append("Invalid email format")

        elif input_type == "username":
            if not re.match(r'^[a-zA-Z0-9_-]+$', input_str):
                result['valid'] = False
                result['errors'].append("Username contains invalid characters")
            if len(input_str) < 3 or len(input_str) > 50:
                result['valid'] = False
                result['errors'].append("Username must be 3-50 characters")

        elif input_type == "filename":
            try:
                self.sanitize_filename(input_str)
            except ValueError as e:
                result['valid'] = False
                result['errors'].append(str(e))

        return result

    def _remove_null_bytes(self, input_str: str) -> str:
        """Remove null bytes that could be used for attacks"""
        return input_str.replace('\x00', '')

    def _normalize_unicode(self, input_str: str) -> str:
        """Normalize unicode to prevent unicode-based attacks"""
        import unicodedata
        return unicodedata.normalize('NFKC', input_str)

    def _normalize_whitespace(self, input_str: str) -> str:
        """Normalize whitespace characters"""
        return re.sub(r'\s+', ' ', input_str).strip()


# Create a global instance to avoid recreating it every time
_global_sanitizer = InputSanitizer()


def sanitize_user_input(
    input_value: Union[str, Dict, List],
    input_type: str = "general",
    max_length: Optional[int] = None
) -> Any:
    """Convenience function for sanitizing user input"""

    if isinstance(input_value, str):
        validation = _global_sanitizer.validate_secure_input(input_value, input_type)
        if not validation['valid']:
            raise ValueError(f"Input validation failed: {', '.join(validation['security_issues'])}")
        return validation['sanitized_value']

    elif isinstance(input_value, dict):
        return _global_sanitizer.sanitize_dict(input_value, max_value_length=max_length)

    elif isinstance(input_value, list):
        return [_global_sanitizer.sanitize_string(str(item)) for item in input_value]

    else:
        return _global_sanitizer.sanitize_string(str(input_value), max_length=max_length)

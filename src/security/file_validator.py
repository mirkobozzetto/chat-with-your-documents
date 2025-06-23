# src/security/file_validator.py
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("⚠️ python-magic/libmagic not available, using basic file validation")

import hashlib
import tempfile
import os
from pathlib import Path
from typing import Dict, Tuple
from fastapi import HTTPException, status, UploadFile


class SecureFileValidator:
    """Comprehensive file validation with content analysis and security checks"""

    MIME_TYPE_MAPPING = {
        '.pdf': {'application/pdf'},
        '.docx': {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/zip'
        },
        '.txt': {'text/plain', 'text/x-python', 'application/octet-stream'},
        '.md': {'text/plain', 'text/markdown', 'text/x-markdown'}
    }

    MAGIC_SIGNATURES = {
        '.pdf': [b'%PDF-'],
        '.docx': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        '.txt': [],
        '.md': []
    }

    DANGEROUS_PATTERNS = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'data:text/html',
        b'<?php',
        b'<%',
        b'eval(',
        b'exec(',
        b'shell_exec',
        b'system(',
        b'passthru(',
        b'base64_decode'
    ]

    MAX_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}

    def __init__(self):
        self._init_magic()

    def _init_magic(self) -> None:
        """Initialize python-magic for MIME type detection"""
        if MAGIC_AVAILABLE:
            try:
                self.mime_detector = magic.Magic(mime=True)
            except Exception:
                self.mime_detector = None
                print("⚠️ python-magic initialization failed, using basic validation")
        else:
            self.mime_detector = None

    def validate_file_comprehensive(self, file: UploadFile) -> Dict[str, any]:
        """Comprehensive file validation with security analysis"""
        validation_result = {
            'valid': False,
            'file_info': {},
            'security_checks': {},
            'errors': []
        }

        try:
            basic_checks = self._validate_basic_properties(file)
            validation_result['file_info'] = basic_checks

            if not basic_checks['valid']:
                validation_result['errors'] = basic_checks['errors']
                return validation_result

            content_checks = self._validate_file_content(file)
            validation_result['security_checks'] = content_checks

            if not content_checks['valid']:
                validation_result['errors'] = content_checks['errors']
                return validation_result

            validation_result['valid'] = True

        except Exception as e:
            validation_result['errors'].append(f"Validation failed: {str(e)}")

        return validation_result

    def _validate_basic_properties(self, file: UploadFile) -> Dict[str, any]:
        """Validate basic file properties"""
        result = {
            'valid': True,
            'errors': [],
            'filename': file.filename,
            'size': 0,
            'extension': '',
            'content_type': file.content_type
        }

        if not file.filename:
            result['valid'] = False
            result['errors'].append("No filename provided")
            return result

        extension = Path(file.filename).suffix.lower()
        result['extension'] = extension

        if extension not in self.ALLOWED_EXTENSIONS:
            result['valid'] = False
            result['errors'].append(f"File type not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}")

        if self._contains_dangerous_filename(file.filename):
            result['valid'] = False
            result['errors'].append("Filename contains dangerous characters")

        return result

    def _validate_file_content(self, file: UploadFile) -> Dict[str, any]:
        """Validate file content and detect potential threats"""
        result = {
            'valid': True,
            'errors': [],
            'mime_type': '',
            'file_hash': '',
            'magic_signature_valid': False,
            'dangerous_content_found': False
        }

        try:
            file.file.seek(0)
            content = file.file.read()
            file.file.seek(0)

            if len(content) > self.MAX_SIZE_BYTES:
                result['valid'] = False
                result['errors'].append(f"File too large. Max size: {self.MAX_SIZE_BYTES // (1024*1024)}MB")
                return result

            result['file_hash'] = hashlib.sha256(content).hexdigest()

            extension = Path(file.filename).suffix.lower()

            mime_valid = self._validate_mime_type(content, extension)
            if not mime_valid:
                result['valid'] = False
                result['errors'].append("File content doesn't match extension")

            signature_valid = self._validate_magic_signature(content, extension)
            result['magic_signature_valid'] = signature_valid
            if not signature_valid and extension in ['.pdf', '.docx']:
                result['valid'] = False
                result['errors'].append("File signature validation failed")

            dangerous_content = self._scan_dangerous_content(content)
            result['dangerous_content_found'] = dangerous_content
            if dangerous_content:
                result['valid'] = False
                result['errors'].append("Dangerous content patterns detected")

            if extension == '.pdf':
                pdf_checks = self._validate_pdf_structure(content)
                if not pdf_checks:
                    result['valid'] = False
                    result['errors'].append("Invalid PDF structure")

        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Content validation failed: {str(e)}")

        return result

    def _contains_dangerous_filename(self, filename: str) -> bool:
        """Check for dangerous filename patterns"""
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        dangerous_names = ['con', 'prn', 'aux', 'nul', 'com1', 'com2', 'lpt1', 'lpt2']

        if any(char in filename for char in dangerous_chars):
            return True

        name_without_ext = Path(filename).stem.lower()
        return name_without_ext in dangerous_names

    def _validate_mime_type(self, content: bytes, extension: str) -> bool:
        """Validate MIME type matches file extension"""
        if not self.mime_detector:
            return True

        try:
            detected_mime = self.mime_detector.from_buffer(content)
            expected_mimes = self.MIME_TYPE_MAPPING.get(extension, set())

            if not expected_mimes:
                return True

            return detected_mime in expected_mimes
        except Exception:
            return True

    def _validate_magic_signature(self, content: bytes, extension: str) -> bool:
        """Validate file magic signature"""
        signatures = self.MAGIC_SIGNATURES.get(extension, [])

        if not signatures:
            return True

        return any(content.startswith(sig) for sig in signatures)

    def _scan_dangerous_content(self, content: bytes) -> bool:
        """Scan for dangerous content patterns"""
        content_lower = content.lower()

        return any(pattern in content_lower for pattern in self.DANGEROUS_PATTERNS)

    def _validate_pdf_structure(self, content: bytes) -> bool:
        """Basic PDF structure validation"""
        if not content.startswith(b'%PDF-'):
            return False

        if b'%%EOF' not in content:
            return False

        dangerous_pdf_patterns = [
            b'/JavaScript',
            b'/JS',
            b'/Launch',
            b'/EmbeddedFile',
            b'/XFA'
        ]

        return not any(pattern in content for pattern in dangerous_pdf_patterns)

    def create_secure_temp_file(self, file: UploadFile, validation_result: Dict) -> Tuple[str, str]:
        """Create secure temporary file with validated content"""
        if not validation_result['valid']:
            raise ValueError("Cannot create temp file for invalid file")

        try:
            file.file.seek(0)
            content = file.file.read()
            file.file.seek(0)

            suffix = Path(file.filename).suffix
            prefix = f"secure_upload_{validation_result['file_info']['file_hash'][:8]}_"

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix=prefix,
                mode='wb',
                dir=tempfile.gettempdir()
            ) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            os.chmod(temp_path, 0o600)

            return temp_path, validation_result['file_info']['file_hash']

        except Exception as e:
            raise Exception(f"Failed to create secure temp file: {str(e)}")


def validate_uploaded_file_secure(file: UploadFile) -> Dict[str, any]:
    """Secure file validation function for FastAPI endpoints"""
    validator = SecureFileValidator()
    validation_result = validator.validate_file_comprehensive(file)

    if not validation_result['valid']:
        error_details = "; ".join(validation_result['errors'])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {error_details}"
        )

    return validation_result

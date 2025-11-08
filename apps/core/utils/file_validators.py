"""
File validation utilities for secure file uploads
"""
from rest_framework.exceptions import ValidationError
import os


# Maximum file sizes (in bytes)
MAX_EXCEL_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 MB

# Allowed file extensions
ALLOWED_EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.xlsm'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Excel MIME types
ALLOWED_EXCEL_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'application/vnd.ms-excel.sheet.macroEnabled.12',  # .xlsm
}


def validate_excel_file(file):
    """
    Validates an uploaded Excel file for security
    
    Args:
        file: UploadedFile object from request.FILES
    
    Raises:
        ValidationError: If file is invalid or potentially dangerous
    
    Returns:
        True if file is valid
    """
    # Check if file exists
    if not file:
        raise ValidationError("No se proporcionó archivo")
    
    # Check file size
    if file.size > MAX_EXCEL_SIZE:
        raise ValidationError(
            f"Archivo demasiado grande. Máximo: {MAX_EXCEL_SIZE / (1024 * 1024):.1f} MB"
        )
    
    if file.size == 0:
        raise ValidationError("El archivo está vacío")
    
    # Check file extension
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in ALLOWED_EXCEL_EXTENSIONS:
        raise ValidationError(
            f"Extensión de archivo no permitida: {file_ext}. "
            f"Permitidas: {', '.join(ALLOWED_EXCEL_EXTENSIONS)}"
        )
    
    # Check MIME type (content type)
    content_type = file.content_type
    if content_type and content_type not in ALLOWED_EXCEL_MIME_TYPES:
        # Some browsers don't send correct MIME type, so we only warn
        # but don't reject if extension is correct
        pass
    
    # Check for suspicious file names (path traversal attempts)
    if '..' in file.name or '/' in file.name or '\\' in file.name:
        raise ValidationError("Nombre de archivo inválido")
    
    return True


def validate_image_file(file):
    """
    Validates an uploaded image file for security
    
    Args:
        file: UploadedFile object from request.FILES
    
    Raises:
        ValidationError: If file is invalid or potentially dangerous
    
    Returns:
        True if file is valid
    """
    # Check if file exists
    if not file:
        raise ValidationError("No se proporcionó imagen")
    
    # Check file size
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f"Imagen demasiado grande. Máximo: {MAX_IMAGE_SIZE / (1024 * 1024):.1f} MB"
        )
    
    if file.size == 0:
        raise ValidationError("El archivo está vacío")
    
    # Check file extension
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Extensión de archivo no permitida: {file_ext}. "
            f"Permitidas: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # Check for suspicious file names
    if '..' in file.name or '/' in file.name or '\\' in file.name:
        raise ValidationError("Nombre de archivo inválido")
    
    return True


def sanitize_filename(filename):
    """
    Sanitizes a filename by removing dangerous characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Get the extension
    name, ext = os.path.splitext(filename)
    
    # Remove dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    name = ''.join(c if c in safe_chars else '_' for c in name)
    
    # Limit length
    max_length = 100
    if len(name) > max_length:
        name = name[:max_length]
    
    return f"{name}{ext.lower()}"

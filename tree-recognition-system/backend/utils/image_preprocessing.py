"""
Image Preprocessing Utilities
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from typing import Union, Tuple
import os


class ImagePreprocessor:
    """
    Preprocesses images for tree recognition
    Handles resizing, enhancement, normalization
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        enhance_contrast: bool = True,
        enhance_sharpness: bool = False
    ):
        """
        Initialize image preprocessor
        
        Args:
            target_size: Target image size (width, height)
            enhance_contrast: Whether to enhance contrast
            enhance_sharpness: Whether to enhance sharpness
        """
        self.target_size = target_size
        self.enhance_contrast = enhance_contrast
        self.enhance_sharpness = enhance_sharpness
    
    def preprocess(
        self,
        image_path: Union[str, np.ndarray],
        return_array: bool = True
    ) -> Union[np.ndarray, Image.Image]:
        """
        Preprocess image for feature extraction
        
        Args:
            image_path: Path to image or numpy array
            return_array: If True, return numpy array; else PIL Image
            
        Returns:
            Preprocessed image
        """
        # Load image
        if isinstance(image_path, str):
            img = self._load_image(image_path)
        else:
            img = Image.fromarray(image_path)
        
        # Resize
        img = self._resize_image(img, self.target_size)
        
        # Enhance if enabled
        if self.enhance_contrast:
            img = self._enhance_contrast(img)
        
        if self.enhance_sharpness:
            img = self._enhance_sharpness(img)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        if return_array:
            return np.array(img)
        return img
    
    def _load_image(self, image_path: str) -> Image.Image:
        """Load image from path"""
        try:
            return Image.open(image_path)
        except Exception as e:
            print(f"Error loading image: {e}")
            # Return blank image as fallback
            return Image.new('RGB', self.target_size, color='white')
    
    def _resize_image(
        self,
        img: Image.Image,
        target_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Resize image maintaining aspect ratio
        
        Args:
            img: PIL Image
            target_size: Target size (width, height)
            
        Returns:
            Resized image
        """
        # Use thumbnail to maintain aspect ratio
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create new image with target size and paste resized image
        new_img = Image.new('RGB', target_size, color='white')
        # Center the image
        x_offset = (target_size[0] - img.size[0]) // 2
        y_offset = (target_size[1] - img.size[1]) // 2
        new_img.paste(img, (x_offset, y_offset))
        
        return new_img
    
    def _enhance_contrast(self, img: Image.Image, factor: float = 1.2) -> Image.Image:
        """Enhance image contrast"""
        try:
            enhancer = ImageEnhance.Contrast(img)
            return enhancer.enhance(factor)
        except Exception as e:
            print(f"Error enhancing contrast: {e}")
            return img
    
    def _enhance_sharpness(self, img: Image.Image, factor: float = 1.1) -> Image.Image:
        """Enhance image sharpness"""
        try:
            enhancer = ImageEnhance.Sharpness(img)
            return enhancer.enhance(factor)
        except Exception as e:
            print(f"Error enhancing sharpness: {e}")
            return img
    
    def normalize_image(self, img_array: np.ndarray) -> np.ndarray:
        """
        Normalize image array to [0, 1]
        
        Args:
            img_array: Image as numpy array
            
        Returns:
            Normalized image
        """
        if img_array.dtype != np.float32:
            img_array = img_array.astype(np.float32)
        
        # Normalize to [0, 1]
        if img_array.max() > 1.0:
            img_array = img_array / 255.0
        
        return img_array
    
    def validate_image(
        self,
        image_path: str,
        max_size_mb: int = 10,
        min_dimension: int = 100
    ) -> Tuple[bool, str]:
        """
        Validate image file
        
        Args:
            image_path: Path to image
            max_size_mb: Maximum file size in MB
            min_dimension: Minimum image dimension
            
        Returns:
            (is_valid, error_message)
        """
        # Check if file exists
        if not os.path.exists(image_path):
            return False, "Image file not found"
        
        # Check file size
        file_size = os.path.getsize(image_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"Image too large (max {max_size_mb}MB)"
        
        # Check if it's a valid image
        try:
            img = Image.open(image_path)
            img.verify()
            
            # Check dimensions
            img = Image.open(image_path)  # Reopen after verify
            width, height = img.size
            if width < min_dimension or height < min_dimension:
                return False, f"Image too small (min {min_dimension}x{min_dimension})"
            
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Invalid image: {str(e)}"
    
    def extract_region(
        self,
        image_path: Union[str, np.ndarray],
        bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    ) -> np.ndarray:
        """
        Extract region of interest from image
        
        Args:
            image_path: Path to image or numpy array
            bbox: Bounding box (x, y, width, height)
            
        Returns:
            Extracted region as numpy array
        """
        if isinstance(image_path, str):
            img = cv2.imread(image_path)
        else:
            img = image_path
        
        x, y, w, h = bbox
        roi = img[y:y+h, x:x+w]
        
        return roi

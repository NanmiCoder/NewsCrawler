# -*- coding: utf-8 -*-
"""
Image processing utilities for AI agents
"""
import base64
import io
from typing import Optional, Tuple
from PIL import Image
import httpx
from io import BytesIO


class ImageProcessor:
    """Image download and processing utilities"""

    @staticmethod
    async def download_image(url: str, timeout: int = 10) -> Optional[bytes]:
        """
        Download image from URL

        Args:
            url: Image URL
            timeout: Request timeout in seconds

        Returns:
            Image bytes or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
            return None

    @staticmethod
    def encode_image_to_base64(image_bytes: bytes, format: str = "JPEG") -> str:
        """
        Encode image bytes to base64 string

        Args:
            image_bytes: Image bytes
            format: Image format (JPEG, PNG, etc.)

        Returns:
            Base64 encoded string
        """
        try:
            # Load image
            img = Image.open(BytesIO(image_bytes))

            # Convert to RGB if necessary (for JPEG)
            if format.upper() == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background

            # Resize if too large (max 2048px on longest side)
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = BytesIO()
            img.save(output, format=format, quality=85)
            image_bytes = output.getvalue()

            # Encode to base64
            base64_str = base64.b64encode(image_bytes).decode('utf-8')
            return base64_str

        except Exception as e:
            print(f"Failed to encode image: {e}")
            raise

    @staticmethod
    async def download_and_encode(url: str, format: str = "JPEG") -> Optional[str]:
        """
        Download image and encode to base64

        Args:
            url: Image URL
            format: Target image format

        Returns:
            Base64 encoded string or None if failed
        """
        image_bytes = await ImageProcessor.download_image(url)
        if image_bytes:
            try:
                return ImageProcessor.encode_image_to_base64(image_bytes, format)
            except Exception as e:
                print(f"Failed to encode image from {url}: {e}")
                return None
        return None

    @staticmethod
    def get_image_mime_type(format: str) -> str:
        """
        Get MIME type for image format

        Args:
            format: Image format (JPEG, PNG, etc.)

        Returns:
            MIME type string
        """
        mime_types = {
            "JPEG": "image/jpeg",
            "JPG": "image/jpeg",
            "PNG": "image/png",
            "GIF": "image/gif",
            "WEBP": "image/webp",
        }
        return mime_types.get(format.upper(), "image/jpeg")

    @staticmethod
    def create_data_uri(base64_str: str, format: str = "JPEG") -> str:
        """
        Create data URI from base64 string

        Args:
            base64_str: Base64 encoded image
            format: Image format

        Returns:
            Data URI string
        """
        mime_type = ImageProcessor.get_image_mime_type(format)
        return f"data:{mime_type};base64,{base64_str}"

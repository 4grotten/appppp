import os

from PIL import Image
from imagekit import ImageSpec
from imagekit.utils import get_field_info
from pilkit.processors import ResizeToFit, Crop


class Watermark(object):
    def __init__(self, watermark_path: str):
        self.watermark_path = watermark_path

    def process(self, original):
        original = original.convert('RGB')
        min_len_side = min(original.width, original.height)
        resizer = ResizeToFit(min_len_side * 0.2)

        filename = os.path.join(os.path.dirname(__file__), self.watermark_path)
        watermark = Image.open(filename)
        watermark = resizer.process(watermark)

        if watermark.mode != 'RGBA':
            watermark = watermark.convert('RGBA')

        position = (original.width - int(watermark.width * 1.2), original.height - int(watermark.height * 1.2))
        original.paste(watermark, position, watermark)
        return original


class ResizeWatermarkedSpec(ImageSpec):
    format = 'JPEG'
    options = {'quality': 100}
    height = 600
    width = 600

    @property
    def processors(self):
        processors = [ResizeToFit(self.width, self.height, upscale=False)]
        model, field_name = get_field_info(self.source)
        # if str(model).endswith('.webp'):
        #     self.format = 'WEBP'
        if model.is_watermarked:
            processors.append(Watermark('watermark/watermark_logo.png'))
        return processors


class MobileWallpaper(ImageSpec):
    format = 'JPEG'
    options = {'quality': 100}
    height = 941
    width = 375

    @property
    def processors(self):
        processors = [Crop(self.width, self.height)]
        return processors

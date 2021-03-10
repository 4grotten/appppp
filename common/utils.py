import json
import posixpath
import hashlib
import datetime
import decimal
import uuid
import os
from pathlib import Path
from django.conf import settings

from django.core.serializers.json import DjangoJSONEncoder

from django.utils.crypto import get_random_string
from imagekit.cachefiles.namers import hash, source_name_dot_hash
from imagekit.utils import suggest_extension

LENGTH_OF_NUMBER = 6
ALLOWED_SYMBOLS = '123456789'


def generate_random_code():
    return int(get_random_string(LENGTH_OF_NUMBER, ALLOWED_SYMBOLS))


def upload_to_factory(prefix):
    def get_upload_path(instance, filename):
        name, ext = posixpath.splitext(filename)
        return posixpath.join(prefix, name + ext)

    return get_upload_path


def upload_file_with_original_file_name(instance, filename):
    opts = instance._meta

    return upload_to_factory(posixpath.join(
        opts.app_label,
        instance.__class__.__name__.lower(),
    ))(instance, filename)


def upload_file_with_unique_name(instance, filename):
    return Path(settings.MEDIA_UPLOAD_PREFIX).relative_to('/') / Path(
        hashlib.sha256(
            datetime.date.today().strftime('%Y%m').encode()
        ).hexdigest()[32:-16]
    ) / Path(str(uuid.uuid4())).with_suffix(
        Path(filename).suffix
    )


def imagekit_filename_generator(generator):
    # 'media/45428685bacab859/a2d7a138-6861-4609-b56e-3dbf97f0db4f.jpg'
    source_filename = getattr(generator.source, 'name', None)

    if source_filename is None or os.path.isabs(source_filename):
        return hash(generator)
    else:
        path = Path(source_filename)

        return str(
            path.with_name(f'{path.stem}-{generator.get_hash()[0:8]}').with_suffix(
                suggest_extension(source_filename or '', generator.format)
            )
        )


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            # this call is needed for request permissions
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


class DecimalEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return {"__type__": "decimal", "__value__": str(o)}
        else:
            return super().default(o)


class DecimalDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj: dict):
        if "__type__" in obj and "__value__" in obj:
            if obj["__type__"] == "decimal":
                return decimal.Decimal(obj["__value__"])
        return obj

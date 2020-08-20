import posixpath

from django.utils.crypto import get_random_string

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


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            # this call is needed for request permissions
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator

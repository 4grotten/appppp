import pytz
import six
from rest_framework import serializers

from .models import File, Currency, Country, City


class ImageSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    large = serializers.ImageField(read_only=True)
    medium = serializers.ImageField(read_only=True)
    small = serializers.ImageField(read_only=True)

    class Meta:
        model = File
        fields = ('id', 'file', 'name', 'large', 'medium', 'small')
        read_only_fields = ('name',)

    def get_name(self, obj):
        return obj.file.name.split("/")[-1]


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('code', 'name',)


class CountrySerializer(serializers.ModelSerializer):
    currency = CurrencySerializer()

    class Meta:
        model = Country
        fields = ('code', 'name', 'flag', 'currency')


class CitySerializer(serializers.ModelSerializer):
    country_code = serializers.CharField(source='country.code')

    class Meta:
        model = City
        fields = ('id', 'name', 'country_code', 'postal',)


class CountryCityQueryParamSerializer(serializers.Serializer):
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), default=None)
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), default=None)


class TimezoneField(serializers.Field):

    def to_representation(self, obj):
        return six.text_type(obj)

    def to_internal_value(self, time_zone):
        try:
            return pytz.timezone(str(time_zone))
        except pytz.UnknownTimeZoneError:
            raise serializers.ValidationError(
                "Unknown time zone: '%s'" % time_zone
            )


class FileRelatedField(serializers.RelatedField):
    default_error_messages = {
        'invalid': 'A valid integer is required.',
        'not_found': 'File does not exist.'
    }

    def to_representation(self, value):
        try:
            url = value.file.url
        except AttributeError:
            return None
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def to_internal_value(self, data):
        try:
            pk = int(data)
            return self.get_queryset().get(pk=pk)
        except ValueError:
            self.fail('invalid')
        except File.DoesNotExist:
            self.fail('not_found')

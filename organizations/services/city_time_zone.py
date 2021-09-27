from django.utils.timezone import make_aware
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

def get_timezone(time, city):
    print("Location address:", city)
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(city)
    print((location.latitude, location.longitude))
    obj = TimezoneFinder()
    time_zone = obj.timezone_at(lng=location.longitude, lat=location.latitude)   # pass the Latitude and Longitud into a timezone_at and it return timezone
    print("Time Zone : ", time_zone)
    tz = pytz.timezone(time_zone)
    ct = datetime.now(tz=tz)
    diff_hours = ct.strftime('%Z')
    print(diff_hours)

    naive = datetime.strptime(str(time), "%H:%M:%S")
    local_dt = tz.localize(naive)
    print(time)
    print(local_dt)
    # utc_dt = local_dt.astimezone(pytz.utc)
    # print(utc_dt)

    return diff_hours

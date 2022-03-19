MALE = 'male'
FEMALE = 'female'

GENDER_CHOICES = (
    (MALE, MALE.capitalize()),
    (FEMALE, FEMALE.capitalize())
)

SMS_CODE_MESSAGE = '{}  is your verification code'

PHONE_NUMBER_TYPE = 'phone_number'
EMAIL_TYPE = 'email'

FORGOT_PASSWORD_CHOICES = (
    (PHONE_NUMBER_TYPE, PHONE_NUMBER_TYPE),
    (EMAIL_TYPE, EMAIL_TYPE)
)

CHANGE_AUTH_NUMBER_TYPE = 'auth_number_type'
REGISTER_AUTH_TYPE = 'register_auth_type'

RESEND_CODE_CHOICES = (
    (CHANGE_AUTH_NUMBER_TYPE, CHANGE_AUTH_NUMBER_TYPE),
    (REGISTER_AUTH_TYPE, REGISTER_AUTH_TYPE)
)

DEVICE_TYPES = ('ios', 'android')

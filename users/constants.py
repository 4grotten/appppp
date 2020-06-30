MALE = 'male'
FEMALE = 'female'

GENDER_CHOICES = (
    (MALE, MALE.capitalize()),
    (FEMALE, FEMALE.capitalize())
)

SMS_CODE_MESSAGE = 'Your code is {}'

PHONE_NUMBER_TYPE = 'phone_number'
EMAIL_TYPE = 'email'

FORGOT_PASSWORD_CHOICES = (
    (PHONE_NUMBER_TYPE, PHONE_NUMBER_TYPE),
    (EMAIL_TYPE, EMAIL_TYPE)
)

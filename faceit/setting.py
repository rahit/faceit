__author__ = 'rahit'

from django.conf import settings

# A string describing the Facebook application's ID.
FACEBOOK_APPLICATION_ID = getattr(settings, 'FACEBOOK_APPLICATION_ID')

# A string describing the URL to redirect to upon authorizing users.
FACEBOOK_AUTHORIZATION_REDIRECT_URL = getattr(settings, 'FACEBOOK_AUTHORIZATION_REDIRECT_URL', None)

# A string describing the Facebook application's secret key.
FACEBOOK_APPLICATION_SECRET_KEY = getattr(settings, 'FACEBOOK_APPLICATION_SECRET_KEY')

# A list of strings describing `permissions <http://developers.facebook.com/docs/reference/api/permissions/>`_
# that will be requested upon authorizing the application.
FACEBOOK_APPLICATION_SCOPE =  getattr(settings, 'FACEBOOK_APPLICATION_SCOPE', None)


"""
A funtion to get the authentication url.

"""
def get_auth_url():
    scope = ','.join(FACEBOOK_APPLICATION_SCOPE)
    auth_url = "https://www.facebook.com/dialog/oauth?" \
               "client_id="+`FACEBOOK_APPLICATION_ID`+\
               "&redirect_uri="+FACEBOOK_AUTHORIZATION_REDIRECT_URL.__str__()+\
               "&scope="+scope.__str__()
    return auth_url
=====
Faceit
=====

A simple django module for authenticate user using their facebook account.
Nicely suited with default Auth module.

Thanks to Johannes Gorset's facepy(https://github.com/jgorset/facepy) module. Make sure you have it installed.
Faceit requires this module to communicate with Facebook.

Quick start
-----------

1. Make sure you have FacePy installed. https://github.com/jgorset/facepy

2. Add "faceit" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'faceit',
    )

2. specify these setting in your setting.py file.

    FACEBOOK_APPLICATION_ID = your facebook app id
    
    FACEBOOK_AUTHORIZATION_REDIRECT_URL = redirect url after authentication
    
    FACEBOOK_APPLICATION_SECRET_KEY = your facebook app secret key
    
    FACEBOOK_APPLICATION_SCOPE = a list of permission. ex: ['email', 'publish_stream']


**Note: Make sure you have specified *email* permission in scope.**

3. Run `python manage.py migrate` to create the faceit related models.

4. You can get authentication url `using get_auth_url()` function after importing `faceit.settings`

import random
import re
import string
from urlparse import parse_qs
from datetime import timedelta
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http.response import HttpResponseRedirect
from django.utils.timezone import now
from facepy.graph_api import GraphAPI
from faceit.models import Facebook, FacebookOAuthToken, FacebookProfile
from faceit.setting import FACEBOOK_APPLICATION_ID, FACEBOOK_AUTHORIZATION_REDIRECT_URL, FACEBOOK_APPLICATION_SECRET_KEY


__author__ = 'rahit'


def get_full_path(request, remove_querystrings=[]):
    """Gets the current path, removing specified querstrings"""

    path = request.get_full_path()
    for qs in remove_querystrings:
        path = re.sub(r'&?' + qs + '=?(.+)?&?', '', path)
    return path


def password_generator():
    chars = string.letters + string.digits
    return ''.join(random.choice(chars) for x in range(12))



"""
A Middleware class to check, update, create Facebook profile in our site
Also it login user using extended FaceitBackend

"""
class FaceitMiddleware():

    def process_request(self, request):
        # user already authed
        if request.user.is_authenticated() or (hasattr(request, 'facebook') and request.facebook):
            return

        # User is not authed. Lets init some variables to play with
        request.facebook = Facebook()
        oauth_token = False


        # User may redirect after they granted us to access their facebook.
        # Now we are going to do some business with facebook.
        if 'code' in request.GET:
            try:
                graph = GraphAPI()
                # Don't disturb!!! doing business with Mr. Zuckerberg
                response = graph.get(
                    'oauth/access_token',
                    client_id=FACEBOOK_APPLICATION_ID,
                    redirect_uri=FACEBOOK_AUTHORIZATION_REDIRECT_URL,
                    client_secret=FACEBOOK_APPLICATION_SECRET_KEY,
                    code=request.GET['code']
                )
                parsed_response = parse_qs(response)

                # We got a virgin OAuth Token from Facebook. Now we gonna put it into our DB.
                oauth_token, new_oauth_token = FacebookOAuthToken.objects.get_or_create(
                    token=parsed_response['access_token'][0],
                    issued_at=now(),
                    expires_at=now() + timedelta(seconds=int(parsed_response['expires'][0]))
                )

            except GraphAPI.OAuthError as error:
                pass

        # the user may already bring a token for us in past. Lets check our cookie for that
        elif 'facebook_oauth_token' in request.COOKIES:
            try:
                # we got the cookie. But wait!!! We should have it in our DB too. let's cross check
                oauth_token = FacebookOAuthToken.objects.get(token=request.COOKIES['facebook_oauth_token'])
            except FacebookOAuthToken.DoesNotExist:
                request.facebook = False
                return

        # NO code from Facebook or NO Access Token stored in cookie.
        # how the heck I gonna identify you?
        if not oauth_token or oauth_token.expired:
            request.facebook = False
            return


        # GREAT!!! You must have a valid access token...
        try:
            facebook_profile = oauth_token.facebookprofile
            if not facebook_profile.authorized:
                request.facebook = False
            facebook_profile.last_seen_at = now()
            facebook_profile.save()
        except FacebookProfile.DoesNotExist:
            # No Facebook Profile found against the current oauth token
            graph = GraphAPI(oauth_token.token)
            profile = graph.get('me')

            # Two Possibilities:
            # 1. User already have their Facebook profile with us and we need to integrate this new token
            # 2. User didn't connect it yet. But they want to connect now.
            try:
                # case 1:
                facebook_profile = FacebookProfile.objects.get(facebook_id=profile.get('id'))
                if not facebook_profile.authorized:
                    if new_oauth_token:
                        facebook_profile.authorized = True
                        facebook_profile.last_seen_at = now()
                    else:
                        request.facebook = False
                        return
            except FacebookProfile.DoesNotExist:
                # case 2:
                email = profile.get('email')
                # lets check whether we have already an account for this email or not
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    username = email.split('@')[0]
                    user = User.objects.create(
                                username=username,
                                email=email,
                                password=password_generator(),
                                first_name=profile.get('first_name'),
                                last_name=profile.get('last_name'),
                            )
                facebook_profile = FacebookProfile.objects.create(
                    user = user,
                    facebook_id = profile.get('id'),
                    email = email,
                    oauth_token = oauth_token
                )

            facebook_profile.synchronize(profile)

            # Delete previous access token if there is any and its not same as current
            prev_oauth_token = None
            if facebook_profile.oauth_token != oauth_token:
                prev_oauth_token = facebook_profile.oauth_token
                facebook_profile.oauth_token = oauth_token

            facebook_profile.save()
            if prev_oauth_token:
                prev_oauth_token.delete()

        if facebook_profile.oauth_token.extended:
            try:
                facebook_profile.oauth_token.extend()
            except:
                pass

        request.facebook.facebookprofile = facebook_profile
        request.facebook.oauth_token = oauth_token
        user = authenticate(username=facebook_profile.user.username, password=oauth_token)
        login(request, user)


    def process_response(self, request, response):
        """
        Set compact P3P policies and save auth token to cookie.

        P3P is a WC3 standard (see http://www.w3.org/TR/P3P/), and although largely ignored by most
        browsers it is considered by IE before accepting third-party cookies (ie. cookies set by
        documents in iframes). If they are not set correctly, IE will not set these cookies.
        """
        if hasattr(request, "facebook") and request.facebook and request.facebook.oauth_token:
            if "code" in request.REQUEST:
                """ Remove auth related query params """
                path = get_full_path(request, remove_querystrings=['code', 'web_canvas'])
                response = HttpResponseRedirect(path)

            response.set_cookie('facebook_oauth_token', request.facebook.oauth_token.token)
        else:
            response.delete_cookie('facebook_oauth_token')

        response['P3P'] = 'CP="IDC CURa ADMa OUR IND PHY ONL COM STA"'

        return response

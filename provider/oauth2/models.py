"""
Default model implementations. Custom database or OAuth backends need to
implement these models with fields and methods to be compatible with the
views in :attr:`provider.views`.
"""
from datetime import datetime as dt

from django.conf import settings
from mongoengine import *

from .. import utils
from ..constants import SCOPES, CLIENT_TYPES

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Client(Document):
    """
    Default client implementation.

    Expected fields:

    * :attr:`user`
    * :attr:`name`
    * :attr:`url`
    * :attr:`redirect_url`
    * :attr:`client_id`
    * :attr:`client_secret`
    * :attr:`client_type`

    Clients are outlined in the :draft:`2` and its subsections.
    """
    user = ReferenceField(AUTH_USER_MODEL, related_name='oauth2_client', required=False)
    name = CharField(max_length=255, required=False)
    url = URLField(help_text="Your application's URL.")
    redirect_uri = URLField(help_text="Your application's callback URL")
    client_id = CharField(max_length=255, default=utils.short_token)
    client_secret = CharField(max_length=255, default=utils.long_token)
    client_type = IntegerField(choices=CLIENT_TYPES)

    def __unicode__(self):
        return self.redirect_uri


class Grant(Document):
    """
    Default grant implementation. A grant is a code that can be swapped for an
    access token. Grants have a limited lifetime as defined by
    :attr:`provider.constants.EXPIRE_CODE_DELTA` and outlined in
    :draft:`4.1.2`

    Expected fields:

    * :attr:`user`
    * :attr:`client` - :class:`Client`
    * :attr:`code`
    * :attr:`expires` - :attr:`dt.dt`
    * :attr:`redirect_uri`
    * :attr:`scope`
    """
    user = ReferenceField(AUTH_USER_MODEL)
    client = ReferenceField(Client)
    code = CharField(max_length=255, default=utils.long_token)
    expires = DateTimeField(default=utils.get_code_expiry)
    redirect_uri = CharField(max_length=255, required=False)
    scope = IntegerField(default=0)

    def __unicode__(self):
        return self.code


class AccessToken(Document):
    """
    Default access token implementation. An access token is a time limited
    token to access a user's resources.

    Access tokens are outlined :draft:`5`.

    Expected fields:

    * :attr:`user`
    * :attr:`token`
    * :attr:`client` - :class:`Client`
    * :attr:`expires` - :attr:`dt.dt`
    * :attr:`scope`

    Expected methods:

    * :meth:`get_expire_delta` - returns an integer representing seconds to
        expiry
    """
    user = ReferenceField(AUTH_USER_MODEL)
    token = CharField(max_length=255, default=utils.long_token)
    client = ReferenceField(Client)
    expires = DateTimeField(default=utils.get_token_expiry)
    scope = IntegerField(default=SCOPES[0][0],
            choices=SCOPES)

    def __unicode__(self):
        return self.token

    def get_expire_delta(self):
        """
        Return the number of seconds until this token expires.
        """
        return (self.expires - dt.now()).seconds

    @classmethod
    def get_token(cls, token, **kwargs):
        qs = cls.objects(token=token, expires__gt=dt.now(), **kwargs)
        token = qs.get()
        return token


class RefreshToken(Document):
    """
    Default refresh token implementation. A refresh token can be swapped for a
    new access token when said token expires.

    Expected fields:

    * :attr:`user`
    * :attr:`token`
    * :attr:`access_token` - :class:`AccessToken`
    * :attr:`client` - :class:`Client`
    * :attr:`expired` - ``boolean``
    """
    user = ReferenceField(AUTH_USER_MODEL)
    token = CharField(max_length=255, default=utils.long_token)
    access_token = ReferenceField(AccessToken)
    client = ReferenceField(Client)
    expired = BooleanField(default=False)

    def __unicode__(self):
        return self.token

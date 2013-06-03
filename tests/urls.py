from provider.compat.urls import *

urlpatterns = patterns('',
    url(r'^oauth2/', include('provider.oauth2.urls', namespace = 'oauth2')),
)

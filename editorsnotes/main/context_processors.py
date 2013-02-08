from django_browserid.forms import BrowserIDForm

def browserid(request):
    """
    A context processor necessary for BrowserID auth

    Similar to django_browserid.context_processors, but in addition to the
    BrowserID form, we include whether a user has been logged on via the
    BrowserID authentication backend.
    """
    auth_backend = request.session.get('_auth_user_backend', None)
    return {
        'browserid_form': BrowserIDForm(),
        'browserid_authenticated': auth_backend == 'django_browserid.auth.BrowserIDBackend'
    }

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.utils.http import urlsafe_base64_encode

def send_activation_email(request, user):
    b64uid = urlsafe_base64_encode(str(user.id))
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)

    site_url = '{protocol}://{site}'.format(
        protocol='https' if request.is_secure() else 'http',
        site=settings.SITE_URL
    )

    if user.is_active:
        raise Exception('Will not send activation key to active user')

    send_mail(
        'Activate your Editors\' Notes account',

        'This email was used to create an account at {site_url}.\n\n'
        'To activate your account, visit the following link:\n\n'
        '\t{site_url}{activation_url}\n\n'
        'If you did not request an account, please ignore this email.'.format(
            site_url=site_url,
            activation_url=reverse('auth:activate_account', args=[b64uid, token]),
            activation_token=token),

        settings.SERVER_EMAIL,
        [user.email]
    )

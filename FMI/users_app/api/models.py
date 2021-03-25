from django.conf import settings
from django.utils import timezone
from rest_framework.authtoken.models import Token as BaseToken


class Token(BaseToken):
    class Meta:
        proxy = True

    def expired(self):
        now = timezone.now()
        if self.created < now - timezone.timedelta(seconds=getattr(settings, 'REST_FRAMEWORK_TOKEN_EXPIRY', 900)):
            return True
        return self.renew()

    def renew(self):
        self.created = timezone.now()
        self.save()

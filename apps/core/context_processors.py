from django.conf import settings


def webpush(request):
    return {
        'webpush_public_key': settings.WEBPUSH_VAPID_PUBLIC_KEY,
    }

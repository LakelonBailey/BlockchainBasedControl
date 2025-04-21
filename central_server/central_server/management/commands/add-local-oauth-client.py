# Package Imports
from django.core.management import base as management_base
from oauth2_provider.models import Application


# Fun algorithm that you won't understand
class Command(management_base.BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("client_id")

    def handle(self, *args, **options):
        client_ids = options.get("client_id").split(",")
        origins = ["http://localhost:5173"]
        for i, origin in enumerate(origins):
            client_id = client_ids[i]
            data = {
                "algorithm": "RS256",
                "allowed_origins": origin,
                "authorization_grant_type": "authorization-code",
                "client_id": client_id,
                "client_type": "public",
                "hash_client_secret": True,
                "name": origin.replace("http://", ""),
                "post_logout_redirect_uris": f"{origin}/oauth/logged-out/",
                "redirect_uris": f"{origin}/oauth/callback/",
                "skip_authorization": True,
            }
            app, _ = Application.objects.get_or_create(allowed_origins=origin)
            for key, val in data.items():
                setattr(app, key, val)

            app.save()

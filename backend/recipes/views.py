from django.shortcuts import get_object_or_404, redirect
from rest_framework import views

from .models import ShortLink


class ShortLinkRedirectView(views.APIView):
    """Redirects from a short link to a recipe page."""

    def get(self, request, token):
        """Redirects to a recipe page."""
        short_link = get_object_or_404(ShortLink, token=token)
        return redirect(f'/recipes/{short_link.recipe.id}/')

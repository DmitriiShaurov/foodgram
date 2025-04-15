from rest_framework.pagination import PageNumberPagination
from django.conf import settings


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class that extends PageNumberPagination.
    """

    page_size = settings.CUSTOM_PAGINATION_PAGE_LIMIT
    page_size_query_param = 'limit'

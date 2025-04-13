from django_filters.rest_framework import FilterSet, CharFilter
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag
from users.models import UserDetail

class IngredientFilter(FilterSet):
    """
    Custom filter for Ingredient model that allows filtering by
    the beginning of the name (case-insensitive).
    """
    name = CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = (
            'name',
        )

class RecipeFilter(FilterSet):
    """
    Custom filter for Recipe model with support for filtering by tags, author,
    favorites status, and shopping cart inclusion.
    """
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = filters.ModelChoiceFilter(
        queryset=UserDetail.objects.all(),
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )
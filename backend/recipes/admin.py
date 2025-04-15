from django.contrib import admin

from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    FavoriteRecipe,
    ShoppingCart,
)


class RecipeIngredientInline(admin.TabularInline):
    """Inline admin for RecipeIngredient model."""
    model = RecipeIngredient
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    """Admin configuration for Recipe model."""

    inlines = [
        RecipeIngredientInline,
    ]
    filter_horizontal = ('tags',)


admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient)
admin.site.register(FavoriteRecipe)
admin.site.register(ShoppingCart)

from django.contrib import admin

from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    FavoriteRecipe,
    ShoppingCart,
    ShortLink
)

admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(FavoriteRecipe)
admin.site.register(ShoppingCart)
admin.site.register(ShortLink)


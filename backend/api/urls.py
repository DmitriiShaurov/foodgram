from django.urls import path, include
from rest_framework import routers

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartView,
    TagViewSet,
    UserViewSet,
    UserMeAvatarView,
    SubscriptionsListView,
    SubscribeView,
    FavoriteRecipeView,
    DownloadShoppingCartView
)

router_v1 = routers.DefaultRouter()
router_v1.register(
    'ingredients',
    IngredientViewSet,
)

router_v1.register(
    'recipes',
    RecipeViewSet,
)

router_v1.register(
    'tags',
    TagViewSet,
)

router_v1.register(
    'users',
    UserViewSet,
)

urlpatterns = [
    path(
        'users/me/avatar/',
        UserMeAvatarView.as_view(),
        name='avatar'
    ),
    path(
        'users/subscriptions/',
        SubscriptionsListView.as_view(),
        name='subscriptions'
    ),
    path(
        'users/<int:id>/subscribe/',
        SubscribeView.as_view(),
        name='subscribe'
    ),
    path(
        'recipes/<int:id>/favorite/',
        FavoriteRecipeView.as_view(),
        name='favorite'
    ),
    path(
        'recipes/<int:id>/shopping_cart/',
        ShoppingCartView.as_view(),
        name='shopping_cart'
    ),
    path(
        'recipes/download_shopping_cart/',
        DownloadShoppingCartView.as_view(),
        name='download-shopping-cart'
    ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

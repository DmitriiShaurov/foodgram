from django.urls import path, include
from rest_framework import routers
from djoser.views import UserViewSet as DjoserUserViewSet
from .views import (
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartView,
    TagViewSet,
    UserViewSet,
    UserMeView,
    UserMeAvatarView,
    SubscriptionsListView,
    SubscribeView,
    FavoriteRecipeView,
    GetRecipeLinkView,
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
        'users/set_password/',
        DjoserUserViewSet.as_view({'post': 'set_password'})
    ),
    path(
        'users/me/avatar/',
        UserMeAvatarView.as_view(),
        name='avatar'
    ),
    path(
        'users/me/',
        UserMeView.as_view(),
        name='me'
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
        'recipes/<int:id>/get-link/',
        GetRecipeLinkView.as_view(),
        name='get-recipe-link'
    ),
    path(
        'recipes/download_shopping_cart/',
        DownloadShoppingCartView.as_view(),
        name='download-shopping-cart'
    ),
    path(
        'auth/',
        include('djoser.urls.authtoken')
    ),
    path('', include(router_v1.urls)),
]

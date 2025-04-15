from djoser.views import UserViewSet as DjoserUserViewSet
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, views, generics, permissions, status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.response import Response
from rest_framework.decorators import action
from django.conf import settings

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from recipes.models import (
    Ingredient,
    Recipe,
    Tag,
    FavoriteRecipe,
    ShoppingCart,
    RecipeIngredient,
)
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    UserMeAvatarSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
    ShoppingCartSerializer,
    FavoriteRecipeSerializer,
    SubscriptionSerializer,
    SubscriptionCreateSerializer,
)

from users.models import User, Subscription


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for the Tag model.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for the Ingredient model.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for the Recipe model."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        """Gets a short link for a recipe."""
        recipe = self.get_object()
        short_link = (
            f'{settings.BASE_URL}/r'
            f'/{recipe.short_link_token}/'
        )

        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )


class DownloadShoppingCartView(views.APIView):
    """View to download a shopping cart as TXT file."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """Download a shopping cart"""
        user = request.user

        # Get all the recipes
        recipes_in_cart = Recipe.objects.filter(in_shopping_cart__user=user)
        if not recipes_in_cart.exists():
            return Response(
                {'detail': 'There are no recipes in a shopping cart'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Aggregate ingredients
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes_in_cart
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        # Create TXT file
        content = [
            'Список покупок\n',
            f'Пользователь: {user.username}\n',
            '=' * 50 + '\n\n'
        ]

        for i, item in enumerate(ingredients, 1):
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']

            line = f'{i}. {name} ({unit}) — {amount}\n'
            content.append(line)

        # Return HTTP response with a TXT file
        response = HttpResponse(
            ''.join(content),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'

        return response


class UserViewSet(DjoserUserViewSet):
    """
    ViewSet for the User model,
    extending Djoser UserViewSet.
    """

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[
            permissions.IsAuthenticated,
        ]
    )
    def me(self, request):
        return super().me(request)


class UserMeAvatarView(views.APIView):
    """View to update or delete the user's avatar."""

    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request):
        """Update the current user's avatar."""
        serializer = UserMeAvatarSerializer(
            request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request):
        """Remove the current user's avatar."""
        user = request.user
        if not user.avatar:
            return Response(
                {'detail': 'There is no avatar to delete.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user.avatar.delete()
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeView(views.APIView):
    """View to add or remove a user from a subscription list."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionCreateSerializer(
            data={'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        follower = request.user
        following = get_object_or_404(User, id=id)

        deleted_count, _ = Subscription.objects.filter(
            user=follower,
            author=following
        ).delete()

        if not deleted_count:
            return Response(
                {'detail': 'You are not subscribed to this user.'},
                status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):
    """View to get current user subscriptions."""

    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(
            following__user=self.request.user)


class FavoriteRecipeView(views.APIView):
    """View to add or delete a recipe from a favorite list."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        """Add a recipe to a favorite list."""
        recipe = get_object_or_404(Recipe, id=id)
        serializer = FavoriteRecipeSerializer(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Delete a recipe from a favorite list."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)

        deleted_count, _ = FavoriteRecipe.objects.filter(
            user=user,
            recipe=recipe
        ).delete()

        if not deleted_count:
            return Response(
                {'detail': 'The recipe is not in your favorites.'},
                status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(views.APIView):
    """View to add/delete recipes to a shopping cart."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        """Add a recipe to a shopping cart."""
        recipe = get_object_or_404(Recipe, id=id)
        serializer = ShoppingCartSerializer(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Delete a recipe from a shopping cart."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)

        deleted_count, _ = ShoppingCart.objects.filter(
            user=user,
            recipe=recipe
        ).delete()

        if not deleted_count:
            return Response(
                {'detail': 'The recipe is not in your shopping cart.'},
                status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ShortLinkRedirectView(views.View):
    """Redirects from a short link to a recipe page."""

    def get(self, request, token):
        """Redirects to a recipe page."""
        recipe = get_object_or_404(
            Recipe,
            short_link_token=token
        )

        redirect_url = f'{settings.BASE_URL}/recipes/{recipe.id}/'

        return HttpResponseRedirect(redirect_url)

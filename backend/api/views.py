import os

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, views, generics, permissions, status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from recipes.models import (
    Ingredient,
    Recipe,
    Tag,
    FavoriteRecipe,
    ShoppingCart,
    ShortLink,
    RecipeIngredient
)
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserMeSerializer,
    UserMeAvatarSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
    SubscriptionSerializer,
    RecipeShortSerializer
)

from users.models import UserDetail, Subscription


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


class GetRecipeLinkView(views.APIView):
    """View to get a recipe short link."""


    def get(self, request, id):
        """Gets a recipe short link."""
        recipe = get_object_or_404(Recipe, id=id)
        short_link = ShortLink.objects.filter(recipe=recipe).first()

        # Check if a short link already exists
        if not short_link:
            token = ShortLink.generate_token()
            short_link = ShortLink.objects.create(recipe=recipe, token=token)

        return Response(
            {"short-link": short_link.get_absolute_url()},
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
                {"detail": "There are no recipes in a shopping cart"},
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
        response = HttpResponse(''.join(content), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

        return response


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for the UserDetail model.
    """
    queryset = UserDetail.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """Returns a serializer depending on an action."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer


class UserMeView(views.APIView):
    """View to retrieve information about yourself."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """Retrieve the current user's profile information."""
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


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


        old_avatar_path = user.avatar.path
        user.avatar = None
        user.save()

        # Remove avatar from disk
        if os.path.exists(old_avatar_path):
            os.remove(old_avatar_path)

        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeView(views.APIView):
    """View to add or remove a user from a subscription list."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        author = get_object_or_404(UserDetail, id=id)
        serializer = SubscriptionSerializer(
            data={},
            context={'request': request, 'author': author}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        follower = request.user
        following = get_object_or_404(UserDetail, id=id)

        subscription = Subscription.objects.filter(user=follower, author=following)
        if not subscription.exists():
            return Response(
                {'detail': 'You are no subscribed for this user.'},
                status=status.HTTP_400_BAD_REQUEST)

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):
    """View to get current user subscriptions."""

    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class FavoriteRecipeView(views.APIView):
    """View to add or delete a recipe from a favorite list."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, id):
        """Add a recipe to a favorite list"""
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)

        favorite, created = FavoriteRecipe.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            return Response(
                {'detail': 'The recipe is already in a favorite list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Delete a recipe to a favorite list."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)

        favorite_recipe = FavoriteRecipe.objects.filter(
            user=user,
            recipe=recipe
        )
        if not favorite_recipe.exists():
            return Response(
                {'detail': 'The recipe is not in a favorite list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(views.APIView):
    """View to add/delete recipes to a shopping cart."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Add a recipe to a shopping cart."""
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user

        # Check if a recipe is already in a shopping cart
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'The recipe is already in a shopping cart.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add a recipe to a shopping cart
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, id):
        """Delete a recipe from a shopping cart."""
        user = request.user
        recipe = get_object_or_404(
            Recipe,
            id=id
        )
        shopping_cart_item = ShoppingCart.objects.filter(
            user=user,
            recipe=recipe
        )

        if not shopping_cart_item.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        shopping_cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

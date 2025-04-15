import base64
import uuid

from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework import serializers

from users.models import User, Subscription
from recipes.models import (
    Ingredient,
    Recipe,
    Tag,
    FavoriteRecipe,
    ShoppingCart,
    RecipeIngredient
)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model instances"""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model instances"""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model instances"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'is_subscribed',
            'avatar',
            'password',
        )

        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        """Check if a recipe is favorited."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )


class Base64ImageField(serializers.Field):
    """Custom field for handling base64-encoded images."""

    def to_internal_value(self, data):
        """Converts a base64 string to a Django file object."""

        if not data:
            raise serializers.ValidationError('Image can not be empty.')

        if isinstance(data, str) and data.startswith('data:image'):
            # Example: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEA..."
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]

                # Generate unique name
                filename = f'{uuid.uuid4()}.{ext}'

                # Decode base64 encoded data into binary format
                data = ContentFile(base64.b64decode(imgstr), name=filename)

                return data
            except Exception as e:
                raise serializers.ValidationError(
                    f'Invalid image format: {str(e)}'
                )

        raise serializers.ValidationError(
            'Invalid image format, base64 line is expected.'
        )

    def to_representation(self, value):
        """Returns image URL."""
        if value and hasattr(value, 'url'):
            return value.url
        return None


class UserMeAvatarSerializer(serializers.ModelSerializer):
    """Serializer to update or delete the user's avatar."""
    avatar = Base64ImageField(
        required=True
    )

    class Meta:
        model = User
        fields = (
            'avatar',
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Serializer for ingredients when creating a recipe."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer to create or update a recipe."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = IngredientInRecipeSerializer(
        many=True,
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        """Validates all fields."""

        # Check ingredients
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'This field is required.'}
            )

        ingredients_data = data.get('ingredients', [])
        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': 'At least one ingredient must be specified.'}
            )

        ingredient_ids = [item['id'].id for item in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ingredients should not be repeated.'}
            )

        # Check tags
        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'This field is required.'}
            )

        tags_data = data.get('tags', [])
        if not tags_data:
            raise serializers.ValidationError(
                {'tags': 'At least one tag must be specified.'}
            )

        tag_ids = [tag.id for tag in tags_data]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Tags should not be repeated.'}
            )

        return data

    @staticmethod
    def _create_recipe_ingredients(
            recipe: Recipe,
            ingredients_data: list[Ingredient]
    ) -> None:
        """Creates recipe ingredients."""
        recipe_ingredients = []
        for ingredient_item in ingredients_data:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient_item['id'],
                    amount=ingredient_item['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        self._create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)

        RecipeIngredient.objects.filter(
            recipe=instance
        ).delete()

        self._create_recipe_ingredients(
            instance,
            ingredients_data
        )

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Serializer for reading ingredient information in recipes."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Serializer to read Recipe."""

    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        """Checks if a recipe is favorite."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and FavoriteRecipe.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Checks if a recipe is in a shopping cart."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Serializer for short recipe representation."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ShortLinkSerializer(serializers.Serializer):
    """Serializer for a recipe short link."""
    short_link = serializers.CharField(source='get_absolute_url')


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = FavoriteRecipe
        fields = (
            'user',
            'recipe',
        )

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if FavoriteRecipe.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'The recipe is already in your favorites.'
            )

        return data

    def to_representation(self, instance):
        """Return recipe in short format after adding to favorites."""
        return RecipeShortSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for Shopping Cart"""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe',
        )

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'The recipe is already in your shopping cart.'
            )

        return data

    def to_representation(self, instance):
        """Return recipe in short format after adding to shopping cart."""
        return RecipeShortSerializer(instance.recipe).data


class SubscriptionSerializer(UserSerializer):
    """Serializer for user subscriptions."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Gets recipes with optional limit."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass

        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Gets number of recipes."""
        return obj.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer to create subscription."""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = (
            'user',
            'author',
        )

    def validate(self, data):
        user = data['user']
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                'You can\'t subscribe to yourself.'
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'You are already subscribed for this user.'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionSerializer(
            instance.author,
            context={'request': request}
        ).data


class CustomUserSerializer(UserSerializer):
    """Custom Serializer for Djoser."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Checks subscription."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.follower.filter(
                author=obj
            ).exists()
        )

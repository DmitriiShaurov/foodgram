import base64
import uuid

from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework import serializers

from users.models import UserDetail, Subscription
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
        model = UserDetail
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
        """Check if a user is subscribed."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, author=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for User model instances"""

    class Meta:
        model = UserDetail
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """Create a user with hashed password."""
        return UserDetail.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )


class UserMeSerializer(serializers.ModelSerializer):
    """Serializer to return user information about himself/herself."""
    is_subscribed = serializers.BooleanField(
        default=False,
        read_only=True,
    )

    class Meta:
        model = UserDetail
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )


class Base64ImageField(serializers.Field):
    """Custom field for handling base64-encoded images."""

    def to_internal_value(self, data):
        """Converts a base64 string to a Django file object."""

        if not data:
            raise serializers.ValidationError("Image can not be empty.")

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
                raise serializers.ValidationError(f'Invalid image format: {str(e)}')

        raise serializers.ValidationError('Invalid image format, base64 line is expected.')

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
        model = UserDetail
        fields = (
            'avatar',
        )


class IngredientInRecipeSerializer(serializers.Serializer):
    """Serializer for ingredients when creating a recipe."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=1
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
        """Validates fields."""
        if self.instance:
            if 'ingredients' not in data:
                raise serializers.ValidationError({'ingredients': 'This fields is required.'})
            if 'tags' not in data:
                raise serializers.ValidationError({'tags': 'This fields is required'})

        return data

    def validate_name(self, value):
        """Validates Recipe name."""
        if not self.instance:
            if Recipe.objects.filter(name=value).exists():
                raise serializers.ValidationError('The recipe with such name already exists.')

        else:
            if Recipe.objects.filter(name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError('The recipe with such name already exists.')
        return value

    def validate_ingredients(self, value):
        """Validates Ingredients."""
        if not value:
            raise serializers.ValidationError('At least one ingredient must be specified.')

        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ingredients should not be repeated.')

        return value

    def validate_tags(self, value):
        """Validates tags"""
        if not value:
            raise serializers.ValidationError('At least one tag must be specified')

        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Tags should not be repeated.')

        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

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

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            RecipeIngredient.objects.filter(recipe=instance).delete()
            recipe_ingredients = []
            for ingredient_item in ingredients_data:
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=instance,
                        ingredient=ingredient_item['id'],
                        amount=ingredient_item['amount']
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
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
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

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
        if request and request.user.is_authenticated:
            return FavoriteRecipe.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Checks if a recipe is in a shopping cart."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


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


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer to add or remove recipes from a shopping cart."""

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe',
        )
        read_only_fields = (
            'user',
            'recipe',
        )


class ShortLinkSerializer(serializers.Serializer):
    """Serializer for a recipe short link."""
    short_link = serializers.CharField(source='get_absolute_url')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions with recipes."""
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    email = serializers.ReadOnlyField(source='author.email')
    is_subscribed = serializers.BooleanField(default=True, read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def validate(self, data):
        request = self.context.get('request')
        follower = request.user
        author = self.context.get('author')

        if follower == author:
            raise serializers.ValidationError(
                "You can't subscribe for yourself."
            )

        if Subscription.objects.filter(user=follower, author=author).exists():
            raise serializers.ValidationError(
                "You are already subscribed for this user."
            )

        return data

    def create(self, validated_data):
        follower = self.context['request'].user
        author = self.context['author']
        subscription = Subscription.objects.create(user=follower, author=author)
        return subscription

    def get_avatar(self, obj):
        author = obj.author
        if hasattr(author, 'avatar') and author.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(author.avatar.url)
            return author.avatar.url
        return None

    def get_recipes(self, obj):
        """Gets recipes."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.author.recipes.all()

        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass

        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Gets number of recipes."""
        return obj.author.recipes.count()

import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from users.models import UserDetail


class Ingredient(models.Model):
    """Model representing a recipe ingredient with name and measurement unit."""
    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=settings.INGREDIENTS_NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=settings.INGREDIENTS_MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Model representing recipe tags for categorization."""
    name = models.CharField(
        verbose_name='Название',
        max_length=settings.TAG_NAME_MAX_LENGTH
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг',
        max_length=settings.TAG_SLUG_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Model representing a cooking recipe with ingredients and preparation details."""
    author = models.ForeignKey(
        UserDetail,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=settings.RECIPE_NAME_MAX_LENGTH
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    text = models.TextField(verbose_name='Описание', max_length=settings.RECIPE_TEXT_MAX_LENGTH)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.IntegerField(
        validators=(
            MinValueValidator(settings.RECIPE_MIN_COOKING_TIME),
        ),
        verbose_name='Время приготовления в минутах'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Junction model linking recipes with ingredients and their quantities."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.FloatField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} ({self.amount} {self.ingredient.measurement_unit})'


class FavoriteRecipe(models.Model):
    """Model for tracking users' favorite recipes."""
    user = models.ForeignKey(
        UserDetail,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """Model for tracking recipes added to users' shopping carts."""
    user = models.ForeignKey(
        UserDetail,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShortLink(models.Model):
    """Model for storing shortened URLs for recipes."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_links',
        verbose_name='Рецепт'
    )
    token = models.CharField(
        max_length=settings.SHORTLINK_SIZE,
        unique=True,
        db_index=True,
        verbose_name='Токен'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        ordering = ('-created_at',)

    @classmethod
    def generate_token(cls):
        """Generate a unique token for the short link."""
        return uuid.uuid4().hex[:settings.SHORTLINK_SIZE]

    def get_absolute_url(self):
        """Return the complete URL for the short link."""
        return f'{settings.BASE_URL}/r/{self.token}/'

    def __str__(self):
        return f'Короткая ссылка на {self.recipe.name} ({self.token})'

import string
import random

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    """
    Model representing a recipe ingredient
    with name and measurement unit.
    """

    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=settings.INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'Ингредиент "{self.name}" ({self.measurement_unit})'


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
        return f'Тэг "{self.name}" (slug: {self.slug})'


class Recipe(models.Model):
    """
    Model representing a cooking recipe
    with ingredients and preparation details.
    """

    author = models.ForeignKey(
        User,
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
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                settings.RECIPE_MIN_COOKING_TIME,
                message='Время готовки не может быть менее '
                        f'{settings.RECIPE_MIN_COOKING_TIME} мин'
            ),
            MaxValueValidator(
                settings.RECIPE_MAX_COOKING_TIME,
                message='Время готовки не может быть более '
                        f'{settings.RECIPE_MAX_COOKING_TIME} мин'
            ),
        ),
        verbose_name='Время приготовления в минутах'
    )

    short_link_token = models.CharField(
        verbose_name='Токен короткой ссылки',
        max_length=settings.SHORTLINK_SIZE,
        unique=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'Рецепт "{self.name}" от {self.author.username}'

    def generate_short_link_token(self):
        """Generates a unique token for the short link."""
        chars = string.ascii_letters + string.digits
        return ''.join(
            random.choice(chars)
            for _ in range(settings.SHORTLINK_SIZE)
        )

    def save(self, *args, **kwargs):
        """Override save to generate short link token if it doesn't exist."""
        if not self.short_link_token:
            self.short_link_token = self.generate_short_link_token()

        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """
    Model linking recipes with
    ingredients and their quantities.
    """

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
    amount = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                settings.INGREDIENT_MIN_AMOUNT,
                message='Количество ингредиента не может быть меньше '
                        f'{settings.INGREDIENT_MIN_AMOUNT}'
            ),
            MaxValueValidator(
                settings.INGREDIENT_MAX_AMOUNT,
                message='Количество ингредиента не может быть больше '
                        f'{settings.INGREDIENT_MAX_AMOUNT}'
            ),
        )
    )

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
        return (f'{self.ingredient.name} ({self.amount} '
                f'{self.ingredient.measurement_unit}) '
                f'для "{self.recipe.name}"')


class FavoriteRecipe(models.Model):
    """Model for tracking users' favorite recipes."""

    user = models.ForeignKey(
        User,
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
        return f'Избранное: "{self.recipe.name}" для {self.user.username}'


class ShoppingCart(models.Model):
    """Model for tracking recipes added to users' shopping carts."""

    user = models.ForeignKey(
        User,
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
        return f'{self.user.username} добавил "{self.recipe.name}" в корзину'

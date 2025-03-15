from uuid import uuid4

from django.contrib import admin
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from app_products.filters.admin_filter import ProductCategoryFilterAdmin, \
    ProductManufacturerFilterAdmin, FeedbackUsernameFilterAdmin, \
    FeedbackProductFilterAdmin
from app_products.models import Product, Image, Manufacturer, ProductFeature, \
    Feedback
from app_categories.admin import TypeFeatureFieldMixin
from app_products.forms import FeatureFormset


class FeatureProductInline(TypeFeatureFieldMixin, admin.TabularInline):
    """Добавление характеристик для товаров"""
    model = ProductFeature
    fields = ['feature_fk', 'value', 'type_feature']
    readonly_fields = ['feature_fk', 'type_feature']
    formset = FeatureFormset

    def has_add_permission(self, request, obj) -> bool:
        """Возможность добавлять характеристики к товарам"""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Возможность удалять характеристики у товаров"""
        return False


class ImageProductInline(admin.TabularInline):
    model = Image
    fields = ['image']


class ListDisplayProductExtendMixin():
    """Миксин для расширения list_display"""
    list_select_related = ('category_fk', 'manufacturer_fk')
    list_display = ('name', 'price', 'added', 'count', 'category',
                    'manufacturer', 'is_limited')

    def get_queryset(self, request) -> QuerySet:
        queryset = super().get_queryset(request)\
            .select_related(*self.list_select_related)\
            .prefetch_related('image_set')
        return queryset

    @admin.display(description=_('category'))
    def category(self, obj) -> str:
        """Доп. поле отображения категория"""
        return obj.category_fk.name

    @admin.display(description=_('manufacturer'))
    def manufacturer(self, obj) -> str:
        """Доп. поле отображения производитель"""
        return obj.manufacturer_fk.name


@admin.register(Product)
class ProductAdmin(ListDisplayProductExtendMixin, admin.ModelAdmin):
    """Панель продуктов"""
    inlines = (FeatureProductInline, ImageProductInline)
    ordering = ('-added', )
    search_fields = ('name', )
    list_filter = (ProductCategoryFilterAdmin,
                   ProductManufacturerFilterAdmin,
                   'is_limited')

    def get_field_queryset(self, db, db_field, request) -> QuerySet:
        """Добавлять товары можно только в подкатегории"""
        queryset = super().get_field_queryset(db, db_field, request)

        if db_field == Product._meta.get_field('category_fk'):
            queryset = queryset.filter(level=1).order_by('parent')
        return queryset

    def save_model(self, request, obj, form, change) -> None:
        if not obj.product_id:
            obj.product_id = uuid4()

        if 'category_fk' in form.changed_data:
            obj.save(update_fields=form.changed_data)
        else:
            super().save_model(request, obj, form, change)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'user', 'product')
    search_fields = ('text', )
    list_filter = (FeedbackUsernameFilterAdmin, FeedbackProductFilterAdmin)
    list_select_related = ('user_fk', 'product_fk')
    ordering = ('-added',)

    @admin.display(description=_('text'))
    def short_text(self, obj) -> str:
        """Отображение текста отзыва"""
        return obj.text[:15]

    @admin.display(description=_('user'))
    def user(self, obj) -> str:
        """Доп. поле отображения пользователя"""
        return obj.user_fk.username

    @admin.display(description=_('product'))
    def product(self, obj) -> str:
        """Доп. поле отображения товара"""
        return obj.product_fk.name

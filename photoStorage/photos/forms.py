import base64

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from .models import Photo, Tag, Category, Album

from django import forms
from .models import User
from django.conf import settings


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('name', 'email', 'role')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

# class RegistrationForm(UserCreationForm):
#     class Meta(UserCreationForm.Meta):
#         model = User
#         fields = UserCreationForm.Meta.fields


# class PhotoForm(forms.ModelForm):
#     new_tag = forms.CharField(max_length=50, required=False, label='Добавить тег')
#     new_category = forms.CharField(max_length=100, required=False, label='Добавить категорию')
#
#     class Meta:
#         model = Photo
#         fields = ['title', 'description', 'date', 'id_category']
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#         }
class PhotoForm(forms.ModelForm):
    # Поля для выбора существующих категорий и тегов
    existing_category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Выбрать категорию'
    )
    existing_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        label='Выбрать теги',
        widget=forms.CheckboxSelectMultiple
    )

    # Поля для добавления новых категории и тега
    new_tag = forms.CharField(max_length=50, required=False, label='Добавить тег')
    new_category = forms.CharField(max_length=100, required=False, label='Добавить категорию')

    # Поле для загрузки изображения (не сохраняется напрямую в модель)
    upload_image = forms.ImageField(required=False, label='Загрузить изображение')

    class Meta:
        model = Photo
        fields = ['title', 'description', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Извлекаем user из kwargs, если передан
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        photo = super().save(commit=False)

        # ОБЯЗАТЕЛЬНО устанавливаем пользователя
        if self.user:
            photo.id_user = self.user

        # Обработка категории
        if self.cleaned_data['existing_category']:
            photo.id_category = self.cleaned_data['existing_category']
        elif self.cleaned_data['new_category']:
            category, created = Category.objects.get_or_create(
                name=self.cleaned_data['new_category'],
                defaults={'description': ''}
            )
            photo.id_category = category

        # Обрабатываем теги
        tags_to_add = []
        if self.cleaned_data['existing_tags']:
            tags_to_add.extend(self.cleaned_data['existing_tags'])
        if self.cleaned_data['new_tag']:
            tag, created = Tag.objects.get_or_create(name=self.cleaned_data['new_tag'])
            tags_to_add.append(tag)

        # Обработка изображения и сохранение в формате Base64 в поле image
        uploaded_image = self.cleaned_data.get('upload_image')
        if uploaded_image:
            try:
                image_data = uploaded_image.read()
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                photo.image = encoded_image  # Только строка Base64, без префикса
            except Exception as e:
                print(f"Ошибка кодирования изображения: {e}")
                photo.image = ''
        else:
            photo.image = ''

        if commit:
            photo.save()
            if tags_to_add:
                photo.tags.set(tags_to_add)

        return photo

# class AlbumCreateForm(forms.ModelForm):
#     photos = forms.ModelMultipleChoiceField(
#         queryset=Photo.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         required=False
#     )
#
#     class Meta:
#         model = Album
#         fields = ['name', 'description', 'photos']

class AlbumCreateForm(forms.ModelForm):
    photos = forms.ModelMultipleChoiceField(
        queryset=Photo.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'style': 'display:none;'}),
        required=False
    )

    class Meta:
        model = Album
        fields = ['name', 'description', 'photos']


class AlbumForm(forms.ModelForm):
    photos = forms.ModelMultipleChoiceField(
        queryset=Photo.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Album
        fields = ['name', 'description', 'photos']
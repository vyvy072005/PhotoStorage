import base64
import imghdr
import logging

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.checks import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm, PhotoForm
from .models import Category, Tag, User, PhotoTag, Photo, AlbumPhoto, Album
from django.conf import settings


# def home(request):
#     return render(request, 'photos//home.html')
@login_required
def home(request):
    # Фильтруем фотографии по текущему пользователю
    photos = Photo.objects.select_related(
        'id_category', 'id_user'
    ).filter(
        id_user=request.user  # Только фото текущего пользователя
    ).order_by('-date')

    # Обрабатываем каждую фотографию
    processed_photos = []
    for photo in photos:
        # Проверяем, есть ли изображение
        if photo.image:
            # Формируем Data URL
            data_url = f"data:image/jpeg;base64,{photo.image}"
        else:
            # Заглушка, если изображения нет
            data_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2RkZCIvPjx0ZXh0IHg9IjIwMCIgeT0iMTUwIiBmaWxsPSIjZmZmIiBmb250LWZhbWlseT0iQmV0aGVsb3YiIGZvbnQtc2l6ZT0iMjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiPm5vIGltYWdlPC90ZXh0Pjwvc3ZnPg=='

        processed_photos.append({
            'photo': photo,
            'image_url': data_url
        })

    context = {
        'processed_photos': processed_photos,
        'total_photos': len(processed_photos),  # Количество фото текущего пользователя
    }
    return render(request, 'photos/home.html', context)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # теперь работает корректно
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'photos/register.html', {'form': form})

# def register(request):
#     if request.method == 'POST':
#         form = RegistrationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             #group = Group.objects.get(name='user')
#             #user.groups.add(group)
#             return redirect('home')
#     else:
#         form = RegistrationForm()
#     return render(request, 'photos//register.html', {'form': form})



# @login_required
# def add_photo(request):
#     if request.method == 'POST':
#         form = PhotoForm(request.POST, request.FILES)
#         if form.is_valid():
#             # Получаем объект фото, но не сохраняем сразу (commit=False)
#             photo = form.save(commit=False)
#             # Устанавливаем текущего пользователя
#             photo.id_user = request.user
#
#             # Обработка новой категории
#             new_category_name = form.cleaned_data.get('new_category')
#             if new_category_name:
#                 category, created = Category.objects.get_or_create(
#                     name=new_category_name,
#                     defaults={'description': ''}
#                 )
#                 photo.id_category = category
#
#             # Обработка загруженного изображения и сохранение в формате Base64
#             if 'upload_image' in request.FILES:
#                 uploaded_image = request.FILES['upload_image']
#
#                 # Читаем данные изображения
#                 image_data = uploaded_image.read()
#
#                 # Кодируем в Base64 (правильный модуль — base64)
#                 encoded_image = base64.b64encode(image_data).decode('utf-8')
#
#                 # Сохраняем ТОЛЬКО строку Base64 в поле image (без префикса)
#                 photo.image = encoded_image
#             else:
#                 # Если изображение не загружено, сохраняем пустую строку в поле image
#                 photo.image = ''
#
#             # Сохраняем фото (включая Base64‑строку) в БД
#             photo.save()
#
#             # Сохраняем связи ManyToMany (теги)
#             form.save_m2m()
#
#             return redirect('home')
#     else:
#         form = PhotoForm()
#
#     return render(request, 'photos/add_photo.html', {'form': form})


@login_required
def add_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            photo = form.save(commit=True)  # Вся логика в форме
            return redirect('home')
    else:
        form = PhotoForm()
    return render(request, 'photos/add_photo.html', {'form': form})


def create_album(request):
    return 0




@login_required
def profile(request):
    """
    Отображение страницы профиля текущего пользователя
    """
    user = request.user

    context = {
        'user': user,
    }

    return render(request, 'photos//profile.html')


def edit_profile(request):
    return render(request, 'photos//edit_profile.html')


@require_http_methods(['GET'])
@login_required
def get_sorted_photos(request):
    sort_by = request.GET.get('sort', 'date')

    # Определяем поле сортировки
    sort_fields = {
        'date': '-date',
        'category': 'id_category__name',
        'tag': 'tags__name'
    }

    order_by = sort_fields.get(sort_by, '-date')

    # Для сортировки по альбомам нужно выполнить дополнительный запрос через AlbumPhoto
    if sort_by == 'album':
        # Получаем все альбомы текущего пользователя
        user_albums = Album.objects.filter(id_user=request.user)
        # Получаем фото, связанные с этими альбомами
        photos = Photo.objects.select_related(
            'id_category', 'id_user'
        ).filter(
            id_user=request.user
        ).prefetch_related(
            'tags'
        )
        # Сортируем вручную по названию альбома
        photo_list = list(photos)
        # Добавляем информацию об альбоме для каждой фото
        for photo in photo_list:
            # Получаем альбомы для фото через AlbumPhoto
            albums_for_photo = Album.objects.filter(
                id_album__in=AlbumPhoto.objects.filter(
                    id_photo=photo
        ).values_list('id_album', flat=True)
            )
            photo.album_names = ', '.join([a.name for a in albums_for_photo]) if albums_for_photo else 'не указан'
        # Сортируем по названию альбома (если есть)
        photo_list.sort(key=lambda x: x.album_names.lower())
    else:
        # Обычная сортировка по другим полям
        photos = Photo.objects.select_related(
            'id_category', 'id_user'
        ).filter(
            id_user=request.user
        ).order_by(order_by)[:100]
        photo_list = list(photos)

    processed_photos = []
    for photo in photo_list[:100]:  # Ограничиваем 100 фото
        if photo.image:
            data_url = f"data:image/jpeg;base64,{photo.image}"
        else:
            data_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2RkZCIvPjx0ZXh0IHg9IjIwMCIgeT0iMTUwIiBmaWxsPSIjZmZmIiBmb250LWZhbWlseT0iQmV0aGVsb3YiIGZvbnQtc2l6ZT0iMjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiPm5vIGltYWdlPC90ZXh0Pjwvc3ZnPg=='

        # Собираем теги для фото
        tags_list = ', '.join([tag.name for tag in photo.tags.all()]) if photo.tags.exists() else 'не указаны'

        processed_photos.append({
            'title': photo.title,
            'description': photo.description,
            'date': photo.date.strftime('%d.%m.%Y'),
            'image_url': data_url,
            'category_name': photo.id_category.name if photo.id_category else 'не указана',
            'username': photo.id_user.name,  # Используем name вместо username
            'album_names': getattr(photo, 'album_names', 'не указан'),
            'tags_list': tags_list
        })

    return JsonResponse({'photos': processed_photos})

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(['POST'])
@login_required
def edit_photo(request):
    try:
        # Получаем ID фото ДО любых операций с данными
        photo_id = request.POST.get('photo_id')
        if not photo_id:
            return JsonResponse({'success': False, 'error': 'ID фото не указан'}, status=400)

        user_id = request.user.pk
        logger.info(f'Попытка редактирования фото {photo_id} пользователем {user_id}')

        # Получаем остальные данные
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category_id')

        # Находим фотографию пользователя
        try:
            photo = Photo.objects.get(id_photo=photo_id, id_user=request.user)
        except Photo.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Фото не найдено или у вас нет прав на его редактирование'
            }, status=404)

        # Валидация обязательных полей
        if not title:
            return JsonResponse({'success': False, 'error': 'Название фотографии обязательно'}, status=400)

        # Обновляем поля
        photo.title = title
        photo.description = description if description else None

        # Обрабатываем категорию
        if category_id:
            try:
                category = Category.objects.get(id_category=category_id)
                photo.id_category = category
            except Category.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Указанная категория не существует'}, status=400)
        else:
            photo.id_category = None

        # Обрабатываем новое изображение, если загружено
        new_image = request.FILES.get('image')
        base64_data = None  # Инициализируем переменную

        if new_image:
            # Проверяем размер файла (до 5 МБ)
            if new_image.size > 5 * 1024 * 1024:  # 5 МБ
                return JsonResponse({'success': False, 'error': 'Файл слишком большой (максимум 5 МБ)'}, status=400)

            # Читаем файл и конвертируем в base64
            image_data = new_image.read()
            try:
                # Определяем MIME‑тип по сигнатуре
                mime_type = imghdr.what(None, image_data)
                if not mime_type:
                    return JsonResponse({'success': False, 'error': 'Неподдерживаемый формат изображения'}, status=400)
                if mime_type == 'jpeg':
                    mime_type = 'jpg'  # Нормализуем

                base64_data = base64.b64encode(image_data).decode('utf-8')
                # Добавляем префикс для корректного отображения
                photo.image = f'data:image/{mime_type};base64,{base64_data}'
                logger.info(f'Изображение успешно закодировано (тип: {mime_type})')
            except Exception as e:
                logger.error(f'Ошибка кодирования изображения в base64: {e}')
                return JsonResponse({'success': False, 'error': 'Ошибка обработки изображения'}, status=400)

        # Сохраняем изменения с обработкой ошибок БД
        try:
            photo.save()
        except Exception as save_error:
            logger.error(f'Ошибка сохранения фото {photo_id} в БД: {save_error}')
            return JsonResponse({'success': False, 'error': 'Ошибка сохранения данных в базе'}, status=500)

        logger.info(f'Фото {photo_id} успешно обновлено пользователем {user_id}')

        return JsonResponse({
            'success': True,
            'photo': {
                'id_photo': photo.id_photo,
                'title': photo.title,
                'description': photo.description or 'Без описания',
                'category_name': photo.id_category.name if photo.id_category else 'не указана',
                # Возвращаем base64 для обновления UI (без префикса)
                'image_base64': base64_data if new_image else (
                    photo.image.split(',')[1] if photo.image and ',' in photo.image else None
                )
            }
        })

    except ValidationError as e:
        logger.error(f'Валидация данных не пройдена: {e}')
        return JsonResponse({'success': False, 'error': f'Ошибка валидации: {str(e)}'}, status=400)
    except Exception as e:
        user_id = getattr(request.user, 'pk', 'unknown')
        logger.exception(f'Неожиданная ошибка при редактировании фото {photo_id} пользователем {user_id}: {e}')
        return JsonResponse({'success': False, 'error': 'Внутренняя ошибка сервера'}, status=500)

@require_http_methods(['DELETE'])
@login_required
def delete_photo(request, photo_id):
    try:
        photo = get_object_or_404(Photo, id_photo=photo_id, id_user=request.user)
        photo.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
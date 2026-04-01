from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='photos/login.html'), name='login'),
    path('home/', views.home, name='home'),  # страница после входа
    path('logout/', auth_views.LogoutView.as_view(template_name='photos/logout.html'), name='logout'),

    path('register/', views.register, name='register'),
    path('add-photo/', views.add_photo, name='add_photo'),
    path('create-album/', views.create_album, name='create_album'),
    path('add-photo/', views.add_photo, name='add_photo'),
    path('profile/', views.profile, name='profile'),  # Страница личного кабинета
    path('edit_profile/', views.edit_profile, name='edit_profile'),  # Страница личного кабинета
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/photos/sorted/', views.get_sorted_photos, name='get_sorted_photos'),
    path('api/photos/sorted/', views.get_sorted_photos, name='get_sorted_photos'),
    path('api/photos/edit/', views.edit_photo, name='edit_photo'),
    path('api/photos/delete/<int:photo_id>/', views.delete_photo, name='delete_photo'),

]
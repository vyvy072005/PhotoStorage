from django.db import models


from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


from django.conf import settings
from django.contrib.auth.hashers import make_password



class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, **extra_fields)

class User(AbstractBaseUser):
    id_user = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(
        max_length=255,
        default=make_password('default_temporary_password')  # Хешированный временный пароль
    )
    role = models.CharField(max_length=50, default='user')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

# class User(models.Model):
#     id_user = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=100)
#     email = models.EmailField(unique=True)
#     pass_hash = models.CharField(max_length=255)
#     role = models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.name


class Category(models.Model):
    id_category = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Tag(models.Model):
    id_tag = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Album(models.Model):
    id_album = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='albums')

    def __str__(self):
        return self.name


class Photo(models.Model):
    id_photo = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    image = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True)  # Добавьте это поле
    id_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True
    )
    id_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='photos'
    )

    def __str__(self):
        return self.title
# class Photo(models.Model):
#     id_photo = models.AutoField(primary_key=True)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     date = models.DateField()
#     id_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
#     id_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
#
#     def __str__(self):
#         return self.title

class PhotoTag(models.Model):
    id_photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    id_tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('id_photo', 'id_tag')

class AlbumPhoto(models.Model):
    id_album = models.ForeignKey(Album, on_delete=models.CASCADE)
    id_photo = models.ForeignKey(Photo, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('id_album', 'id_photo')
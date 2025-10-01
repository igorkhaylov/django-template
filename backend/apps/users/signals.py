from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_rosetta_group(sender, **kwargs):
    if sender.name != "django.contrib.admin":
        return
    # Создаем группу для Rosetta
    rosetta_group, created = Group.objects.get_or_create(name="Rosetta Users")
    # Получаем разрешение для изменения сообщений
    content_type = ContentType.objects.get_for_model(Permission)
    permission, created = Permission.objects.get_or_create(
        codename="can_change_rosetta_messages",
        name="Can change rosetta messages",
        content_type=content_type,
    )
    # Добавляем разрешение к группе
    rosetta_group.permissions.add(permission)

    if created:
        print("✅ Группа 'Rosetta Users' создана и настроена")
    else:
        print("ℹ️ Группа 'Rosetta Users' уже существует")

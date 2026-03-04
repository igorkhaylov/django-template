import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('expires_at', models.DateTimeField(verbose_name='expires at')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created at')),
                ('user_email', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='verification_tokens',
                    to='users.useremail',
                    verbose_name='user email',
                )),
            ],
            options={
                'verbose_name': 'Email verification token',
                'verbose_name_plural': 'Email verification tokens',
            },
        ),
    ]

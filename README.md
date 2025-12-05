# Django Template

##### show directory structure
```bash
tree -I __pycache__ -I .git -a
# or
tree --gitignore -I .git -a # Filter by using .gitignore files
# options
# -f            Print the full path prefix for each file.
# -L level      Descend only level directories deep
# -J            Prints out an JSON representation of the tree
# -I pattern    Do not list files that match the given pattern.
```

```bash
# Create project in current directory
django-admin startproject config .
```


# Poetry
```bash
poetry init
poetry show --tree
poetry show -T
poetry add django psycopg[binary]
poetry add --group dev pytest django-debug-toolbar
poetry install --no-root --only main
poetry install --no-root --with dev
```


# Django management commands
```bash
# create new app
cd apps
python ../manage.py startapp new_app
```


# generate locales
```bash
python manage.py makemessages -l ru -l en --ignore venv
# compile locales
python manage.py compilemessages
```

# update translation fields
```bash
# populate translation fields if field*_ru not exist in model
python manage.py update_translation_fields
```


# generate random hex key
```bash
# generate random hex key with length 64 (can be changed)
openssl rand -hex 64
```


##### При создании из шаблона нужно заменить:

###### ./docker-compose.yml
- change docker compose name
- change nginx service ports for django and minio

###### ./.env.example
- change port in MINIO_ENDPOINT
- change port in DJANGO_CSRF_TRUSTED_ORIGINS
- other changes for security

###### ./.devcontainer/backend/devcontainer.json
- change name and add port

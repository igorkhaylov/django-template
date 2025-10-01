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

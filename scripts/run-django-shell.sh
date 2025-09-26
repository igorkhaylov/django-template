# Load environments from ../.env
set -a
source "$(dirname "$0")/../.env"
set +a

docker compose exec -it backend python manage.py shell -v 2

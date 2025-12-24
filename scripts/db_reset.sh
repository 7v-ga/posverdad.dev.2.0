docker compose down -v
docker compose up -d db

until docker exec posverdad-db-1 pg_isready -U posverdad -d posverdad; do
  sleep 1
done

alembic upgrade head
alembic current

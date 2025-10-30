## Contexto
Simplificar setup local y preparar futuro despliegue.

## Objetivo
Docker Compose para FE, API, DB, Redis. Manifiestos K8s opcionales.

## Cambios incluidos
- `docker-compose.yml` con servicios `frontend`, `api`, `db`, `redis`
- `.env`/`.env.example` variables mínimas
- (Opcional) `/k8s` con manifests base (Deployment/Service)

## Acceptance Criteria
- `docker compose up` levanta stack local
- README con instrucciones

## Follow-ups
- CI/CD docker build/push

Closes #26

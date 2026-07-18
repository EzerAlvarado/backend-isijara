# Backend — Sistema ISIJARA

API REST con Django 5 + Django REST Framework.

## Requisitos

- Python 3.11+
- Entorno virtual (recomendado)

## Instalación

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # si aún no tienes .env
python manage.py migrate
python manage.py createsuperuser   # opcional, para /admin
python manage.py runserver
```

El servidor queda en `http://localhost:8000`.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health/` | Estado del servicio |
| CRUD | `/api/prendas/` | Inventario |
| CRUD | `/api/rentas/` | Rentas (`?semana_inicio=2025-06-22`) |
| Filtros | query params | Ver sección **Filtros** abajo |
| CRUD | `/api/devoluciones/` | Devoluciones |
| CRUD | `/api/transacciones/` | Corte / finanzas |

Panel de administración: `http://localhost:8000/admin/`

## Filtros (query params)

| Recurso | Ejemplos |
|---------|----------|
| Prendas | `?talla=M&estatus=disponible&codigo=129&search=negro` |
| Rentas | `?semana_inicio=2025-06-22&tipo_entrega=premier&estatus_fila=salio` |
| Devoluciones | `?estatus=retrasado&cliente=carlos&fecha_limite_desde=2025-06-01` |
| Transacciones | `?pago=Efectivo&timestamp_desde=2025-06-01T00:00:00` |

## Frontend

El proxy de Vite (`frontend/vite.config.ts`) redirige `/api` → `http://localhost:8000`.

# Backend (Django + DRF)

## Requisitos

- Python 3.13+

## Instalar dependencias

```powershell
cd backend
pip install -r requirements.txt
```

## Rodar migracoes e servidor

```powershell
python manage.py migrate
python manage.py runserver
```

## Endpoints iniciais

- `GET /api/health/` -> healthcheck da API
- `GET /admin/` -> painel admin do Django
- `POST /api/auth/register/` -> cria usuario e retorna token
- `POST /api/auth/login/` -> autentica e retorna token
- `GET /api/auth/me/` -> retorna usuario autenticado (`Authorization: Token <token>`)
- `POST /api/auth/logout/` -> invalida token atual

## Exemplo de integracao com Next (fetch)

```ts
const response = await fetch("http://127.0.0.1:8000/api/auth/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});

const data = await response.json();
// data.token -> salve no estado/localStorage/cookie (conforme sua estrategia)
```

## Observacao sobre CORS

O projeto ja esta preparado para `django-cors-headers`. Se o pacote nao estiver instalado, a API continua subindo sem CORS.

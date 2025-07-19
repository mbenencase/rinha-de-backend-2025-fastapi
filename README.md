# Rinha de Backend 2025

Código da terceira edição da rinha de backend disponível [aqui](https://github.com/zanfranceschi/rinha-de-backend-2025/tree/main).

## Tecnologias

- FastAPI
- Redis
- PostgreSQL
- NGINX

## Como Utilizar

### Dev Local - Instalando as Dependências

Eu gosto de utilizar o [uv](https://docs.astral.sh/uv/getting-started/installation/).

Se você tiver o [uv](https://docs.astral.sh/uv/getting-started/installation/), basta apenas rodar:

```
uv sync
```

e ativar o virutal env. Caso contrário, pode usar o `requirements.txt` com:

```
pip3 install -r requirements.txt
```

### Docker Compose

Para executar o que subi no meu Docker Hub, basta:
```
make up
```

Para derrubar os contâineres:
```
make down
```
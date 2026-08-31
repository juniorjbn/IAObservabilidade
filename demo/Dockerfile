FROM python:3.12-slim

# Uma imagem só para os quatro processos. Numa demo que roda em notebook de
# 16GB, cada camada duplicada é RAM e tempo de build que você não tem.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY demo/requirements.txt /app/demo/requirements.txt
RUN pip install --no-cache-dir -r /app/demo/requirements.txt

COPY demo /app/demo

CMD ["python", "-c", "print('informe um command no compose')"]

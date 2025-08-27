FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências básicas
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos
COPY . .

# Instala as dependências
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Cria pasta de uploads se não existir
RUN mkdir -p /app/uploads

# Comando padrão
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "4", "--timeout", "120", "run:app"]

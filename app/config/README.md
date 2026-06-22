## database.py

1.Instalar dependencias (psycopg[binary], psycopg-pool y pgvector)

    pip install "psycopg[binary]" psycopg-pool pgvector

2.Y luego, agregarlas al requirements.txt

    pip freeze | grep -E "psycopg|pgvector" >> requirements.txt


## ollama.py

1.Instalar dependencia

    pip install langchain-ollama


## settings.py

1.Instalar dependencia
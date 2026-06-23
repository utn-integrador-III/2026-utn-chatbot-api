## database.py

1.Install dependences (psycopg[binary], psycopg-pool y pgvector)

    pip install "psycopg[binary]" psycopg-pool pgvector

2.Y luego, agregarlas al requirements.txt

    pip freeze | grep -E "psycopg|pgvector" >> requirements.txt


## ollama.py

1.Install dependence

    pip install langchain-ollama

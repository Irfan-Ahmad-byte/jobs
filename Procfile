web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
worker: gunicorn -w 1 -k uvicorn.workers.UvicornWorker proxies_worker:app

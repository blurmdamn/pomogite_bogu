# pomogite_bogu
 uvicorn src.main:app --reload
 rm -rf alembic/versions/*    
 alembic upgrade head       
 alembic revision --autogenerate -m "Initial migration"


git add .

git commit -m "Commit"

 git push origin master


celery -A src.celery.worker.celery_app worker --loglevel=info


celery -A src.celery.worker call src.tasks.parsers.run_gog_parser #для задач


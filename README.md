# pomogite_bogu
 uvicorn src.main:app --reload
 rm -rf alembic/versions/*    
 alembic upgrade head       
 alembic revision --autogenerate -m "Initial migration"


git add .

git commit -m "Commit"

 git push origin master

# Crypto & Stocks Tracker 🏛️

In this app users are able to create thresholds and subscribe to them, when crypto currency or stock is going to be less or greater than users's value, and user will get an email notification about his tresholds, when crypto currency or stock will reach a certain value <br> 

Also users can check price of crypto currencies and stocks in real time.

## Tech Stack 💻

| Backend core | Database Managing | Background tasks | 
| ----------- | ----------- | ----- |
| ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)      | ![Postgres](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)       | ![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white) |
| ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)   | ![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)        | ![Celery](https://img.shields.io/badge/Celery-b6de64?style=for-the-badge&logo=celery&logoColor=white&color) |

## Additional tools that I used 🛠️
 * <div style="display: flex; algin-items: center"><img src="https://img.shields.io/badge/alembic-95a5a6?style=for-the-badge&logoColor=white"> - To apply changes(migrations) to my database</div>
* <div style="display: flex; align-items: center"><img src="https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens"> - Authentication, Authorization</div>
* <div style="display: flex; align-items: center;"><img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white"> - Database hosting</div>
* <div style="display: flex; align-items: center;"><img src="https://img.shields.io/badge/docker-257bd6?style=for-the-badge&logo=docker&logoColor=white"> - Application containerization</div>

## Additional APIs 🌐
* CoinGeckoAPI - to get the latest information about cryptocurrencies
* AlphaVantageAPI - to get the information about stocks

## Project setup 
#### Repository copying
```
git clone https://github.com/sdeffff/crypto_stocks_portfolio.git
```

Change directory to copied repo: ```cd crypto_stocks_portfolio``` <br>
#### Install all of dependecies
```
pip install -r requirements.txt
```
#### Then start redis by writing `redis-server` in terminal or wsl <br>
#### And run server itself
```
uvicorn src.main:app --reload
```
#### Run also celery worker and celery beat
```
celery -A src.celery_worker worker --pool=solo -l info
celery -A src.celery_worker beat --loglevel=info
```

After this, application will be accessible on: `http://localhost:8000` <br>
And you will be able to find information about endpoints on `http://localhost:8000/docs`

#### And thats it, happy using 🚀

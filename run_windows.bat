@echo off
title Criminal Record Intelligence API
cd /d "%~dp0"
if not exist venv (
    py -3.13 -m venv venv
)
call venv\Scripts\activate
set DJANGO_DEBUG=true
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
pause

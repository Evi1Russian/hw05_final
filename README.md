## Описание проекта Yatube<br>

Yatube - это мини блог  реализованный на Django<br> в котором есть функция создания учётной записи, подписок на авторов и оставления комментариев к записям.<br>
Также есть админка и возможность модерации. В целом этот сайт представляет собой ленту с постами зарегистрированных пользователей, и возможность простматривать ленту подписок. Всё это реализованно с помощью базы данных Django ORM

### Установка
Клонировать репозиторий:
```bash
git clone git@github.com:Evi1Russian/hw05_final.git
```
Перейти в папку с проектом:
```bash
cd hw05_final/
```
Установить виртуальное окружение для проекта:
```bash
python -m venv venv
```
Активировать виртуальное окружение для проекта:

для OS Lunix и MacOS
```bash
source venv/bin/activate
```
для OS Windows
```bash
source venv/Scripts/activate
```
Установить зависимости:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
Выполнить миграции на уровне проекта:
```bash
cd yatube
python3 manage.py makemigrations
python3 manage.py migrate
```
Запустить проект локально:
```bash
python3 manage.py runserver
```
адрес запущенного проекта
http://127.0.0.1:8000
Зарегистирировать суперпользователя Django:
```bash
python3 manage.py createsuperuser
```
адрес панели администратора
http://127.0.0.1:8000/admin

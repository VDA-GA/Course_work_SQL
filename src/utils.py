import json
import time
from typing import Any

import psycopg2
import requests


def get_top_employers(key_word) -> list[dict[str, Any]]:
    """Получает список словарей работадателей с количеством объявлений больше 3
    :param key_word - слово для поиска вакансий
    :return список словарей с id, названием компании, url"""
    list_vacancies = []
    list_employers = []
    dict_employers = {}
    for i in range(0, 20):
        params = {"key_word": key_word, "area": 113, "page": i,
                  "per_page": 100}  # "area": 113 = поиск по России
        try:
            req = requests.get("https://api.hh.ru/vacancies", params)
            data = req.content.decode()
            req.close()
            list_vacancies.extend(json.loads(data)['items'])
        except requests.exceptions.ConnectionError:
            list_vacancies = []
            print("Connection Error. Please check your network connection.")
    for vacancy in list_vacancies:
        try:
            list_employers.append(vacancy['employer']['id'])
            dict_employers[vacancy['employer']['id']] = (vacancy['employer']['name'], vacancy['employer']['url'])
        except KeyError:
            continue
    list_top_employers = list(set([i for i in list_employers if list_employers.count(i) > 3]))
    employers_data = [{'id': k, 'name': dict_employers[k][0], 'url': dict_employers[k][1]} for k in list_top_employers]
    return employers_data


def get_vacancies_by_employer(employers_data: list) -> list[dict[str, Any]]:
    """Получает список данных по вакансиям работадателей из списка, для которых количество объявлений больше 3
    :param employers_data данные работадателей
    :return список словарей по каждой вакансии"""

    list_vacancies = []
    vacancy_data = []

    for employer in employers_data:
        time.sleep(10)
        for i in range(0, 10):
            params = {"employer_id": employer['id'], "page": i, "per_page": 100}
            try:
                req = requests.get("https://api.hh.ru/vacancies", params)
                data = req.content.decode()
                req.close()
                list_vacancies.extend(json.loads(data)['items'])
            except requests.exceptions.ConnectionError:
                list_vacancies = []
                print("Connection Error. Please check your network connection.")
    for vacancy in list_vacancies:
        if vacancy['salary']:
            if vacancy['salary']['from'] and not vacancy['salary']['to']:
                vacancy_data.append({'vacancy_id': int(vacancy['id']), 'employer_id': int(vacancy['employer']['id']),
                                     'vacancy_name': vacancy['name'], 'vacancy_url': vacancy['alternate_url'],
                                     'city': vacancy['area']['name'],
                                     'date': vacancy['created_at'], 'schedule': vacancy['schedule']['name'],
                                     'salary_from': vacancy['salary']['from'], 'salary_to': vacancy['salary']['from']})
            elif not vacancy['salary']['from'] and vacancy['salary']['to']:
                vacancy_data.append({'vacancy_id': int(vacancy['id']), 'employer_id': int(vacancy['employer']['id']),
                                     'vacancy_name': vacancy['name'], 'vacancy_url': vacancy['alternate_url'],
                                     'city': vacancy['area']['name'],
                                     'date': vacancy['created_at'], 'schedule': vacancy['schedule']['name'],
                                     'salary_from': vacancy['salary']['to'], 'salary_to': vacancy['salary']['to']})
            elif vacancy['salary']['from'] and vacancy['salary']['to']:
                vacancy_data.append({'vacancy_id': int(vacancy['id']), 'employer_id': int(vacancy['employer']['id']),
                                     'vacancy_name': vacancy['name'], 'vacancy_url': vacancy['alternate_url'],
                                     'city': vacancy['area']['name'],
                                     'date': vacancy['created_at'], 'schedule': vacancy['schedule']['name'],
                                     'salary_from': vacancy['salary']['from'], 'salary_to': vacancy['salary']['to']})

        else:
            vacancy_data.append({'vacancy_id': int(vacancy['id']), 'employer_id': int(vacancy['employer']['id']),
                                 'vacancy_name': vacancy['name'], 'vacancy_url': vacancy['alternate_url'],
                                 'city': vacancy['area']['name'],
                                 'date': vacancy['created_at'], 'schedule': vacancy['schedule']['name'],
                                 'salary_from': None, 'salary_to': None})
    return vacancy_data


def create_database(database_name: str, params: dict) -> None:
    """Создание базы данных и таблиц для сохранения данных о вакансиях и работодателей."""

    conn = psycopg2.connect(dbname='postgres', **params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {database_name}")
    cur.execute(f"CREATE DATABASE {database_name}")

    cur.close()
    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        cur.execute("""
                CREATE TABLE employers (
                    employer_id SERIAL PRIMARY KEY,
                    employer_name VARCHAR(300) NOT NULL,
                    employer_url VARCHAR(100)
                )
            """)

    with conn.cursor() as cur:
        cur.execute("""
                CREATE TABLE vacancies (
                    vacancy_id SERIAL PRIMARY KEY,
                    employer_id INT REFERENCES employers(employer_id),
                    vacancy_name TEXT NOT NULL,
                    vacancy_url VARCHAR(100),
                    city VARCHAR(100),
                    publish_date DATE,
                    schedule VARCHAR(100),
                    salary_from INT NULL DEFAULT NULL,
                    salary_to INT NULL DEFAULT NULL
                )
            """)
    conn.commit()
    conn.close()


def save_data_to_database(employers_data: list[dict[str, Any]], vacancy_data: list[dict[str, Any]], database_name: str,
                          params: dict) -> None:
    """Сохранение данных о вакансиях и работодателях в базу данных.
    :param employers_data - данные по работадателям
    :param vacancy_data - данные по вакансиям
    :param database_name - имя базы данных
    :param params - параметры для входа в базу данных"""
    conn = psycopg2.connect(dbname=database_name, **params)
    with conn.cursor() as cur:
        for employer in employers_data:
            cur.execute("INSERT INTO employers VALUES (%s, %s, %s)",
                        (int(employer['id']), employer['name'], employer['url']))
        cur.execute("SELECT * FROM employers")
        conn.commit()
        for vacancy in vacancy_data:
            cur.execute(
                "INSERT INTO vacancies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (vacancy['vacancy_id'], vacancy['employer_id'], vacancy['vacancy_name'],
                 vacancy['vacancy_url'], vacancy['city'], vacancy['date'],
                 vacancy['schedule'], vacancy['salary_from'], vacancy['salary_to']))
        cur.execute("SELECT * FROM vacancies")
        conn.commit()

    conn.close()

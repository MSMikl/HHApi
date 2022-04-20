import os

import requests

from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(vacancy):
    salary = vacancy['salary']
    if salary['currency'] != 'RUR':
        return None
    if not salary['from'] and not salary['to']:
        return None
    if not salary['from']:
        return salary['to']*0.8
    if not salary['to']:
        return salary['from']*1.2
    return (salary['from'] + salary['to'])/2


def head_hunter_vacancies(languages):
    vacancies = {}
    for lang in languages:
        vacancies[lang] = {}
        payload = {
            'text': lang,
            'area': '1',
            'period': '30',
            'only_with_salary': 'true',
            'per_page': '50'
        }
        response = requests.get(
            'https://api.hh.ru/vacancies',
            params=payload
        ).json()
        vacancies[lang]['vacancies_found'] = response['found']
        non_zero_count = 0
        total_salary = 0
        for page in range(0, min(response['pages'], 40)):
            payload.update(page=page)
            try:
                page_response = requests.get(
                    'https://api.hh.ru/vacancies',
                    params=payload
                ).json()
            except requests.exceptions.ConnectionError:
                continue
            for vacancy in page_response['items']:
                salary = predict_rub_salary(vacancy)
                if not salary:
                    continue
                total_salary += salary
                non_zero_count += 1
        vacancies[lang]['vacancies_processed'] = non_zero_count
        vacancies[lang]['average_salary'] = int(total_salary/non_zero_count)
    return vacancies


def predict_rub_salary_for_superJob(vacancy):
    if not vacancy['payment_from'] and not vacancy['payment_to']:
        return None
    if not vacancy['payment_from']:
        return vacancy['payment_to']*0.8
    if not vacancy['payment_to']:
        return vacancy['payment_from']*1.2
    return (vacancy['payment_from'] + vacancy['payment_to'])/2


def superjob_vacancies(languages):
    load_dotenv()
    api_key = os.getenv('SUPER_JOB_KEY')
    headers = {
        'X-Api-App-Id': api_key
        }
    vacancies = {}
    for lang in languages:
        vacancies[lang] = {}
        params = {
            'keyword': lang,
            'town': 4,
            'catalogues': 48,
            'no_agreement': 1,
            'count': 50
        }
        response = requests.get(
            'https://api.superjob.ru/2.0/vacancies/',
            headers=headers,
            params=params
        ).json()
        vacancies[lang]['vacancies_found'] = response['total']
        non_zero_count = 0.0001
        total_salary = 0
        for page in range(0, vacancies[lang]['vacancies_found']//50 + 1):
            params.update(page=page)
            try:
                page_response = requests.get(
                    'https://api.superjob.ru/2.0/vacancies/',
                    headers=headers,
                    params=params
                ).json()
            except requests.exceptions.ConnectionError:
                continue
            for vacancy in page_response['objects']:
                salary = predict_rub_salary_for_superJob(vacancy)
                if not salary:
                    continue
                total_salary += salary
                non_zero_count += 1
        vacancies[lang]['vacancies_processed'] = int(non_zero_count)
        vacancies[lang]['average_salary'] = int(total_salary/non_zero_count)
    return vacancies


def tableprint(vacancies, header=''):
    tabledata = [
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
    ]
    for lang in vacancies:
        tabledata.append(
            [
                lang, vacancies[lang]['vacancies_found'],
                vacancies[lang]['vacancies_processed'],
                vacancies[lang]['average_salary']
            ]
        )
    table = AsciiTable(tabledata)
    table.title = header
    print(table.table)


if __name__ == '__main__':
    languages = [
        'Python',
        'Java',
        'Javascript',
        'C++',
        'Pascal'
    ]

    tableprint(superjob_vacancies(languages), 'SuperJobMoscow')
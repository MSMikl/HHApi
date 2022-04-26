import argparse
import os
import traceback

import requests

from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(
    salary_from=None,
    salary_to=None,
    salary_currency='RUR'
):
    if salary_currency != 'RUR':
        return None
    if salary_from and salary_to:
        return (salary_from + salary_to)/2
    if salary_from:
        return salary_from*1.2
    if salary_to:
        return salary_to*0.8
    return None


def get_hh_vacancies(language):
    vacancies = {}
    params = {
        'text': language,
        'area': '1',
        'period': '30',
        'only_with_salary': 'true',
        'per_page': '50'
    }
    response = requests.get(
        'https://api.hh.ru/vacancies',
        params=params
    )
    response.raise_for_status()
    page1 = response.json()
    vacancies['vacancies_found'] = page1['found']
    non_zero_count = 0.0001
    total_salary = 0
    for page in range(0, min(page1['pages'], 40)):
        params['page'] = page
        page_response = requests.get(
            'https://api.hh.ru/vacancies',
            params=params
        )
        page_response.raise_for_status()
        for vacancy in page_response.json()['items']:
            salary = predict_rub_salary(
                salary_from=vacancy['salary']['from'],
                salary_to=vacancy['salary']['to'],
                salary_currency=vacancy['salary']['currency']
            )
            if not salary:
                continue
            total_salary += salary
            non_zero_count += 1
        vacancies['vacancies_processed'] = int(non_zero_count)
        vacancies['average_salary'] = int(total_salary/non_zero_count)
    return vacancies


def get_superjob_vacancies(language, api_key):
    headers = {
        'X-Api-App-Id': api_key
        }
    vacancies = {}
    params = {
        'keyword': language,
        'town': 4,
        'catalogues': 48,
        'no_agreement': 1,
        'count': 50
    }
    response = requests.get(
        'https://api.superjob.ru/2.0/vacancies/',
        headers=headers,
        params=params
    )
    response.raise_for_status()
    vacancies['vacancies_found'] = response.json()['total']
    non_zero_count = 0.0001
    total_salary = 0
    for page in range(0, vacancies['vacancies_found']//50 + 1):
        params['page'] = page
        page_response = requests.get(
            'https://api.superjob.ru/2.0/vacancies/',
            headers=headers,
            params=params
        )
        page_response.raise_for_status()
        for vacancy in page_response.json()['objects']:
            salary = predict_rub_salary(
                salary_from=vacancy['payment_from'],
                salary_to=vacancy['payment_to']
            )
            if not salary:
                continue
            total_salary += salary
            non_zero_count += 1
        vacancies['vacancies_processed'] = int(non_zero_count)
        vacancies['average_salary'] = int(total_salary/non_zero_count)
    return vacancies


def print_table(tabledata, header=''):
    tabledata = [
        [
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        ]
    ] + tabledata
    table = AsciiTable(tabledata)
    table.title = header
    print(table.table)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s',
        action='store_true',
        help='Get vacancies from SuberJob'
    )
    parser.add_argument(
        '-H',
        action='store_true',
        help='Get vacancies from HeadHunter'
    )
    parser.add_argument(
        'langs',
        nargs='*',
        help='Enter keywords for search'
    )
    args = parser.parse_args()
    superjob, headhunter, languages = args.s, args.H, args.langs

    if superjob:
        load_dotenv()
        api_key = os.getenv('SUPER_JOB_KEY')
        tabledata = []
        for lang in languages:
            try:
                vacancies = get_superjob_vacancies(lang, api_key)
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
                traceback.print_exc()
                continue
            except:
                raise
            tabledata.append(
                [
                    lang,
                    vacancies['vacancies_found'],
                    vacancies['vacancies_processed'],
                    vacancies['average_salary']
                ]
            )
        print_table(tabledata, 'SuperJobMoscow')

    if headhunter:
        tabledata = []
        for lang in languages:
            try:
                vacancies = get_hh_vacancies(lang)
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
                traceback.print_exc()
                continue
            except:
                raise
            tabledata.append(
                [
                    lang,
                    vacancies['vacancies_found'],
                    vacancies['vacancies_processed'],
                    vacancies['average_salary']
                ]
            )
        print_table(tabledata, 'HeadHunterMoscow')

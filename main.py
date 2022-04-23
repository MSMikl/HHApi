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
    if not salary_from and not salary_to:
        return None
    if not salary_from:
        return salary_to*0.8
    if not salary_to:
        return salary_from*1.2
    return (salary_from + salary_to)/2


def head_hunter_vacancies(language):
    vacancies = {}
    payload = {
        'text': language,
        'area': '1',
        'period': '30',
        'only_with_salary': 'true',
        'per_page': '50'
    }
    try:
        response = requests.get(
            'https://api.hh.ru/vacancies',
            params=payload
        )
        response.raise_for_status()
    except:
        raise
    page1 = response.json()
    vacancies['vacancies_found'] = page1['found']
    non_zero_count = 0
    total_salary = 0
    for page in range(0, min(page1['pages'], 40)):
        payload.update(page=page)
        try:
            page_response = requests.get(
                'https://api.hh.ru/vacancies',
                params=payload
            )
            page_response.raise_for_status()
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.HTTPError:
            raise
        except:
            raise
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
        vacancies['vacancies_processed'] = non_zero_count
        vacancies['average_salary'] = int(total_salary/non_zero_count)
    return vacancies


def superjob_vacancies(language, api_key):
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
    try:
        response = requests.get(
            'https://api.superjob.ru/2.0/vacancies/',
            headers=headers,
            params=params
        )
        response.raise_for_status()
    except:
        raise
    vacancies['vacancies_found'] = response.json()['total']
    non_zero_count = 0.0001
    total_salary = 0
    for page in range(0, vacancies['vacancies_found']//50 + 1):
        params.update(page=page)
        try:
            page_response = requests.get(
                'https://api.superjob.ru/2.0/vacancies/',
                headers=headers,
                params=params
            )
            page_response.raise_for_status()
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.HTTPError:
            raise
        except:
            raise
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


def tableprint(tabledata, header=''):
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
                vacancies = superjob_vacancies(lang, api_key)
            except:
                traceback.print_exc()
                continue
            tabledata.append(
                    [
                lang,
                vacancies['vacancies_found'],
                vacancies['vacancies_processed'],
                vacancies['average_salary']
                ]
            )
        tableprint(tabledata, 'SuperJobMoscow')

    if headhunter:
        tabledata = []
        for lang in languages:
            try:
                vacancies = head_hunter_vacancies(lang)
            except:
                traceback.print_exc()
                continue
            tabledata.append(
                    [
                lang,
                vacancies['vacancies_found'],
                vacancies['vacancies_processed'],
                vacancies['average_salary']
                ]
            )
        tableprint(tabledata, 'HeadHunterMoscow')
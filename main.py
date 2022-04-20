import requests


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

languages = ['Python', 'Java', 'Javascript', 'C++', 'Pascal']
vacancies = {}
for lang in languages:
    vacancies[lang] = {}
    payload = {
        'text': lang,
        'area': '1',
        'period': '30',
        'only_with_salary': 'true'
    }
    response = requests.get('https://api.hh.ru/vacancies', params=payload).json()
    vacancies[lang]['vacancies_found'] = response['found']
    count = 0
    total_salary = 0
    for vacancy in response['items']:
        salary = predict_rub_salary(vacancy)
        if not salary:
            continue
        total_salary += salary
        count += 1
    vacancies[lang]['vacancies_processed'] = count
    vacancies[lang]['average_salary'] = int(total_salary/count)
print(vacancies)
import requests


languages = ['Python', 'Java', 'Javascript', 'C++', 'Pascal']
vacancies = {}
for lang in languages:
    payload = {
        'text': lang,
        'area': '1',
        'period': '30'
    }
    response = requests.get('https://api.hh.ru/vacancies', params=payload)
    vacancies[lang] = response.json()['found']
print(vacancies)
from bs4 import BeautifulSoup as bs
import urllib.request
import time
import sys
import csv
import re
import config

pages_count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
url_site = 'https://hh.ru/search/vacancy?clusters=true&enable_snippets=true&specialization=1&specialization=25&no_magic=true&area=90'


def get_html_page(url):
    """return html code of page"""

    response = urllib.request.urlopen(url)
    return response.read()


def get_avg_salary(salary):
    """return avg salary in rubles or None if not defined"""

    if salary != "Не указана":
        if salary.find("USD") != -1:
            convert = True
        else:
            convert = False

        avg_salary = re.sub("[^0123456789-]", "", salary)
        avg_salary = re.findall(r'\d+', avg_salary)
        avg_salary = (int(avg_salary[0]) + int(avg_salary[1])) / 2 if len(avg_salary) > 1 else int(avg_salary[0])

        if convert:
            avg_salary *= 60

        return avg_salary


def parse(url, page_count):
    """return list of vacancies"""

    result = []
    avg_salary = 0
    counter_with_salary = 0
    counter_all = 0

    for page in range(page_count):
        soup = bs(get_html_page(url + '&page=%d' % page), 'html.parser')

        # all vacancies
        vacancies = soup.find_all('div', {'class': ['search-result-description__item_primary']})

        for vacancy in vacancies:
            counter_all += 1
            job = vacancy.find('a', {'class': 'search-result-item__name'}).string
            salary = vacancy.find('div', class_='b-vacancy-list-salary')

            if config.ONLY_WITH_SALARY and not salary:
                continue

            salary = salary.text if salary else 'Не указана'
            avg_salary_vacancy = get_avg_salary(salary)

            if avg_salary_vacancy is not None:
                avg_salary += avg_salary_vacancy
                counter_with_salary += 1
            else:
                avg_salary_vacancy = "Не указана"

            company = vacancy.find('div', class_="search-result-item__company").text
            date = vacancy.find('span', class_="b-vacancy-list-date").text

            if config.SHOW_IN_CONSOLE:
                print("%s / %s / %s / %s / %s" % (job, salary, avg_salary_vacancy, company, date))

            result.append({
                "job": job,
                "salary": salary,
                "avg_salary_vacancy": avg_salary_vacancy,
                "company": company,
                "date": date
            })

        print("progress %d%%" % round((page + 1) / page_count * 100))
        time.sleep(config.SLEEP_TIME)

    avg_salary = avg_salary / counter_with_salary
    print("vacancies total count = %d" % counter_all)
    print("vacancies with salary = %d" % counter_with_salary)
    print("avg salary = %d" % avg_salary)
    return result


def save_vacancies(vacancies_list, file):
    with open(file, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(("Должность", "Зарплата", "Средняя зп", "Компания", "Дата"))

        for vacancy in vacancies_list:
            writer.writerow((
                vacancy['job'],
                vacancy['salary'],
                vacancy['avg_salary_vacancy'],
                vacancy['company'],
                vacancy['date']
            ))


vacancies_all = parse(url_site, pages_count)
save_vacancies(vacancies_all, "vacancies.csv")

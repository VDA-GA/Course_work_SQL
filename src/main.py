from pprint import pprint

from src.config import config
from src.DBManager import DBManager
from src.utils import create_database, get_top_employers, get_vacancies_by_employer, save_data_to_database


def main() -> None:
    """Основная функция"""
    keyword = input('Введите слово для поиска работодателей \n')
    list_employers = get_top_employers(keyword)
    list_vacancies = get_vacancies_by_employer(list_employers)
    params = config()
    create_database('head_hunters', params)
    save_data_to_database(list_employers, list_vacancies, 'head_hunters', params)
    print('База данных создана!')
    dbm = DBManager('head_hunters', ['employers', 'vacancies'], params)
    list_employers_and_vacancies = dbm.get_companies_and_vacancies_count()
    list_all_vacancies = dbm.get_all_vacancies()
    avg_salary = dbm.get_avg_salary()
    vac_with_higher_salary = dbm.get_vacancies_with_higher_salary()
    vac_with_keyword = dbm.get_vacancies_with_keyword(keyword)
    pprint(f'Список всех компаний с количеством вакансий: {list_employers_and_vacancies}')
    pprint(f'Данные по вакансиям: {list_all_vacancies}')
    print(f'Средняя зарплата составляет: {avg_salary}')
    pprint(f'Список вакансий с зарплатой выше средней: {vac_with_higher_salary}')
    pprint(f'Список вакансий с вашим ключевым словом: {vac_with_keyword}')


if __name__ == '__main__':
    main()

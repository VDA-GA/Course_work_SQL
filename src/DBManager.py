import psycopg2


class DBManager:
    def __init__(self, dbname: str, list_tables: list, params: dict) -> None:
        """Инициализатор класса DBManager
        :param dbname - имя базы данных
        :param list_tables - список названий таблиц
        :param params - параметры для входа"""
        self.dbname = dbname
        self.list_tables = list_tables
        self.__params = params

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dbname}. Tables: {self.list_tables})"

    def get_companies_and_vacancies_count(self) -> list:
        """Метод для получения списка всех компаний и количества вакансий у каждой компании."""
        conn = psycopg2.connect(dbname=self.dbname, **self.__params)
        with conn.cursor() as cur:
            cur.execute("SELECT employers.employer_name, COUNT(*) FROM vacancies "
                        "INNER JOIN employers USING (employer_id)"
                        "GROUP BY employers.employer_name")
            list_employers_and_vacancies = cur.fetchall()
        conn.close()
        return list_employers_and_vacancies

    def get_all_vacancies(self) -> list:
        """Метод получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию."""
        conn = psycopg2.connect(dbname=self.dbname, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT employers.employer_name, vacancy_name, salary_from, salary_to, vacancy_url FROM vacancies "
                "INNER JOIN employers USING (employer_id)")
            list_all_vacancies = cur.fetchall()
        conn.close()
        return list_all_vacancies

    def get_avg_salary(self) -> int:
        """Метод получает среднюю зарплату по вакансиям."""
        conn = psycopg2.connect(dbname=self.dbname, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT (AVG(salary_from) + AVG(salary_to))/2 FROM vacancies ")
            avg_salary = cur.fetchall()
        conn.close()
        return round(avg_salary[0][0])

    def get_vacancies_with_higher_salary(self) -> list:
        """Метод получает список всех вакансий, у которых зарплата выше средней по всем вакансиям."""
        conn = psycopg2.connect(dbname=self.dbname, **self.__params)
        avg_salary = self.get_avg_salary()
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM vacancies WHERE (salary_from + salary_to)/2 >= {avg_salary}")
            vac_with_higher_salary = cur.fetchall()
        conn.close()
        return vac_with_higher_salary

    def get_vacancies_with_keyword(self, keyword) -> list:
        """Метод получает список всех вакансий, в названии которых содержатся переданные в метод слова
        :param keyword - слово для фильтрации"""
        conn = psycopg2.connect(dbname=self.dbname, **self.__params)
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM vacancies WHERE vacancy_name LIKE '%{keyword}%'")
            vac_with_keyword = cur.fetchall()
        conn.close()
        return vac_with_keyword

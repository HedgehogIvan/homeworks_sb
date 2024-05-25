from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from fake_useragent import FakeUserAgentError
import undetected_chromedriver as uc
from time import sleep
import pandas as pd
import random


PROXIES = [
        "socks4://37.228.65.107:51032",
        "socks4://85.29.147.90:5678",
        "http://213.230.110.47:3128",
        "socks4://95.220.110.1:80",
        "http://188.247.194.210:3128",
        "http://213.5.188.210:3128",
        "http://185.74.6.247:8080"
    ]


def create_link(_brand, _model, _page=None):
    _brand = _brand.replace(' ', '+')
    _model = _model.replace(' ', '+')
    return (
        f"https://www.avito.ru/moskva/avtomobili?cd=1"
        f"{f'&p={_page}' if _page else ''}"
        f"&q="
        f"{_brand}+"
        f"{_model}"
        f"&radius=0&searchRadius=0"
    )


def get_driver_with_proxy(proxies):
    if len(proxies) == 0:
        return None

    i_proxy = random.randint(0, len(proxies) - 1)
    proxy = proxies.pop(i_proxy)

    try:
        agent = UserAgent().chrome
    except FakeUserAgentError:
        agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36 Edg/104.0.1293.47"
    options = uc.ChromeOptions()
    options.add_argument(f"user-agent={agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--proxy-server={proxy}")

    driver = uc.Chrome(options=options)
    driver.implicitly_wait(20)

    return driver


def avito_parser(brand, model):
    proxies = PROXIES.copy()
    page = None
    attempt_count = 0

    cars_dict = {
        "Name": [],
        "Link": [],
        "Price": []
    }

    driver = get_driver_with_proxy(proxies)

    while True:
        if driver is None:
            print("ERROR: Закончить парсинг не удалось, кончились прокси")
            break

        if attempt_count > 1:
            attempt_count = 0
            print("Смена прокси")

            # Перезапуск драйвера
            driver.quit()
            driver = get_driver_with_proxy(proxies)

            continue

        url = create_link(brand, model, page)

        try:
            driver.get(url)
        except Exception as e:
            print(e)
            attempt_count += 1
            sleep(30)
            continue

        if driver.title == 'Доступ ограничен: проблема с IP':
            print("ERROR: IP блочат")
            attempt_count += 1
            sleep(30)
            continue

        # Поиск объявлений
        cars = driver.find_elements(by=By.XPATH, value='//div[@data-marker="catalog-serp"]/div[@data-marker="item"]')

        if len(cars) > 0:
            for car in cars:
                # Название
                name = car.find_element(by=By.XPATH, value='.//a[@data-marker = "item-title"]/h3').text
                # Ссылка
                link = car.find_element(By.XPATH, './/a[@data-marker = "item-title"]').get_attribute("href")
                # Цена
                price = car.find_element(By.XPATH, './/*[@itemprop="price"]').get_attribute("content")

                cars_dict["Name"].append(name)
                cars_dict["Link"].append(link)
                cars_dict["Price"].append(price)

        # Поиск стрелки пагинации (next)
        # Если автомобилей на сайте меньше, чем стандартное кол-во авто на страницу (50),
        # то к основным объявлениям добавляются объявления из других городов.
        # Средство пагинации у обоих элементов идентично.
        # Чтобы избежать ложного срабатывания перехода на следующую страницу,
        # было решено искать списки с объявлениями.
        # Если список один, то это нужный переход
        # Если два, то переход рекламный
        car_lists = driver.find_elements(by=By.XPATH, value='//div[contains(@class, "items-items")]')
        if car_lists == 1:
            try:
                next_page = driver.find_element(by=By.XPATH, value='//a[@data-marker="pagination-button/nextPage"]')
            except:
                break
        else:
            break

        # Если страница не указана (None), но есть кнопка перехода, то следующая страница будет 2-ой
        if page:
            page += 1
        else:
            page = 2

        nap = random.uniform(30, 90)
        sleep(nap)

    df = pd.DataFrame(cars_dict)

    return df

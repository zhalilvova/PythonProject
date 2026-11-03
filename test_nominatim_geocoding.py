import pytest
import requests
import time
import json


# Базовый URL публичного API Nominatim
BASE_URL = "https://nominatim.openstreetmap.org"

# Обязательный заголовок User-Agent по правилам использования сервиса
HEADERS = {
    "User-Agent": "MyGeocodingApp/1.0 (madinajalilova7@gmail.com)",
    "Accept": "application/json",
    "Accept-Language": "ru",
}

# DDT: Набор данных для прямого геокодирования (Адрес -> Координаты)
# Формат: (query, expected_country_code)
FORWARD_CASES = [
    ("Медный всадник, Санкт-Петербург", "ru"),
    ("Озеро Байкал, Иркутск", "ru"),
    ("Пирамида Хеопса, Гиза", "eg"),
    ("Большой Барьерный риф, Австралия", "au"),
]

# DDT: Набор данных для обратного геокодирования (Координаты -> Адрес)
# Формат: (lat, lon, expected_country_code)
REVERSE_CASES = [
    ("59.9364", "30.3022", "ru"),  #  Медный всадник
    ("53.6167299", "108.1307186", "ru"),  # Озеро байкал
    ("29.9791647", "31.1342133", "eg"),  # Пирамида Хеопса
    ("-16.35", "145.9", "au"),  # Большой барьерный рельеф

]

# DDT: Набор данных для обратного геокодирования (Координаты -> Адрес) негатив
# Формат: (query, expected_country_code)
FORWARD_NEGATIVE_CASES = [
    ("", ""),
    ("asdfghjklqwerty123456", "запрос"),
]

# DDT: Набор данных для обратного геокодирования (Координаты -> Адрес) негатив
# Формат: (lat, lon, expected_country_code)
REVERSE_NEGATIVE_CASES = [
    ("", "",""),
    ("29.9791647", "","ru"),
]

@pytest.fixture(autouse=True)
def polite_delay():
    time.sleep(1.1)


@pytest.mark.parametrize("query, expected_country_code", FORWARD_CASES)
def test_forward_geocoding(query, expected_country_code):
    #Прямое геокодирование: Поиск координат по текстовому адресу.
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1
    }

    response = requests.get(f"{BASE_URL}/search", params=params, headers=HEADERS)

    #Проверка HTTP статуса
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"

    data = response.json()

    #Проверка, что результат не пустой (найдено хотя бы одно место)
    assert len(data) > 0, f"По запросу '{query}' ничего не найдено"

    first_result = data[0]

    #Проверка структуры ответа (наличие ключевых полей)
    assert "lat" in first_result
    assert "lon" in first_result
    assert "display_name" in first_result

    actual_country = first_result.get("address", {}).get("country_code", "").lower()
    assert actual_country == expected_country_code, \
        f"Ожидалась страна '{expected_country_code}', получена '{actual_country}'"

    # Вывод координат
    coords = {"Широта": data[0]["lat"], "Долгота": data[0]["lon"]}
    print(json.dumps(coords, ensure_ascii=False, indent=2))


@pytest.mark.parametrize("lat, lon, expected_country_code", REVERSE_CASES)
def test_reverse_geocoding(lat, lon, expected_country_code):
    #Обратное геокодирование: Получение адреса по координатам.
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "addressdetails": 1

    }

    response = requests.get(f"{BASE_URL}/reverse", params=params, headers=HEADERS)

    #Проверка HTTP статуса
    assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"

    data = response.json()

    #Проверка, что ответ не содержит ошибки (Nominatim возвращает 'error' при неудаче)
    assert "error" not in data, f"API вернул ошибку: {data.get('error')}"

    # Вывод адреса
    address = data.get("address", {})
    print("\n" + json.dumps({
        "Место": data.get("display_name"),
        "Адрес": address,
    }, ensure_ascii=False, indent=2))

    #Проверка соответствия страны
    actual_country = data.get("address", {}).get("country_code", "").lower()
    assert actual_country == expected_country_code, \
        f"Ожидалась страна '{expected_country_code}', получена '{actual_country}' для координат ({lat}, {lon})"


@pytest.mark.parametrize("query, expected_country_code", FORWARD_NEGATIVE_CASES)
def test_forward_geocoding_negative(query, expected_country_code):
    #Прямое геокодирование (негатив)
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1
    }
    response = requests.get(f"{BASE_URL}/search", params=params, headers=HEADERS)

    # Проверка HTTP статуса
    if response.status_code == 200:
        data = response.json()
        assert "error" in data, f"Ожидалась ошибка, получено: {data}"
    else:
        assert response.status_code == 400, \
            f"Ожидался 400 для запроса {query}, получен {response.status_code}: {response.text}"


@pytest.mark.parametrize("lat, lon, expected_country_code", REVERSE_NEGATIVE_CASES)
def test_reverse_geocoding_negative(lat, lon,expected_country_code):
    #Обратное геокодирование (негатив)
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2"
    }
    response = requests.get(f"{BASE_URL}/reverse", params=params, headers=HEADERS)


    # Проверка HTTP статуса
    if response.status_code == 200:
        data = response.json()
        assert "error" in data, f"Ожидалась ошибка, получено: {data}"
    else:
        print(f"Ожидался 400, получен '{response.status_code}': '{response.text}'")
        assert response.status_code == 400, \
           f"Ожидался 400, получен {response.status_code}: {response.text}"


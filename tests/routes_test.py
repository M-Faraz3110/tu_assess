import requests


def login():
    url = "http://127.0.0.1:8000/login"
    data = {
        "username": "doctor1",
        "password": "doc1"
    }
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*'}
    r = requests.post(url, headers=headers, data=data)
    return r.json()


def test_login_jwt():
    url = "http://127.0.0.1:8000/login"
    data = {
        "username": "doctor1",
        "password": "doc1"
    }
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*'}
    r = requests.post(url, headers=headers, data=data)
    print(r.json())
    assert r.headers["Content-Type"] == "application/json"


def test_get_docs():
    response = requests.get('http://127.0.0.1:8000/doctors')
    assert response.headers["Content-Type"] == "application/json"


def test_get_docid():
    response = requests.get('http://127.0.0.1:8000/doctors/2')
    assert response.headers["Content-Type"] == "application/json"


def test_slots():
    token = login()
    access_token = token["access_token"]
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*',
               'Authorization': 'Bearer' + access_token}
    response = requests.get(
        "http://127.0.0.1:8000/doctors/1/slots", headers=headers)
    assert response.headers["Content-Type"] == "application/json"


def test_book():
    token = login()
    access_token = token["access_token"]
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*',
               'Authorization': 'Bearer' + access_token}
    response = requests.get(
        "http://127.0.0.1:8000/book/2/?duration=20", headers=headers)
    assert response.headers["Content-Type"] == "application/json"


def test_av():
    token = login()
    access_token = token["access_token"]
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*',
               'Authorization': 'Bearer' + access_token}
    response = requests.get(
        "http://127.0.0.1:8000/available", headers=headers)
    assert response.headers["Content-Type"] == "application/json"


def test_history():
    token = login()
    access_token = token["access_token"]
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*',
               'Authorization': 'Bearer' + access_token}
    response = requests.get(
        "http://127.0.0.1:8000/history", headers=headers)
    assert response.headers["Content-Type"] == "application/json"


def test_apps():
    token = login()
    access_token = token["access_token"]
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*',
               'Authorization': 'Bearer' + access_token}
    response = requests.get(
        "http://127.0.0.1:8000/appointments", headers=headers)
    assert response.headers["Content-Type"] == "application/json"


def test_mostapps():
    token = login()
    access_token = token["access_token"]
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*',
               'Authorization': 'Bearer' + access_token}
    response = requests.get(
        "http://127.0.0.1:8000/mostapps", headers=headers)
    assert response.headers["Content-Type"] == "application/json"


def plushours():
    token = login()
    access_token = token["access_token"]
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Accept': '*/*',
               'Authorization': 'Bearer' + access_token}
    response = requests.get(
        "http://127.0.0.1:8000/6+hours", headers=headers)
    assert response.headers["Content-Type"] == "application/json"

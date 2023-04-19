from requests import get


def get_question(quantity=1):
    url = 'http://jservice.io/api/random'
    params = {'count': quantity}
    tex, res = get(url, params=params).json(), []
    for i in range(quantity):
        res.append([tex[i]['question'], tex[i]['answer']])
    return res


def get_question_with_params(quantity, value):
    url = 'http://jservice.io/api/random'
    params = {'count': quantity, 'value': value}
    tex, res = get(url, params=params).json(), []
    for i in range(quantity):
        res.append([tex[i]['question'], tex[i]['answer']])
    return res

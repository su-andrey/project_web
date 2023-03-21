from requests import get
import json


def get_question(quantity=1):
    url = 'http://jservice.io/api/random'
    params = {'count': quantity}
    tex, res = get(url, params=params).json(), []
    for i in range(quantity):
        res.append([tex[i]['question'], tex[i]['answer']])
    return res



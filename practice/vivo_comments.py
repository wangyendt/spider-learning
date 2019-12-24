#!/usr/bin/env python
# encoding: utf-8

"""
@author: Wayne
@contact: wangye.hope@gmail.com
@software: PyCharm
@file: vivo_comments
@time: 2019/10/12 14:51
"""

import os
import time
from multiprocessing import Pool
from urllib.parse import urlencode

import jsonpath
import pandas as pd
import requests
from fake_useragent import UserAgent

products = {
    'nex3': 10001477,
    'iqoo': 10000467,
    'iqoo-pro': 10001399
}
save_path = 'data/vivo-comments.txt'
save_excel_path = 'data/vivo-comments.xlsx'
url_base = 'http://shop.vivo.com.cn/api/v1/remark/getDetail?'

ua = UserAgent()


def get_page_number():
    json_str = get_one_page_comments(
        url_base,
        'iqoo-pro'
    )
    page_numbers = jsonpath.jsonpath(json_str, '$..pages')
    return int(page_numbers[0])


def get_one_page_comments(url, product, page=1):
    header = {
        'user-agent': ua.random,
        # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
    }
    data = {
        'spuId': products[product],
        'onlyHasPicture': False,
        'fullpaySkuIdSet': '',
        'pageNum': page,
        'pageSize': 10,
        't': int(time.time() * 1000)
    }
    try:
        response = requests.get(url + urlencode(data), headers=header)
        time.sleep(1)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'状态码错误{response.status_code}')
            return None
    except:
        print(f'爬取单页失败{url}')
        return None


def parse_one_page_comments(page):
    json_str = get_one_page_comments(
        url_base,
        'nex3', page
    )
    # import pprint
    # pprint.pprint(json_str)
    comments = jsonpath.jsonpath(json_str, '$..content')
    score = jsonpath.jsonpath(json_str, '$..summaryScore')
    if comments:
        for comm, scr in zip(comments, score):
            yield {'content': comm, 'score': int(scr)}


def clear_save_file():
    if os.path.exists(save_path):
        os.remove(save_path)


def save_to_file(contents):
    with open(save_path, 'a+', encoding='utf-8') as f:
        for content in contents:
            print(content)
            f.write(f'score: {content["score"]}, comment: {content["content"]}\n')
    res = pd.DataFrame(contents)
    res.to_excel(save_excel_path)


def work(page):
    print(f'正在爬取第{page}页...')
    return [dic for dic in parse_one_page_comments(page)]


if __name__ == '__main__':
    page_number = get_page_number()
    clear_save_file()
    pool = Pool()
    max_worker = 64
    n_tasks = page_number // max_worker
    result = []
    for i in range(n_tasks + 1):
        result += (pool.imap(work, range(max_worker * i + 1, min(page_number, max_worker * (i + 1)) + 1)))
    # todo: 要改成监听异步减少运行时间
    save_to_file(sum(result, []))

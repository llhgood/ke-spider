import random
import time
import os
import sys
from pathlib import Path
import pandas as pd
from curl_cffi import requests
import urllib.parse
from bs4 import BeautifulSoup


def get_local_path(filename: str) -> str:
    """始终从当前目录/可执行文件目录/源码目录查找外置文件，不使用 _MEIPASS。"""
    candidates = []
    # 1) 当前工作目录
    candidates.append(Path.cwd() / filename)
    # 2) 可执行文件所在目录（PyInstaller 打包后）
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / filename)
    # 3) 源码文件所在目录（开发运行）
    candidates.append(Path(__file__).resolve().parent / filename)

    for p in candidates:
        if p.exists():
            return str(p)
    # 找不到则返回当前目录的目标路径，后续 open 会抛 FileNotFoundError
    return str(Path.cwd() / filename)


def get_detail(url, cookies):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://wh.ke.com/ershoufang/sf1c376946150952833rs%E6%81%92%E5%A4%A7%E5%BE%A1%E6%99%AF%E6%B9%BE/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Cookie': f'{cookies}',
    }

    response = requests.get(
        url,
        headers=headers,
    )
    soup = BeautifulSoup(response.text, 'html.parser')
    ul = soup.find('ul', {'class': 'sellListContent'})
    if ul:
        li = ul.findAll('li')[0]
        price = li.find('div', {'class': 'totalPrice'}).text.strip().replace('\n', '')
        unitPrice = li.find('div', {'class': 'unitPrice'}).text.strip()
        print(price, unitPrice)
        return price, unitPrice
    else:
        return None, None


if __name__ == '__main__':
    # 使用正确的路径获取文件
    try:
        cookies_path = get_local_path('cookies.txt')
        print(f"正在读取cookies文件: {cookies_path}")

        with open(cookies_path, encoding='utf8') as f:
            cookies = f.readline().strip()
        print("成功读取cookies")

    except FileNotFoundError:
        print("错误: 找不到cookies.txt文件")
        print("请确保cookies.txt与可执行文件或当前运行目录在同一目录下")
        print("当前目录文件列表:", os.listdir('.'))
        sys.exit(1)

    all_data = []
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://wh.ke.com/ershoufang/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Cookie': f'{cookies}',
    }

    # 使用正确的路径获取Excel文件
    try:
        excel_path = get_local_path('房源.xlsx')
        print(f"正在读取Excel文件: {excel_path}")
        df = pd.read_excel(excel_path)
        lf_name = df['楼盘名称'].tolist()
        print(f"成功读取Excel文件，共{len(lf_name)}条数据")

    except FileNotFoundError:
        print("错误: 找不到房源.xlsx文件")
        print("请确保房源.xlsx与可执行文件或当前运行目录在同一目录下")
        sys.exit(1)

    for name in lf_name:
        print(f"正在处理: {name}")
        reuslt = dict()
        reuslt['name'] = name
        code = urllib.parse.quote(name)
        response = requests.get(
            f'https://wh.ke.com/ershoufang/rs{code}/',
            headers=headers,
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        list_more = soup.find_all('div', class_='list-more')
        dl = soup.find_all('dl')[0]
        h2 = dl.find('h2')
        if h2.text.strip() == '小区':
            url = dl.find('a')['href']
            url_code = url.split('/')[-1]
            detail_url = ('https://wh.ke.com/ershoufang/co41sf1' + url_code + '/')
            print(detail_url)
            price, unitPrice = get_detail(detail_url, cookies)
            if unitPrice:
                unitPrice = int(unitPrice.split('元')[0].replace(',', '')) / 10000
            reuslt['price'] = price
            reuslt['unitPrice'] = unitPrice
            all_data.append(reuslt)
        print(reuslt)
        time.sleep(random.randint(1, 3))

    result_df = pd.DataFrame(all_data)
    result_df.to_excel('结果.xlsx', index=False)
    print("爬取完成，结果已保存到 结果.xlsx")

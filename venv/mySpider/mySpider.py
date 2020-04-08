# -*- coding: utf-8 -*- 
# @Time : 2020/4/8 17:55 
# @Author : lzm 
# @File : mySpider.py

"""
微信公众号采集器
"""
import sys

import requests
import re
import json
import time
import os
from bs4 import BeautifulSoup
import logging as log


class WeChatSpider(object):

    def getCookies(self):
        """
        从txtw文件中读取cookie
        :return:
        """
        with open('../wechat-cookie.txt', 'r') as file:
            cookie = file.read()
        cookies = json.loads(cookie)
        return cookies

    def getToken(self, cookies):
        """
        通过请求微信公众平台，获取到下一步请求的参数token
        :return:
        """
        url = 'https://mp.weixin.qq.com/'
        response = requests.get(url=url, cookies=cookies)
        response_url = response.url
        # 正则表达式匹配响应的url中的token值
        # https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=105208983
        # print(response_url)
        token = re.match('^http.*token=(\d+)$', response_url)
        token = token.group(1)
        log.debug('获取到的token值是：[%s]', token)
        return token

    def getFakeId(self, cookies, token, query):
        """
        获取公众号的唯一id，提供给获取文章时使用
        """
        headers = {
            "Referer": 'https://mp.weixin.qq.com/cgi-bin/appmsg?action=list_ex&begin=0&count=5&fakeid=&type=9&query' \
                       '=&token=' + token + '&lang=zh_CN&f=json&ajax=1',
            "Host": "mp.weixin.qq.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/79.0.3945.88 Safari/537.36 "
        }
        request_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&begin=0&count=5&query=' + query + '&token=' + token + '&lang=zh_CN&f=json&ajax=1'
        response = requests.get(request_url, cookies=cookies, headers=headers)
        # print(response.text)
        text_json = response.json()
        wechats = text_json.get('list')
        fake_id = ''
        for item in wechats:
            if item['nickname'] == query:
                fake_id = item['fakeid']
                break
        log.debug('获取到的fakeid是：[%s]', fake_id)
        return fake_id

    def getArticles(self, cookies, token, fake_id):
        """
        获取公众号的文章
        :param cookies:
        :param token:
        :param fake_id:
        :return:
        """
        headers = {
            "Referer": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10"
                       "&token=" + token + "&lang=zh_CN",
            "Host": "mp.weixin.qq.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/79.0.3945.88 Safari/537.36 "
        }
        for page in range(1, 2, 1):
            log.debug('开始执行第[%s]页数据采集', page)
            start = (page - 1) * 5
            requestUrl = "https://mp.weixin.qq.com/cgi-bin/appmsg?action=list_ex&begin=" + str(
                start) + "&count=5&fakeid=" + fake_id + "&type=9&query=&token=" + token + "&lang=zh_CN&f=json&ajax=1"
            response = requests.get(requestUrl, cookies=cookies, headers=headers)
            text_json = response.json()
            articles = text_json.get('app_msg_list')
            for i in articles:
                log.debug('文章标题:[%s]，发布时间:[%s], 详情地址:[%s]' % (
                    i['title'], time.strftime('%Y-%M-%d %H:%M:%S', time.localtime(i['create_time'])), i['link']))
                title = i['title'].replace(' ', '')
                detail_response = requests.get(i['link'], cookies=cookies, headers=headers)
                self.save(detail_response, i['aid'], i['aid'])
            time.sleep(10)
            print('--------------------------------------------------')

    def save(self, response, html_dir, file_name):
        """
        将微信文章详情以及图片保存为html格式
        """
        # 保存 html 的位置
        htmlDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), html_dir)
        # 保存图片的位置
        targetDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), html_dir + '/images')
        # 不存在创建文件夹
        if not os.path.isdir(targetDir):
            os.makedirs(targetDir)
        domain = 'https://mp.weixin.qq.com/s'
        # 调用保存 html 方法
        self.save_html(response, htmlDir, file_name)
        # 调用保存图片方法
        self.save_file_to_local(htmlDir, targetDir, response, domain, file_name)

    def save_html(self, url_content, html_dir, file_name):
        f = open(html_dir + "/" + file_name + '.html', 'wb')
        # 写入文件
        f.write(url_content.content)
        f.close()
        return url_content

    def save_file_to_local(self, html_dir, target_dir, search_response, domain, file_name):
        # 使用lxml解析请求返回的页面
        obj = BeautifulSoup(self.save_html(search_response, html_dir, file_name).content, 'lxml')
        # 找到有 img 标签的内容
        imgs = obj.find_all('img')
        # 将页面上图片的链接加入list
        urls = []
        for img in imgs:
            if 'data-src' in str(img):
                urls.append(img['data-src'])
            elif 'src=""' in str(img):
                pass
            elif "src" not in str(img):
                pass
            else:
                urls.append(img['src'])

        # 遍历所有图片链接，将图片保存到本地指定文件夹，图片名字用0，1，2...
        i = 0
        for each_url in urls:
            # 跟据文章的图片格式进行处理
            if each_url.startswith('//'):
                new_url = 'https:' + each_url
                r_pic = requests.get(new_url)
            elif each_url.startswith('/') and each_url.endswith('gif'):
                new_url = domain + each_url
                r_pic = requests.get(new_url)
            elif each_url.endswith('png') or each_url.endswith('jpg') or each_url.endswith('gif') or each_url.endswith(
                    'jpeg'):
                r_pic = requests.get(each_url)
            # 创建指定目录
            t = os.path.join(target_dir, str(i) + '.jpeg')
            print('该文章共需处理' + str(len(urls)) + '张图片，正在处理第' + str(i + 1) + '张……')
            # 指定绝对路径
            fw = open(t, 'wb')
            # 保存图片到本地指定目录
            fw.write(r_pic.content)
            i += 1
            # 将旧的链接或相对链接修改为直接访问本地图片
            self.update_file(each_url, t, html_dir, file_name)
            fw.close()

    def update_file(self, old, new, html_dir, file_name):
        # 打开两个文件，原始文件用来读，另一个文件将修改的内容写入
        with open(html_dir + "/" + file_name + '.html', encoding='utf-8') as f, open(
                html_dir + "/" + file_name + '_bak.html', 'w', encoding='utf-8') as fw:
            # 遍历每行，用replace()方法替换路径
            for line in f:
                new_line = line.replace(old, new)
                new_line = new_line.replace("data-src", "src")
                # 写入新文件
                fw.write(new_line)
        # 执行完，删除原始文件
        os.remove(html_dir + "/" + file_name + '.html')
        time.sleep(5)
        # 修改新文件名为 html
        os.rename(html_dir + "/" + file_name + '_bak.html', html_dir + "/" + file_name + '.html')


# spider = WeChatSpider()
# print(wechat-spider.getToken(wechat-spider.getCookies()))


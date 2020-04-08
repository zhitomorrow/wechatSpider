# -*- coding: utf-8 -*- 
# @Time : 2020/4/8 17:55 
# @Author : lzm 
# @File : myCookie.py

"""
处理微信公众平台cookie相关内容
"""

import json


class WechatCookie(object):

    def cookieStrToJson(self):
        """
        将cookie字符串转换成json格式存储到文件中
        :return:
        """
        # 微信公众平台cookie
        cookieStr = 'xxx'

        cookie_map = {}

        for cookies in cookieStr.split(';'):
            cookie_item = cookies.split('=')
            cookie_map[cookie_item[0]] = cookie_item[1]
        with open('../wechat-cookie.txt', 'w') as file:
            file.write(json.dumps(cookie_map))


cla = WechatCookie()
cla.cookieStrToJson()
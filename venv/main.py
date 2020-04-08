# -*- coding: utf-8 -*- 
# @Time : 2020/4/8 17:45 
# @Author : lzm 
# @File : main.py


from myCookie import myCookie
from mySpider import mySpider

def main():
    # cookie_cla = myCookie.WechatCookie()
    # cookie_cla.cookieStrToJson()

    spider = mySpider.WeChatSpider()
    c = spider.getCookies()
    t = spider.getToken(c)
    fid = spider.getFakeId(c, t, '关哥说险')
    spider.getArticles(c, t, fid)


if __name__ == '__main__':
    main()
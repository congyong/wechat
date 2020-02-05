#!/usr/bin/env python
# coding:utf8
#from __future__ import unicode_literals
from bs4 import BeautifulSoup
import sys
import random
import requests
import re
import os
from threading import Timer
reload(sys)
sys.setdefaultencoding( "utf8" )

import itchat
from itchat.content import *

# step1 ： 安装itchat 和其他依赖
# step2 :  将需要同步的群聊保存，建议群聊名前面字符想用用尾数区分，这样可以一个账号同步不同类型的群聊组
# step3 :  执行这个脚本
# step4 ： 也可以配置下面几个变量，以实现不检查群名(全部同步) 和检查群名（分类同步）
# others:  脚本会定时往文件助手推送新闻,减少掉线几率,由于腾讯策略问题,凌晨4点多会掉线,这个解决不了

#define function
#检查群名开启
check_name=True
#检查长度
check_len =3 #比对的群名称字符长度
#比如需要同步的群为 测试群1 测试群2，设置比对长度为3即可
#也可以把check_name关闭，这样所有会同步到所有的保存的群聊


#如果新消息群名包含以下字节不转发,即单向同步, 可以做到把检测的群聊信息集中
check_str = "one-way"

# 自动回复文本等类别消息
# isGroupChat=False表示非群聊消息
#@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING], isGroupChat=False)
#def text_reply(msg):
#   itchat.send('代码测试--- ', msg['FromUserName'])
#
## 自动回复图片等类别消息
## isGroupChat=False表示非群聊消息
#@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO], isGroupChat=False)
#def download_files(msg):
#   itchat.send('代码测试---', msg['FromUserName'])
#
# 自动处理添加好友申请
#@itchat.msg_register(FRIENDS)
#def add_friend(msg):
#   itchat.add_friend(**msg['Text']) # 该操作会自动将新好友的消息录入，不需要重载通讯录
#   itchat.send_msg(u'萨瓦迪卡', msg['RecommendInfo']['UserName'])
#    

# tencent news

def sohunews():
    url="http://news.sohu.com/"
    wbdata=requests.get(url).text
    soup=BeautifulSoup(wbdata,'lxml')
    news_titles=soup.select("div.list16>ul>li>a")
    i = random.randint(0,len(news_titles)-1)
    title=news_titles[i].get_text()
    title=title.replace(' ','')
    link=news_titles[i].get("href")
    return title,link

def downnews():
    url_group = ["http://news.qq.com/world_index.shtml","https://news.qq.com/index.shtml"]
    url=url_group[random.randint(0,len(url_group)-1)]
    #请求腾讯新闻的URl，获取其text文本
    wbdata = requests.get(url).text
    #对获取的文本进行解析
    soup = BeautifulSoup(wbdata,'lxml')
    #从解析文件中通过select选择器定位指定的元素，返回一个列表 
    ul= soup.find_all("a",class_="linkto")
    i = random.randint(0,len(ul)-1)
    #print(ul[i].text)
    #print(ul[i]['href'])
    return ul[i].text,ul[i]['href']

def auto_send_news():
    try:
        if(random.choice([True,False])):
            contents=downnews()
        else:
            contents=sohunews()
        itchat.send('https:%s'%(contents[1]), toUserName="filehelper")
        itchat.send(contents[0], toUserName="filehelper")
        #每86400秒（1天），发送1次
        #为了防止时间太固定，于是决定对其加上随机数
        ran_int=random.randint(0,100)
        t=Timer(100+ran_int,auto_send_news)
        t.start()
    except:
        itchat.send("something wrong", toUserName="filehelper")


# 自动回复文本等类别的群聊消息
# isGroupChat=True表示为群聊消息
@itchat.msg_register([TEXT, SHARING], isGroupChat=True)
def group_reply_text(msg):

    # 消息来自于哪个群聊
    chatroom_id = msg['FromUserName']
    #收到的群消息的名称
    cur_cht_name = msg['User']['NickName']
    #print ("收到群消息：%s %d\n"%(cur_cht_name,len(cur_cht_name)) ) 
    # 发送者的昵称
    username = msg['ActualNickName']

    # 消息并不是来自于需要同步的群
    if not chatroom_id in chatroom_ids:
        return 
    #群名关键字过滤 实现单向通信
    if check_str in cur_cht_name:
        return 

    if msg['Type'] == TEXT:
        content = msg['Content']
    elif msg['Type'] == SHARING:
        content = msg['Text']

    # 根据消息类型转发至其他需要同步消息的群聊
    if msg['Type'] == TEXT:
        for item in chatrooms:
            if not item['UserName'] == chatroom_id:
                #匹配群名
                    if (check_name and  (item['NickName'][0:check_len-1] == cur_cht_name[0:check_len-1]) ):
                        itchat.send('%s:\n%s' % (username, msg['Content']), item['UserName'])
#                # 关键字回复
#                   if u'查询微信号' in msg['Text']:
#                       #thewechat_account=itchat.search_friends(name=msg['Content'][5:])[0]
#                       itchat.send('%s的微信号为:%s'%(msg['Content'][5:],itchat.search_friends(name=msg['Content'][5:])[0]['UserName']),  item['UserName'])
    elif msg['Type'] == SHARING:
        for item in chatrooms:
            if not item['UserName'] == chatroom_id:
            #群名称匹配
                    if (check_name and  (item['NickName'][0:check_len-1] == cur_cht_name[0:check_len-1]) ):
                        itchat.send('%s:\n%s\n%s' % (username, msg['Text'], msg['Url']), item['UserName'])
                        #itchat.send(u'msg from--%s' %(username),item['UserName'])


# 自动回复图片等类别的群聊消息
# isGroupChat=True表示为群聊消息          
@itchat.msg_register([PICTURE, ATTACHMENT, VIDEO], isGroupChat=True)
def group_reply_media(msg):
    # 消息来自于哪个群聊
    chatroom_id = msg['FromUserName']
    #收到的群消息的名称
    cur_cht_name = msg['User']['NickName']
    #print ("收到群消息：%s %d\n"%(cur_cht_name,len(cur_cht_name)) ) 
    # 发送者的昵称
    username = msg['ActualNickName']

    # 消息并不是来自于需要同步的群
    if not chatroom_id in chatroom_ids:
        return

    # 如果为gif图片则不转发
#   if msg['FileName'][-4:] == '.gif':
#       return

    # 下载图片等文件
    msg['Text'](msg['FileName'])
    # 转发至其他需要同步消息的群聊
    for item in chatrooms:
        if not item['UserName'] == chatroom_id:
                    #比对群名
            if (check_name and  (item['NickName'][0:check_len-1] == cur_cht_name[0:check_len-1])  ):
                    itchat.send('@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName']), item['UserName'])
                    itchat.send(u'msg from--%s' %(username),item['UserName'])

# 扫二维码登录
#itchat.auto_login(hotReload=True)
itchat.auto_login(enableCmdQR=2)
# 获取所有通讯录中的群聊
# 需要在微信中将需要同步的群聊都保存至通讯录
chatrooms = itchat.get_chatrooms(update=True, contactOnly=True)
chatroom_ids = [c['UserName'] for c in chatrooms]
print '正在监测的群聊：', len(chatrooms), '个'
print ' '.join([item['NickName'] for item in chatrooms])
auto_send_news()
# 开始监测
itchat.run()

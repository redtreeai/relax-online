# -*- coding: utf-8 -*-
# @Time    : 19-6-3 下午4:53
# @Author  : Redtree
# @File    : r_server.py
# @Desc :


import asyncio
import json
import websockets
import random
import time

USERS = set()

PAN_NAME = ['3b','3w','5b','6b','7t','8b','9t','dong','fa']

#实例化服务端信息
DATA = {
    'cuser':'', #当前操作用户
    'code':'', #当前操作命令
    'a':0,  #a是否链接
    'b':0,  #b是否链接
    'ar':0, #a是否准备
    'br':0, #b是否准备
    'game_ing':0, #是否开局中
    'chatlog':[], #日志信息
    'loglong':5 , #日志长度
    'acount':0, #a消灭计数
    'bcount':0, #b消灭计数
    'turn':'a', #轮次
    'pan':[] , #盘面实际数据
    'pan_show':[],#盘面显示数据
    'checkson':[], #当前校验组
    'overed':[] #已处理过的位置组

}

#分配游戏数据
async def start_game():
    while len(DATA['pan'])<64:
        cobj = random.choice(PAN_NAME)
        DATA['pan'].append(cobj)
        DATA['pan'].append(cobj)

    while len(DATA['pan_show'])<64:
        DATA['pan_show'].append('bg')

    #每组两个 然后打乱
    random.shuffle(DATA['pan'])
    DATA['turn']='a'
    DATA['acount']=0
    DATA['bcount']=0


#重置操作数据
async def reset_cmsg():
    DATA['cuser']=''
    DATA['code']=''

# 一旦有玩家退出或投降则重置游戏数据
async def reset_ginfo():
    DATA['ar'] = 0
    DATA['br'] = 0
    DATA['game_ing'] = 0


async def notify_users():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = json.dumps(DATA)
        #发送后重置请求
        await reset_cmsg()
        await asyncio.wait([user.send(message) for user in USERS])

#登记不同用户的websocket链接
async def register(websocket):
    USERS.add(websocket)
    #登记后对所有用户进行广播
    await notify_users()


#注销不同用户的websocket链接
async def unregister(websocket):
    USERS.remove(websocket)
    #注销后对所有用户进行广播
    await notify_users()


#主通信管道
async def linker(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        async for message in websocket:
            print('客服端本次发送:'+message)
            if message == 'connect':
                if DATA['a'] == 0:
                    DATA['a'] = 1
                    DATA['chatlog'].append('玩家a进入了房间')
                    print('玩家a进入了房间')
                    if len(DATA['chatlog'])>5:
                        DATA['chatlog'].pop(0)
                    DATA['code'] = 'connected'
                    DATA['cuser'] = 'a'
                    await notify_users()

                elif DATA['b'] == 0:
                    DATA['b'] = 1
                    DATA['chatlog'].append('玩家b进入了房间')
                    print('玩家b进入了房间')
                    if len(DATA['chatlog']) > DATA['loglong']:
                        DATA['chatlog'].pop(0)

                    DATA['code'] = 'connected'
                    DATA['cuser'] = 'b'

                    await notify_users()
                else:
                    DATA['code'] = 'm'
                    DATA['cuser'] = 'm'
                    await notify_users()
            elif message == 'aexit':
                DATA['a'] = 0
                DATA['chatlog'].append('玩家a退出了房间')
                print('玩家a退出了房间')
                if len(DATA['chatlog']) > DATA['loglong']:
                    DATA['chatlog'].pop(0)

                DATA['code'] = 'exit'
                DATA['cuser'] = 'a'

                await reset_ginfo()
                await notify_users()
            elif message == 'bexit':
                DATA['b'] = 0
                DATA['chatlog'].append('玩家b退出了房间')
                print('玩家b退出了房间')
                if len(DATA['chatlog']) > DATA['loglong']:
                    DATA['chatlog'].pop(0)
                DATA['code'] = 'exit'
                DATA['cuser'] = 'b'

                await reset_ginfo()
                await notify_users()

            elif message == 'aready':
                if DATA['br'] ==1:
                    DATA['ar'] = 1
                    DATA['game_ing'] = 1
                    #双方都准备，直接开始游戏
                    DATA['chatlog'].append('双方准备完毕，游戏开始')
                    print('双方准备完毕，游戏开始')
                    if len(DATA['chatlog']) > DATA['loglong']:
                        DATA['chatlog'].pop(0)

                    DATA['code'] = 'startgame'
                    DATA['cuser'] = 'm'

                    await start_game()
                    await notify_users()

                else:
                    DATA['ar'] = 1
                    DATA['chatlog'].append('玩家a已准备进行游戏')
                    print('玩家a已准备进行游戏')
                    if len(DATA['chatlog']) > DATA['loglong']:
                        DATA['chatlog'].pop(0)
                    DATA['code'] = 'ready'
                    DATA['cuser'] = 'a'

                    await notify_users()


            elif message == 'bready':
                if DATA['ar'] == 1:
                    # 双方都准备，直接开始游戏
                    DATA['br'] = 1
                    DATA['game_ing'] = 1
                    DATA['chatlog'].append('双方准备完毕，游戏开始')

                    print('双方准备完毕，游戏开始')
                    if len(DATA['chatlog']) > DATA['loglong']:
                        DATA['chatlog'].pop(0)

                    DATA['code'] = 'startgame'
                    DATA['cuser'] = 'm'

                    await start_game()
                    await notify_users()

                else:
                    DATA['br'] = 1
                    DATA['chatlog'].append('玩家b已准备进行游戏')
                    print('玩家b已准备进行游戏')
                    if len(DATA['chatlog']) > DATA['loglong']:
                        DATA['chatlog'].pop(0)
                    DATA['code'] = 'ready'
                    DATA['cuser'] = 'b'

                    await notify_users()

            elif message == 'anotready':
                if DATA['game_ing'] ==1:
                    print('非法操作，游戏已开始，无法取消')
                else:
                    DATA['ar'] = 0
                    #双方都准备，直接开始游戏
                    DATA['chatlog'].append('玩家a取消准备')
                    print('玩家a取消准备')
                    if len(DATA['chatlog']) > DATA['loglong']:
                        DATA['chatlog'].pop(0)

                    DATA['code'] = 'notready'
                    DATA['cuser'] = 'a'

                    await notify_users()

            elif message == 'bnotready':
                if DATA['game_ing'] ==1:
                    print('非法操作，游戏已开始，无法取消')
                else:
                    DATA['br'] = 0
                    #双方都准备，直接开始游戏
                    DATA['chatlog'].append('玩家b取消准备')
                    print('玩家b取消准备')
                    if len(DATA['chatlog']) > DATA['loglong']:
                        DATA['chatlog'].pop(0)

                    DATA['code'] = 'notready'
                    DATA['cuser'] = 'b'

                    await notify_users()


            elif str(message).startswith('a:') or str(message).startswith('b:'):
                DATA['chatlog'].append(message)
                if len(DATA['chatlog']) > DATA['loglong']:
                    DATA['chatlog'].pop(0)
                DATA['code'] = 'chat'
                DATA['cuser'] = 'm'

                await notify_users()

            elif str(message) == 'mt':

                DATA['code'] = 'allexit'
                DATA['cuser'] = 'all'
                DATA['a'] = 0
                DATA['b'] = 0
                DATA['ar'] = 0
                DATA['br'] = 0
                DATA['game_ing'] = 0
                DATA['chatlog'] = []
                DATA['loglong'] = 5
                DATA['acount'] = 0
                DATA['bcount'] = 0
                DATA['turn'] = 'a'
                DATA['pan'] = []
                DATA['checkson'] = []
                DATA['pan_show'] = []
                DATA['overed'] = []

                await notify_users()

            elif str(message).startswith('check:'):

                index = str(message).split(':')[2]
                cuser = str(message).split(':')[1]

                if cuser==DATA['turn']:
                    if int(index) in DATA['overed'] or int(index) in DATA['checkson']:
                        # donothing
                        print('操作无效')
                    else:
                        if len(DATA['checkson']) == 0:
                            DATA['checkson'].append(int(index))
                            DATA['code'] = 'check'
                            DATA['cuser'] = cuser
                            # 显示盘反转指定牌
                            DATA['pan_show'][int(index)] = DATA['pan'][int(index)]
                        elif len(DATA['checkson']) == 1:
                            if int(index) == DATA['checkson'][0]:
                                # 如果点击相同的位置,没有反应
                                print('操作无效')
                            else:
                                DATA['checkson'].append(int(index))
                                DATA['code'] = 'check'
                                DATA['cuser'] = cuser
                                # 显示盘反转指定牌
                                DATA['pan_show'][int(index)] = DATA['pan'][int(index)]

                        await notify_users()

                        if len(DATA['checkson']) == 2:

                            # 如果校验的两个相等
                            if DATA['pan'][DATA['checkson'][0]] == DATA['pan'][DATA['checkson'][1]]:
                                DATA['code'] = 'check'
                                DATA['cuser'] = cuser
                                DATA[cuser + 'count'] = DATA[cuser + 'count'] + 1

                                # 加入完成组
                                DATA['overed'].append(DATA['checkson'][0])
                                DATA['overed'].append(DATA['checkson'][1])


                            else:
                                if cuser == 'a':
                                    DATA['turn'] = 'b'
                                else:
                                    DATA['turn'] = 'a'

                                # 不等则翻回去
                                DATA['code'] = 'check'
                                DATA['cuser'] = cuser
                                # # 显示盘牌面清空
                                DATA['pan_show'][DATA['checkson'][0]] = 'bg'
                                DATA['pan_show'][DATA['checkson'][1]] = 'bg'

                            DATA['checkson'] = []

                        time.sleep(1.5)
                        await notify_users()
                else:
                    print('非法操作')




            else:
                ld = {
                    'code':'nomessage'
                }
                await websocket.send(json.dumps(ld))

            print('服务端:'+str(DATA))
    except:
        print('用户意外断开链接')

    finally:
        print('用户断开链接')
        await unregister(websocket)


print('正在配置websocket-server基础信息')
HOST = 'localhost'
#HOST = '0.0.0.0'
wserver = websockets.serve(linker, HOST, 9999)
print('正在启动wserver')
asyncio.get_event_loop().run_until_complete(wserver
    )
print('启动成功,端口9999')
asyncio.get_event_loop().run_forever()

# -*- coding: utf-8 -*-
# @Time    : 19-6-3 下午4:53
# @Author  : Redtree
# @File    : r_server.py
# @Desc :


import asyncio
import json
import websockets


USERS = set()

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
    'loglong':5  #日志长度
}

async def reset():
    DATA['cuser']=''
    DATA['code']=''


async def notify_users():
    if USERS:       # asyncio.wait doesn't accept an empty list
        message = json.dumps(DATA)
        #发送后重置请求
        await reset()
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

                await notify_users()
            elif message == 'bexit':
                DATA['b'] = 0
                DATA['chatlog'].append('玩家b退出了房间')
                print('玩家b退出了房间')
                if len(DATA['chatlog']) > DATA['loglong']:
                    DATA['chatlog'].pop(0)
                DATA['code'] = 'exit'
                DATA['cuser'] = 'b'

                await notify_users()
            elif str(message).startswith('a:') or str(message).startswith('b:'):
                DATA['chatlog'].append(message)
                if len(DATA['chatlog']) > DATA['loglong']:
                    DATA['chatlog'].pop(0)
                DATA['code'] = 'chat'
                DATA['cuser'] = 'm'

                await notify_users()

            else:
                await websocket.send(message)

            print('服务端:'+str(DATA))
    except:
        print('用户意外断开链接')

    finally:
        print('用户断开链接')
        await unregister(websocket)


print('正在配置websocket-server基础信息')
wserver = websockets.serve(linker, '0.0.0.0', 9999)
print('正在启动wserver')
asyncio.get_event_loop().run_until_complete(wserver
    )
print('启动成功,端口9999')
asyncio.get_event_loop().run_forever()

# -*- coding: utf-8 -*-
# @Time    : 2021/7/21
# @Author  : hwkxk(丶大K丶)
# @Email   : k@hwkxk.cn
# Modified By liqman
## 新增多账号功能
## 新增pushplus、tgbot、钉钉机器人、企业微信机器人通知
## 新增早睡打卡任务申请
## 新增早睡打卡任务打卡(定时请定到晚8点以后此功能才生效)
## 新增抽奖开关

import requests, json, time, logging, traceback, hmac, hashlib, base64, urllib.parse, re


# 请配置该值 ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
## 推荐定时  30 0,20 * * *
## 早睡打卡瓜分积分开关，开启请填true,默认关闭
zaoshui_open = 'false'
## 抽奖开关，开启请填true,默认关闭
lottery_open = 'false'
## 下面HT_cookies_list、HT_UserAgent_list、notice_list请一一对应，notice_list某一行无通知可留空
## 填入APP抓取到Cookies,可以直接把抓包的全部cookie值填入，一个cookie一行
HT_cookies_list = [
    ''
]
## 填入抓取到User-Agent，参考以下 【建议使用自己抓取的！避免异常/防黑(推测）】
HT_UserAgent_list = [
    ''
]
## 填入推送方式及对应值
notice_list = [
    ['PUSHPLUS',''],  # 账号2  pushplus通知
]
# 请配置该值 ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑


# 用户登录全局变量
client = None
session = None
# 日志基础配置
# 创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# 创建一个handler，用于写入日志文件
# w 模式会记住上次日志记录的位置
fh = logging.FileHandler('../../tmp/log.txt', mode='a', encoding='utf-8')
fh.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(fh)
# 创建一个handler，输出到控制台
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("[%(asctime)s]:%(levelname)s:%(message)s"))
logger.addHandler(ch)


# 获取个人信息，判断登录状态
def get_infouser(HT_cookies, HT_UA):
    flag = False
    global session
    session = requests.Session()
    headers = {
        'Host': 'www.heytap.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
        'User-Agent': HT_UA,
        'Accept-Language': 'zh-cn',
        'Accept-Encoding': 'gzip, deflate, br',
        'cookie': HT_cookies
    }
    response = session.get('https://www.heytap.com/cn/oapi/users/web/member/info', headers=headers)
    response.encoding = 'utf-8'
    try:
        result = response.json()
        if result['code'] == 200:
            logger.info('==== 欢太商城任务 ====')
            logger.info('【登录成功】: ' + result['data']['realName'])
            flag = True
        else:
            logger.info('【登录失败】: ' + result['errorMessage'])
    except Exception as e:
        print(traceback.format_exc())
        logger.error('【登录】: 发生错误，原因为: ' + str(e))
    if flag:
        return session
    else:
        return False


# 活动平台抽奖通用接口
def lottery(datas):
    headers = {
        'clientPackage': 'com.oppo.store',
        'Accept': 'application/json, text/plain, */*;q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Encoding': 'gzip, deflate',
        'cookie': HT_cookies,
        'Origin': 'https://hd.oppo.com',
        'X-Requested-With': 'XMLHttpRequest',
    }
    res = client.post('https://hd.oppo.com/platform/lottery', data=datas, headers=headers)
    res = res.json()
    return res


# 任务中心列表，获取任务及任务状态
def taskCenter():
    headers = {
        'Host': 'store.oppo.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Language': 'zh-cn',
        'Accept-Encoding': 'gzip, deflate, br',
        'cookie': HT_cookies,
        'referer': 'https://store.oppo.com/cn/app/taskCenter/index'
    }
    res1 = client.get('https://store.oppo.com/cn/oapi/credits/web/credits/show', headers=headers)
    res1 = res1.json()
    return res1


# 活动平台完成任务接口
def task_finish(aid, t_index):
    headers = {
        'Accept': 'application/json, text/plain, */*;q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Encoding': 'gzip, deflate',
        'cookie': HT_cookies,
        'Origin': 'https://hd.oppo.com',
        'X-Requested-With': 'XMLHttpRequest',
    }
    datas = "aid=" + str(aid) + "&t_index=" + str(t_index)
    res = client.post('https://hd.oppo.com/task/finish', data=datas, headers=headers)
    res = res.json()
    return res


# 活动平台领取任务奖励接口
def task_award(aid, t_index):
    headers = {
        'Accept': 'application/json, text/plain, */*;q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Encoding': 'gzip, deflate',
        'cookie': HT_cookies,
        'Origin': 'https://hd.oppo.com',
        'X-Requested-With': 'XMLHttpRequest',
    }
    datas = "aid=" + str(aid) + "&t_index=" + str(t_index)
    res = client.post('https://hd.oppo.com/task/award', data=datas, headers=headers)
    res = res.json()
    return res


# 每日签到
# 位置: APP → 我的 → 签到
def daySign_task():
    try:
        dated = time.strftime("%Y-%m-%d")
        headers = {
            'Host': 'store.oppo.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'User-Agent': HT_UserAgent,
            'Accept-Language': 'zh-cn',
            'Accept-Encoding': 'gzip, deflate, br',
            'cookie': HT_cookies,
            'referer': 'https://store.oppo.com/cn/app/taskCenter/index'
        }
        res = taskCenter()
        status = res['data']['userReportInfoForm']['status']
        if status == 0:
            res = res['data']['userReportInfoForm']['gifts']
            for data in res:
                if data['date'] == dated:
                    qd = data
            if qd['today'] == False:
                data = "amount=" + str(qd['credits'])
                res1 = client.post('https://store.oppo.com/cn/oapi/credits/web/report/immediately', headers=headers,
                                   data=data)
                res1 = res1.json()
                if res1['code'] == 200:
                    logger.info('【每日签到成功】: ' + res1['data']['message'])
                else:
                    logger.info('【每日签到失败】: ' + str(res1))
            else:
                # print(str(qd['credits']), str(qd['type']), str(qd['gift']))
                if len(qd['type']) == 0:
                    data = "amount=" + str(qd['credits'])
                else:
                    data = "amount=" + str(qd['credits']) + "&type=" + str(qd['type']) + "&gift=" + str(qd['gift'])
                res1 = client.post('https://store.oppo.com/cn/oapi/credits/web/report/immediately', headers=headers,
                                   data=data)
                res1 = res1.json()
                if res1['code'] == 200:
                    logger.info('【每日签到成功】: ' + res1['data']['message'])
                else:
                    logger.info('【每日签到失败】: ' + str(res1))
        else:
            logger.info('【每日签到】: 已经签到过了！')
        time.sleep(1)
    except Exception as e:
        print(traceback.format_exc())
        logging.error('【每日签到】: 错误，原因为: ' + str(e))


# 浏览商品 10个sku +20 分
# 位置: APP → 我的 → 签到 → 每日任务 → 浏览商品
def daily_viewgoods():
    try:
        headers = {
            'clientPackage': 'com.oppo.store',
            'Host': 'msec.opposhop.cn',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'User-Agent': 'okhttp/3.12.12.200sp1',
            'Accept-Encoding': 'gzip',
            'cookie': HT_cookies,
        }
        res = taskCenter()
        res = res['data']['everydayList']
        for data in res:
            if data['name'] == '浏览商品':
                qd = data
        if qd['completeStatus'] == 0:
            shopList = client.get('https://msec.opposhop.cn/goods/v1/SeckillRound/goods/3016?pageSize=12&currentPage=1')
            res = shopList.json()
            if res['meta']['code'] == 200:
                for skuinfo in res['detail']:
                    skuid = skuinfo['skuid']
                    print('正在浏览商品ID：', skuid)
                    client.get('https://msec.opposhop.cn/goods/v1/info/sku?skuId=' + str(skuid), headers=headers)
                    time.sleep(5)
                res2 = cashingCredits(qd['marking'], qd['type'], qd['credits'])
                if res2 == True:
                    logger.info('【每日浏览商品】: ' + '任务完成！积分领取+' + str(qd['credits']))
                else:
                    logger.info('【每日浏览商品】: ' + "领取积分奖励出错！")
            else:
                logger.info('【每日浏览商品】: ' + '错误，获取商品列表失败')
        elif qd['completeStatus'] == 1:
            res2 = cashingCredits(qd['marking'], qd['type'], qd['credits'])
            if res2 == True:
                logger.info('【每日浏览商品】: ' + '任务完成！积分领取+' + str(qd['credits']))
            else:
                logger.info('【每日浏览商品】: ' + '领取积分奖励出错！')
        else:
            logger.info('【每日浏览商品】: ' + '任务已完成！')
    except Exception as e:
        print(traceback.format_exc())
        logging.error('【每日浏览任务】: 错误，原因为: ' + str(e))


def daily_sharegoods():
    try:
        headers = {
            'clientPackage': 'com.oppo.store',
            'Host': 'msec.opposhop.cn',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'User-Agent': 'okhttp/3.12.12.200sp1',
            'Accept-Encoding': 'gzip',
            'cookie': HT_cookies,
        }
        daySignList = taskCenter()
        res = daySignList
        res = res['data']['everydayList']
        for data in res:
            if data['name'] == '分享商品到微信':
                qd = data
        if qd['completeStatus'] == 0:
            count = qd['readCount']
            endcount = qd['times']
            while (count <= endcount):
                client.get('https://msec.opposhop.cn/users/vi/creditsTask/pushTask?marking=daily_sharegoods',
                           headers=headers)
                count += 1
            res2 = cashingCredits(qd['marking'], qd['type'], qd['credits'])
            if res2 == True:
                logger.info('【每日分享商品】: ' + '任务完成！积分领取+' + str(qd['credits']))
            else:
                logger.info('【每日分享商品】: ' + '领取积分奖励出错！')
        elif qd['completeStatus'] == 1:
            res2 = cashingCredits(qd['marking'], qd['type'], qd['credits'])
            if res2 == True:
                logger.info('【每日分享商品】: ' + '任务完成！积分领取+' + str(qd['credits']))
            else:
                logger.info('【每日分享商品】: ' + '领取积分奖励出错！')
        else:
            logger.info('【每日分享商品】: ' + '任务已完成！')
    except Exception as e:
        print(traceback.format_exc())
        logging.error('【每日分享商品】: 错误，原因为: ' + str(e))


def daily_viewpush():
    try:
        headers = {
            'clientPackage': 'com.oppo.store',
            'Host': 'msec.opposhop.cn',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'User-Agent': 'okhttp/3.12.12.200sp1',
            'Accept-Encoding': 'gzip',
            'cookie': HT_cookies,
        }
        daySignList = taskCenter()
        res = daySignList
        res = res['data']['everydayList']
        for data in res:
            if data['name'] == '点推送消息':
                qd = data
        if qd['completeStatus'] == 0:
            count = qd['readCount']
            endcount = qd['times']
            while (count <= endcount):
                client.get('https://msec.opposhop.cn/users/vi/creditsTask/pushTask?marking=daily_viewpush',
                           headers=headers)
                count += 1
            res2 = cashingCredits(qd['marking'], qd['type'], qd['credits'])
            if res2 == True:
                logger.info('【每日点推送】: ' + '任务完成！积分领取+' + str(qd['credits']))
            else:
                logger.info('【每日点推送】: ' + '领取积分奖励出错！')
        elif qd['completeStatus'] == 1:
            res2 = cashingCredits(qd['marking'], qd['type'], qd['credits'])
            if res2 == True:
                logger.info('【每日点推送】: ' + '任务完成！积分领取+' + str(qd['credits']))
            else:
                logger.info('【每日点推送】: ' + '领取积分奖励出错！')
        else:
            logger.info('【每日点推送】: ' + '任务已完成！')
    except Exception as e:
        print(traceback.format_exc())
        logging.error('【每日推送消息】: 错误，原因为: ' + str(e))


# 执行完成任务领取奖励
def cashingCredits(info_marking, info_type, info_credits):
    headers = {
        'Host': 'store.oppo.com',
        'clientPackage': 'com.oppo.store',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Language': 'zh-cn',
        'Accept-Encoding': 'gzip, deflate, br',
        'cookie': HT_cookies,
        'Origin': 'https://store.oppo.com',
        'X-Requested-With': 'com.oppo.store',
        'referer': 'https://store.oppo.com/cn/app/taskCenter/index?us=gerenzhongxin&um=hudongleyuan&uc=renwuzhongxin'
    }

    data = "marking=" + str(info_marking) + "&type=" + str(info_type) + "&amount=" + str(info_credits)
    res = client.post('https://store.oppo.com/cn/oapi/credits/web/credits/cashingCredits', data=data, headers=headers)
    res = res.json()
    if res['code'] == 200:
        return True
    else:
        return False

def zaoshui_task():
    try:
        headers = {
            'Host':'store.oppo.com',
            'Connection':'keep-alive',
            's_channel':'huawei',
            'utm_term':'direct',
            'utm_campaign':'direct',
            'utm_source':'direct',
            'ut':'direct',
            'uc':'zaoshuidaka',
            'guid':'',
            'clientPackage':'com.oppo.store',
            'Cache-Control':'no-cache',
            'um':'hudongleyuan',
            'User-Agent': HT_UserAgent,
            'ouid':'',
            'Accept':'application/json, text/plain, */*',
            'source_type':'501',
            'utm_medium':'direct',
            'appId':'',
            's_version':'200804',
            'us':'gerenzhongxin',
            'appKey':'',
            'X-Requested-With':'com.oppo.store',
            'Sec-Fetch-Site':'same-origin',
            'Sec-Fetch-Mode':'cors',
            'Sec-Fetch-Dest':'empty',
            'Referer':'https://store.oppo.com/cn/app/cardingActivities?us=gerenzhongxin&um=hudongleyuan&uc=zaoshuidaka',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'cookie': HT_cookies,
        }

        if time.localtime(time.time())[3] <= 18:
            response = client.get('https://store.oppo.com/cn/oapi/credits/web/clockin/applyOrClockIn',headers=headers)
            # is_apply = '"everydayDate":"' + time.strftime("%Y-%m-%d",time.localtime()) + '"' + ',"applyClockInStatus":"报名成功"'
            if json.loads(response.text)['code'] == 200:
                logger.info('【早睡打卡】申请成功')
            if json.loads(response.text)['code'] == 1000005:
                logger.info('【早睡打卡】积分不足，申请失败')
        if time.localtime(time.time())[3] >= 20:
            is_apply = '"everydayDate":"' + time.strftime("%Y-%m-%d", time.localtime()) + '"' + ',"applyClockInStatus":"报名成功"'
            response = client.get('https://store.oppo.com/cn/oapi/credits/web/clockin/applyOrClockIn', headers=headers)
            response_record = client.get('https://store.oppo.com/cn/oapi/credits/web/clockin/getMyRecord',headers=headers)
            if re.search(is_apply,response_record.text) is not None and json.loads(response.text)['code'] == 200:
                logger.info('【早睡打卡】打卡成功')
            if re.search(is_apply,response_record.text) is None:
                logger.info('【早睡打卡】未报名打卡')
    except Exception as e:
        print(traceback.format_exc())
        logging.error('【早睡打卡】: 错误，原因为: ' + str(e))

def zhuanjifen_task():
    headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Encoding': 'gzip, deflate',
        'cookie': HT_cookies,
        'X-Requested-With': 'XMLHttpRequest',
        'referer': 'https://hd.oppo.com/act/m/2021/jifenzhuanpan/index.html?us=gerenzhongxin&um=hudongleyuan&uc=yingjifen'
    }
    data = "aid=1418&lid=1307&mobile=&authcode=&captcha=&isCheck=0&source_type=501&s_channel=oppo_appstore&sku=&spu="
    res = lottery(data)
    # print(res)
    goods_name = res['data']['goods_name']
    # msg = res['msg']
    if goods_name == '':
        logger.info('【赚积分-天天抽奖】获得:未中奖')
    else:
        logger.info('【赚积分-天天抽奖】获得:' + str(goods_name))
    taskList = client.get('https://hd.oppo.com/task/list?aid=1418', headers=headers)
    taskList = taskList.json()
    for i, jobs in enumerate(taskList['data']):
        # print(jobs['t_status'])  # print (jobs.get('t_index'))
        if jobs['t_status'] == 0:
            t_index = jobs['t_index']
            aid = t_index[:t_index.index("i")]
            finishmsg = task_finish(aid, t_index)
            if finishmsg['no'] == 200:
                time.sleep(1)
                awardmsg = task_award(aid, t_index)
                if awardmsg['no'] == 200:
                    res = lottery(data)
                    # msg = res['msg']
                    # print(msg)
                    goods_name = res['data']['goods_name']
                    if goods_name == '':
                        logger.info('【赚积分-天天抽奖】获得:未中奖')
                    else:
                        logger.info('【赚积分-天天抽奖】获得:' + str(goods_name))
                    time.sleep(3)
                else:
                    print('领取奖励出错：', awardmsg)
            else:
                print('完成任务出错：', finishmsg)
        elif jobs['t_status'] == 1:
            t_index = jobs['t_index']
            aid = t_index[:t_index.index("i")]
            awardmsg = task_award(aid, t_index)
            # print(awardmsg['no'])
            if awardmsg['no'] == 200:
                res = lottery(data)
                msg = res['msg']
                print(msg)
                goods_name = res['data']['goods_name']
                logger.info('【赚积分-天天抽奖】获得:' + str(goods_name))
                time.sleep(3)
            else:
                print('领取奖励出错：', awardmsg)

# 天天积分翻倍活动 - 长期 最多3次
def tiantianjifen_lottery():
    x = 1
    while x <= 3:
        data = "aid=675&lid=1289&mobile=&authcode=&captcha=&isCheck=0&source_type=501&s_channel=oppo_appstore&sku=&spu="
        res = lottery(data)
        # msg = res['msg']
        # print(msg)
        goods_name = res['data']['goods_name']
        if goods_name == '':
            logger.info('【天天积分翻倍活动】第' + str(x) + '次，未中奖')
        else:
            logger.info('【天天积分翻倍活动】第' + str(x) + '次，获得:' + str(goods_name))
        x += 1
        time.sleep(5)


# realme宠粉计划-幸运抽奖-转盘
def realme_lottery():
    data = "aid=1182&lid=1429&mobile=&authcode=&captcha=&isCheck=0&source_type=501&s_channel=oppo_appstore&sku=&spu="
    res = lottery(data)
    msg = res['msg']
    print(msg)
    goods_name = res['data']['goods_name']
    if goods_name == '':
        logger.info('【realme宠粉计划转盘】未中奖')
    else:
        logger.info('【realme宠粉计划转盘】获得:' + str(goods_name))
    time.sleep(3)


def zhinengshenghuo_lottery():
    x = 1
    while x <= 5:
        data = "aid=1270&lid=1431&mobile=&authcode=&captcha=&isCheck=0&source_type=501&s_channel=oppo_appstore&sku=&spu="
        res = lottery(data)
        msg = res['msg']
        print(msg)
        goods_name = res['data']['goods_name']
        if goods_name == '':
            logger.info('【智能生活转盘】未中奖')
        else:
            logger.info('【智能生活转盘】第' + str(x) + '次，获得:' + str(goods_name))
        x += 1
        time.sleep(5)


#位置: APP → 首页 → 狂撒百万积分
def jifenpengzhang_task():
    dated = int(time.time())
    endtime = time.mktime(time.strptime("2021-7-31 23:59:59", '%Y-%m-%d %H:%M:%S'))#设置活动结束日期
    if dated < endtime :
        headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Encoding': 'gzip, deflate',
        'cookie': HT_cookies,
        'X-Requested-With': 'XMLHttpRequest',
        'referer':'https://hd.oppo.com/act/m/2021/jifenzhuanpan/index.html?us=gerenzhongxin&um=hudongleyuan&uc=yingjifen'
        }
        data = "aid=1594&lid=1482&mobile=&authcode=&captcha=&isCheck=0&source_type=501&s_channel=oppo_appstore&sku=&spu="
        res = lottery(data)
        print(res)
        goods_name = res['data']['goods_name']
        msg = res['msg']
        if len(goods_name) == 0 or goods_name == '':
            logger.info('【狂撒百万积分-转盘】: 未中奖！')
        else:
            logger.info('【狂撒百万积分-转盘】获得:'+ str(goods_name))
        taskList=client.get('https://hd.oppo.com/task/list?aid=1594', headers=headers)
        taskList=taskList.json()
        time.sleep(3)
        for jobs in taskList['data']:
            print (jobs['t_status'],jobs['title'],jobs['t_index']) #print (jobs.get('t_index'))
            if jobs['t_status'] == 0:
                t_index=jobs['t_index']
                aid=t_index[:t_index.index("i")]
                title=jobs['title']
                finishmsg=task_finish (aid,t_index)
                if finishmsg['no'] == '200':
                    time.sleep(3)
                    awardmsg=task_award(aid,t_index)
                    if awardmsg['no'] == '200':
                        msg = awardmsg['msg']
                        print(msg)
                        logger.info('【狂撒百万积分-'+ str(title) +'】:'+ str(msg))
                        time.sleep(3)
                    else:
                        print('领取奖励出错：', awardmsg)
                else:
                    print('完成任务出错：', finishmsg)
            elif jobs['t_status'] == 1:
                t_index=jobs['t_index']
                aid=t_index[:t_index.index("i")]
                title=jobs['title']
                awardmsg=task_award(aid,t_index)
                if awardmsg['no'] == '200':
                    msg = awardmsg['msg']
                    print(msg)
                    logger.info('【狂撒百万积分-'+ str(title) +'】:'+ str(msg))
                    time.sleep(3)
                else:
                    print('领取奖励出错：', awardmsg)
    else:
        logger.info('【狂撒百万积分活动已结束，不再执行】')
    time.sleep(3)


#位置: APP → OPPO → 0元赢积分
def oppo0yuanzhuanjifen_task():
    dated = int(time.time())
    endtime = time.mktime(time.strptime("2021-7-31 23:59:59", '%Y-%m-%d %H:%M:%S'))#设置活动结束日期
    if dated < endtime :
        headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'User-Agent': HT_UserAgent,
        'Accept-Encoding': 'gzip, deflate',
        'cookie': HT_cookies,
        'X-Requested-With': 'XMLHttpRequest',
        'referer':'https://hd.oppo.com/act/m/2021/oppozhuanjifen/index.html?us=oppochannel&um=zhuanjifen'
        }
        data = "aid=1618&lid=1495&mobile=&authcode=&captcha=&isCheck=0&source_type=501&s_channel=oppo_appstore&sku=&spu="
        res = lottery(data)
        print(res)
        goods_name = res['data']['goods_name']
        msg = res['msg']
        if len(goods_name) == 0 or goods_name == '':
            logger.info('【OPPO0元赚积分-转盘】: 未中奖！')
        else:
            logger.info('【OPPO0元赚积分-转盘】获得:'+ str(goods_name))
        time.sleep(3)
        taskList=client.get('https://hd.oppo.com/task/list?aid=1618', headers=headers)
        taskList=taskList.json()
        for jobs in taskList['data']:
            print (jobs['t_status'],jobs['title'],jobs['t_index']) #print (jobs.get('t_index'))
            if jobs['t_status'] == 0:
                t_index=jobs['t_index']
                aid=t_index[:t_index.index("i")]
                finishmsg=task_finish (aid,t_index)
                if finishmsg['no'] == '200':
                    time.sleep(3)
                    awardmsg=task_award(aid,t_index)
                    if awardmsg['no'] == '200':
                        time.sleep(3)
                        res = lottery(data)
                        msg = res['msg']
                        print(msg)
                        goods_name = res['data']['goods_name']
                        if len(goods_name) == 0:
                            logger.info('【OPPO0元赚积分-转盘】: 未中奖！')
                        else:
                            logger.info('【OPPO0元赚积分-转盘】获得:'+ str(goods_name))
                        time.sleep(3)
                    else:
                        print('领取奖励出错：', awardmsg)
                else:
                    print('完成任务出错：', finishmsg)
            elif jobs['t_status'] == 1:
                t_index=jobs['t_index']
                aid=t_index[:t_index.index("i")]
                awardmsg=task_award(aid,t_index)
                if awardmsg['no'] == '200':
                    time.sleep(3)
                    res = lottery(data)
                    msg = res['msg']
                    print(msg)
                    goods_name = res['data']['goods_name']
                    if len(goods_name) == 0:
                        logger.info('【OPPO0元赚积分-转盘】: 未中奖！')
                    else:
                        logger.info('【OPPO0元赚积分-转盘】获得:'+ str(goods_name))
                    time.sleep(3)
                else:
                    print('领取奖励出错：', awardmsg)
    else:
        logger.info('【OPPO0元赚积分活动已结束，不再执行】')
    time.sleep(3)


def readFile_html(filepath):
    content = ''
    with open(filepath, "r" , encoding='utf-8') as f:
        for line in f.readlines():
            content += line + '<br>'
    return content

def readFile(filepath):
    content = ''
    with open(filepath, encoding='utf-8') as f:
        for line in f.readlines():
            content += line + '\n\n'
    return content

def readFile_text(filepath):
    content = ''
    with open(filepath, encoding='utf-8') as f:
        for line in f.readlines():
            content += line
    return content

# 通知函数 含pushplus、tgbot、钉钉机器人、企业微信机器人通知
def sendmessage(notice):
    if notice[0] == '':
        pass
    if notice[0] == 'PUSHPLUS':
        try:
            # 发送内容
            data = {
                "token": notice[1],
                "title": "HeytapTask每日报表",
                "content": readFile_html('../../tmp/log.txt')
            }
            url = 'http://www.pushplus.plus/send'
            headers = {'Content-Type': 'application/json'}
            body = json.dumps(data).encode(encoding='utf-8')
            resp = requests.post(url, data=body, headers=headers)
        except Exception as e:
            print('push+通知推送异常，原因为: ' + str(e))
            print(traceback.format_exc())
    if notice[0] == 'DDBOT':
        try:
            content = readFile('../../tmp/log.txt')
            data = {
                'msgtype': 'markdown',
                'markdown': {
                    'title': 'HeytapTask每日报表',
                    'text': content
                }
            }
            headers = {
                'Content-Type': 'application/json;charset=utf-8'
            }
            timestamp = str(round(time.time() * 1000))
            secret_enc = notice[1].split('@')[1].encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, notice[1].split('@')[1])
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            print('https://oapi.dingtalk.com/robot/send?access_token=' + notice[1])
            # res = requests.post('https://oapi.dingtalk.com/robot/send?access_token='+notice_type[1], headers=headers, json=data)
            res = requests.post('https://oapi.dingtalk.com/robot/send?access_token={}&timestamp={}&sign={}'.format(
                notice[1].split('@')[0], timestamp, sign), json=data, headers=headers)
            res.encoding = 'utf-8'
            res = res.json()
            print('dinngTalk push : ' + res['errmsg'])
        except Exception as e:
            print('钉钉机器人推送异常，原因为: ' + str(e))
            print(traceback.format_exc())
    if notice[0] == 'TGBOT':
        try:
            token = notice[1].split('@')[0]
            chat_id = notice[1].split('@')[1]
            # 发送内容
            content = readFile_text('../../tmp/log.txt')
            data = {
                'HeytapTask每日报表': content
            }
            content = urllib.parse.urlencode(data)
            url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={content}'
            session = requests.Session()
            resp = session.post(url)
            print(resp)
        except Exception as e:
            print('Tg通知推送异常，原因为: ' + str(e))
            print(traceback.format_exc())
    if notice[0] == 'QYWX':
        try:
            content = readFile_text('../../tmp/log.txt')
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=' + notice[1]
            print(url)
            res = requests.post(url, json=data)
            res.encoding = 'utf-8'
            res = res.json()
            print('企业微信 : ' + res['errmsg'])
        except Exception as e:
            print('企业微信机器人通知推送异常，原因为: ' + str(e))
            print(traceback.format_exc())

# 函数入口
def main(event, context):
    global client
    global HT_cookies
    global HT_UserAgent
    num = len(HT_cookies_list)
    for i in range(num):
        # 清空上一个用户的日志记录
        open('../../tmp/log.txt', mode='w', encoding='utf-8')
        HT_cookies = HT_cookies_list[i]
        HT_UserAgent = HT_UserAgent_list[i]
        client = get_infouser(HT_cookies, HT_UserAgent)

        # 如果不想做特定任务可以手动注释
        if client != False:
            daySign_task()  # 执行每日签到
            daily_viewgoods()  # 执行每日商品浏览任务
            daily_sharegoods()  # 执行每日商品分享任务
            daily_viewpush()  # 执行每日点推送任务
            if lottery_open == 'true':
                tiantianjifen_lottery()  # 天天积分翻倍
                zhuanjifen_task()  # 我的-赚积分-转盘
                zhinengshenghuo_lottery()  # 智能生活-0元抽奖-宠粉转盘 可能此活动中奖率低！返回空白是正常
                realme_lottery()  # realme宠粉计划 转盘
            if zaoshui_open == 'true':
                zaoshui_task()  # 早睡打卡
        sendmessage(notice_list[i])


# 主函数入口
if __name__ == '__main__':
    main("", "")

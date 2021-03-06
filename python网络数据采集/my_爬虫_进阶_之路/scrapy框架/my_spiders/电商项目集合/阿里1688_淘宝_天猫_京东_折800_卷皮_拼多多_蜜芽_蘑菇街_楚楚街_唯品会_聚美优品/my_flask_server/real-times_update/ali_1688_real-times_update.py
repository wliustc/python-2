# coding:utf-8

'''
@author = super_fazai
@File    : ali_1688_real-times_update.py
@Time    : 2017/10/28 07:24
@connect : superonesfazai@gmail.com
'''
import sys
sys.path.append('..')

from ali_1688_parse import ALi1688LoginAndParse
from my_pipeline import SqlServerMyPageInfoSaveItemPipeline

import gc
from time import sleep
from settings import IS_BACKGROUND_RUNNING

from fzutils.time_utils import (
    get_shanghai_time,
)
from fzutils.linux_utils import daemon_init
from fzutils.cp_utils import (
    _get_price_change_info,
    get_shelf_time_and_delete_time,
)

def run_forever():
    while True:
        #### 实时更新数据
        tmp_sql_server = SqlServerMyPageInfoSaveItemPipeline()
        # and GETDATE()-ModfiyTime>1
        sql_str = '''
        select GoodsID, IsDelete, Price, TaoBaoPrice, shelf_time, delete_time
        from dbo.GoodsInfoAutoGet 
        where SiteID=2 and MainGoodsID is not null and GETDATE()-ModfiyTime>1
        '''

        try:
            result = list(tmp_sql_server._select_table(sql_str=sql_str))
        except TypeError as e:
            print('TypeError错误, 原因数据库连接失败...(可能维护中)')
            result = None
        if result is None:
            pass
        else:
            print('------>>> 下面是数据库返回的所有符合条件的goods_id <<<------')
            print(result)
            print('--------------------------------------------------------')

            print('即将开始实时更新数据, 请耐心等待...'.center(100, '#'))
            index = 1
            # 释放内存,在外面声明就会占用很大的，所以此处优化内存的方法是声明后再删除释放
            ali_1688 = ALi1688LoginAndParse()
            for item in result:  # 实时更新数据
                if index % 5 == 0:
                    ali_1688 = ALi1688LoginAndParse()

                if index % 50 == 0:    # 每50次重连一次，避免单次长连无响应报错
                    print('正在重置，并与数据库建立新连接中...')
                    # try:
                    #     del tmp_sql_server
                    # except:
                    #     pass
                    # gc.collect()
                    tmp_sql_server = SqlServerMyPageInfoSaveItemPipeline()
                    print('与数据库的新连接成功建立...')

                if tmp_sql_server.is_connect_success:
                    print('------>>>| 正在更新的goods_id为(%s) | --------->>>@ 索引值为(%d)' % (item[0], index))
                    data = ali_1688.get_ali_1688_data(item[0])
                    if isinstance(data, int) is True:     # 单独处理返回tt为4041
                        continue
                    else:
                        pass

                    if data.get('is_delete') == 1:        # 单独处理【原先插入】就是 下架状态的商品
                        data['goods_id'] = item[0]

                        data['shelf_time'], data['delete_time'] = get_shelf_time_and_delete_time(
                            tmp_data=data,
                            is_delete=item[1],
                            shelf_time=item[4],
                            delete_time=item[5]
                        )
                        print('上架时间:',data['shelf_time'], '下架时间:', data['delete_time'])

                        # print('------>>>| 爬取到的数据为: ', data)
                        ali_1688.to_right_and_update_data(data, pipeline=tmp_sql_server)

                        sleep(1.5)  # 避免服务器更新太频繁
                        index += 1
                        gc.collect()
                        continue

                    data = ali_1688.deal_with_data()
                    if data != {}:
                        data['goods_id'] = item[0]
                        data['shelf_time'], data['delete_time'] = get_shelf_time_and_delete_time(
                            tmp_data=data,
                            is_delete=item[1],
                            shelf_time=item[4],
                            delete_time=item[5]
                        )
                        print('上架时间:',data['shelf_time'], '下架时间:', data['delete_time'])

                        '''为了实现这个就必须保证price, taobao_price在第一次抓下来后一直不变，变得记录到_price_change_info字段中'''
                        # 业务逻辑
                        #   公司后台 modify_time > 转换时间，is_price_change=1, 然后对比pricechange里面的数据，要是一样就不提示平台员工改价格
                        data['_is_price_change'], data['_price_change_info'] = _get_price_change_info(
                            old_price=item[2],
                            old_taobao_price=item[3],
                            new_price=data['price'],
                            new_taobao_price=data['taobao_price']
                        )

                        # print('------>>>| 爬取到的数据为: ', data)
                        ali_1688.to_right_and_update_data(data, pipeline=tmp_sql_server)

                        sleep(.3)       # 避免服务器更新太频繁
                    else:  # 表示返回的data值为空值
                        pass
                else:  # 表示返回的data值为空值
                    print('数据库连接失败，数据库可能关闭或者维护中')
                    pass
                index += 1
                # try:
                #     del ali_1688
                # except:
                #     pass
                gc.collect()
                sleep(2.2)
            print('全部数据更新完毕'.center(100, '#'))  # sleep(60*60)
        if get_shanghai_time().hour == 0:   # 0点以后不更新
            sleep(60*60*5.5)
        else:
            sleep(5)
        # del ali_1688
        gc.collect()

def main():
    '''
    这里的思想是将其转换为孤儿进程，然后在后台运行
    :return:
    '''
    print('========主函数开始========')  # 在调用daemon_init函数前是可以使用print到标准输出的，调用之后就要用把提示信息通过stdout发送到日志系统中了
    daemon_init()  # 调用之后，你的程序已经成为了一个守护进程，可以执行自己的程序入口了
    print('--->>>| 孤儿进程成功被init回收成为单独进程!')
    # time.sleep(10)  # daemon化自己的程序之后，sleep 10秒，模拟阻塞
    run_forever()

if __name__ == '__main__':
    if IS_BACKGROUND_RUNNING:
        main()
    else:
        run_forever()

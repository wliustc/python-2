# coding:utf-8

'''
@author = super_fazai
@File    : just_fuck_run_tmall.py
@Time    : 2018/4/17 14:01
@connect : superonesfazai@gmail.com
'''

import sys
sys.path.append('..')

from time import sleep
import os

from fzutils.time_utils import (
    get_shanghai_time,
)
from fzutils.linux_utils import (
    daemon_init,
    process_exit,
    kill_process_by_name,
)

tejia_file_name_list = [
    # 'taobao_tiantiantejia',
    # 'taobao_tiantiantejia_real-times_update',
]

spike_file_name_list = [
    'taobao_qianggou_spike',
    'taobao_qianggou_miaosha_real-times_update',
]

real_file_name_list = [
    'tmall_real-times_update',
]

logs_file_name_list = [
    'expired_logs_deal_with',
]

server_file_name_list = [
    'new_my_server',
]

def run_one_file_name_list(path, file_name_list):
    for item in file_name_list:
        process_name = item + '.py'
        if process_exit(process_name) == 0:
            # 如果对应的脚本没有在运行, 则运行之
            os.system('cd {0} && python3 {1}.py'.format(path, item))
            sleep(2.5)  # 避免同时先后启动先sleep下
        else:
            print(process_name + '脚本已存在!')

def auto_run(*params):
    print('开始执行脚本'.center(60, '*'))

    run_one_file_name_list(path=params[0], file_name_list=tejia_file_name_list)
    run_one_file_name_list(path=params[1], file_name_list=logs_file_name_list)
    run_one_file_name_list(path=params[3], file_name_list=server_file_name_list)

    if str(get_shanghai_time())[11:13] in ['21', '22', '23', '04', '05', '06', '07', '08',]:
        # kill冲突进程
        [kill_process_by_name(process_name) for process_name in spike_file_name_list[1:]]   # 不杀spike
        # 运行tmall常规商品更新script
        run_one_file_name_list(path=params[2], file_name_list=real_file_name_list)

    # 无法运行成守护进程, 改为tmux模式运行
    if str(get_shanghai_time())[11:13] in ['00', '01', '02', '03', '09', '10']:     # 白天不运行tmall更新，9点即时杀掉
        # 单独运行淘抢购抓取script
        [kill_process_by_name(process_name) for process_name in real_file_name_list]
        # [kill_process_by_name(process_name) for process_name in spike_file_name_list[1:]]
        # run_one_file_name_list(path=params[4], file_name_list=[spike_file_name_list[0]])

    # 并且不运行更新脚本，只运行spike
    # if str(get_shanghai_time())[11:13] in ['13', '14', '15', '16', '17']:
    #     [kill_process_by_name(process_name) for process_name in real_file_name_list]
    #     [kill_process_by_name(process_name) for process_name in spike_file_name_list[0:1]+spike_file_name_list[2:]]
    #     # 单独运行淘抢购更新script
    #     run_one_file_name_list(path=params[4], file_name_list=[spike_file_name_list[1]])

    print('脚本执行完毕'.center(60, '*'))

def main_2():
    while True:
        tejia_path = '~/myFiles/python/my_flask_server/tejia'
        logs_path = '~/myFiles/python/my_flask_server/logs'
        real_path = '~/myFiles/python/my_flask_server/real-times_update'
        server_path = '~/myFiles/python/my_flask_server'
        spike_path = '~/myFiles/python/my_flask_server/spike_everything'

        auto_run(tejia_path, logs_path, real_path, server_path, spike_path)
        print(' Money is on the way! '.center(100, '*'))

        sleep(5*60)

def main():
    '''
    这里的思想是将其转换为孤儿进程，然后在后台运行
    :return:
    '''
    print('========主函数开始========')  # 在调用daemon_init函数前是可以使用print到标准输出的，调用之后就要用把提示信息通过stdout发送到日志系统中了
    daemon_init()  # 调用之后，你的程序已经成为了一个守护进程，可以执行自己的程序入口了
    print('--->>>| 孤儿进程成功被init回收成为单独进程!')
    # time.sleep(10)  # daemon化自己的程序之后，sleep 10秒，模拟阻塞
    main_2()


if __name__ == '__main__':
    main()
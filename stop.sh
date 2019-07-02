#!/bin/bash
# Program:
# 用于停止本项目的进程
# 由于使用了多进程，暂时无法通过ctrl+c的方式停止程序，因此需要从
# 外部强制结束所有和本项目相关的程序
# History: 2019/06/29 izhangxm first release

ps -ef | grep "python manage.py runserver 0.0.0.0:9001 --noreload" | grep -v 'grep' | awk '{print $2}' | xargs -I{} kill -9 {}
echo 'finished!'

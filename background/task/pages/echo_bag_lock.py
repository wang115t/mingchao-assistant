# -*- coding: utf-8 -*-
"""
@software: PyCharm
@file: database_echo.py
@time: 2024/6/20 下午9:53
@author RoseRin0
"""
import time

from . import *
import sys

pages = []


def echo_bag(positions: dict[str, Position]) -> bool:
    """
    提示
    :param positions:
    :return:
    """
    if echo_bag_lock() is False:
        print("\n背包声骸锁定功能结束或异常退出，结束脚本")
        sys.exit(0)
    return True


echo_bag_page = Page(
    name="声骸",
    targetTexts=[
        TextMatch(
            name="声",
            text="声",
        ),
        TextMatch(
            name="培养",
            text="培养",
        ),
    ],
    action=echo_bag,
)

pages.append(echo_bag_page)

# -*- coding: utf-8 -*-
"""
@software: PyCharm
@file: synthesis.py
@time: 2024/6/8 下午10:08
@author SuperLazyDog
"""
import time

from . import *

pages = []


# 定义一个名为login_action的函数，接收一个名为positions的字典参数，返回布尔值
def link_action(positions: dict[str, Position]) -> bool:
    try:
        # 调用find_text函数，传入字符串"点击"，将返回值赋给result变量
        result = find_text("点击")
        # 循环3次点击文字
        for i in range(3):
            # 调用click_position函数，传入result.position作为参数
            click_position(result.position)
            # 暂停0.4秒
            time.sleep(0.4)
    # 如果在try语句块中发生异常，执行except语句块中的代码
    except Exception as e:
        # 打印异常信息
        print(f"发生异常： {e}")
        # 继续点击文字"点击连接"
        result = find_text("点击")
        # 循环3次点击文字
        for i in range(3):
            # 调用click_position函数，传入result.position作为参数
            click_position(result.position)
            # 暂停0.4秒
            time.sleep(0.4)
        # 返回False
        check_game_restarting(del_file=True)
        return False
    # 如果没有发生异常，返回True
    check_game_restarting(del_file=True)
    return True


def add_link_page():
    # 创建一个名为login_page的Page对象
    login_page = Page(
        name="点击连接",
        targetTexts=[
            TextMatch(
                name="点击连接",
                text="点击连接",
            ),
        ],
        action=link_action,
    )
    # 将login_page对象添加到pages列表中
    pages.append(login_page)


add_link_page()  # 点击链接


def automatically_placed_in(positions: dict[str, Position]) -> bool:
    """
    自动放入
    :param positions:
    :return:
    """
    control.activate()
    click_position(positions.get("自动放入"))
    info.automaticallyFailedTimes += 1
    if info.automaticallyFailedTimes > 5:
        time.sleep(0.5)
        check_synthesis_end()
    return True


automatically_placed_in_page = Page(
    name="自动放入",
    targetTexts=[
        TextMatch(
            name="自动放入",
            text="自动放入",
        ),
    ],
    action=automatically_placed_in,
)

pages.append(automatically_placed_in_page)


def fusion(positions: dict[str, Position]) -> bool:
    """
    数据融合
    :param positions:
    :return:
    """
    info.inSynthesisFrame = True
    control.activate()
    click_position(positions.get("数据融合"))
    time.sleep(1)
    return True


fusion_page = Page(
    name="数据融合",
    targetTexts=[
        TextMatch(
            name="数据融合",
            text="数据融合",
            position=Position(
                x1=480,
            )
        ),
    ],
    excludeTexts=[
        TextMatch(
            name="自动放入",
            text="自动放入",
        ),
    ],
    action=fusion,
)
pages.append(fusion_page)


def tips(positions: dict[str, Position]) -> bool:
    """
    提示
    :param positions:
    :return:
    """
    control.activate()
    click_position(positions.get("登录"))
    time.sleep(1)
    random_click(1285, 680)
    time.sleep(1)
    return True


tips_page = Page(
    name="提示",
    targetTexts=[
        TextMatch(
            name="提示",
            text="提示",
        ),
        TextMatch(
            name="确认",
            text="确认",
        ),
        TextMatch(
            name="登录",
            text="登录",
        ),
    ],
    action=tips,
)

pages.append(tips_page)


def get_echoes(positions: dict[str, Position]) -> bool:
    """
    获取回音
    :param positions:
    :return:
    """
    control.activate()
    echo_synthesis()
    info.automaticallyFailedTimes = 0
    time.sleep(1)
    return True


get_echoes_page = Page(
    name="获得声骸",
    targetTexts=[
        TextMatch(
            name="获得声",
            text="获得声",
        ),
    ],
    action=get_echoes,
)

pages.append(get_echoes_page)

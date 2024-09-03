# -*- coding: utf-8 -*-
"""
@software: PyCharm
@file: mouse_reset.py
@time: 2024/6/2 下午4:02
@author SuperLazyDog
"""
import os
import sys
import time
from pynput.mouse import Controller
import math
from pathlib import Path
from threading import Event

project_root = Path(__file__).parent.parent.parent  # 项目根目录  # 获取当前文件所在目录
project_root_str = project_root.as_posix()  # 将 Path 对象转换为字符串
if project_root_str not in sys.path:
    sys.path.append(project_root_str)
from screeninfo import get_monitors
from status import logger


def get_current_monitor(x, y, monitors):
    for monitor in monitors:
        if monitor.x <= x < monitor.x + monitor.width and monitor.y <= y < monitor.y + monitor.height:
            return monitor
    return None


def mouse_reset(e: Event):
    logger("鼠标重置进程启动成功")
    mouse = Controller()
    last_position = mouse.position
    monitors = get_monitors()  # 获取所有显示器的信息
    num_monitors = len(monitors)
    if num_monitors == 1:
        logger(f"单显示器模式。")
        monitor_type = "single"
    else:
        logger(f"多显示器模式，共有{num_monitors}个显示器连接。")
        monitor_type = "multi"
        for i, monitor in enumerate(monitors):
            logger(f"显示器 {i + 1}:")
            logger(f"宽度: {monitor.width}，高度: {monitor.height}，x 坐标: {monitor.x}，y 坐标: {monitor.y}")
    current_monitor = None
    last_monitor = None
    while True:
        time.sleep(0.01)  # 0.01秒检测一次
        if e.is_set():
            break
        current_position = mouse.position
        if monitor_type == "multi":
            current_monitor = get_current_monitor(*current_position, monitors)
            last_monitor = get_current_monitor(*last_position, monitors)
        try:
            distance = math.sqrt(
                (current_position[0] - last_position[0]) ** 2
                + (current_position[1] - last_position[1]) ** 2
            )
            if monitor_type == "multi":
                if distance > 200 and current_monitor == last_monitor:
                    mouse.position = last_position
                else:
                    last_position = current_position
            else:
                if distance > 200:
                    mouse.position = last_position
                else:
                    last_position = current_position
        except Exception:
            logger("鼠标重置进程异常")

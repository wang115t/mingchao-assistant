# -*- coding: utf-8 -*-
"""
@software: PyCharm
@file: init.py
@time: 2024/6/3 下午3:57
@author SuperLazyDog
"""
import os
import ctypes
from status import logger
from constant import w, h, scale_factor, real_w, real_h, root_path, hwnd, wait_exit
import win32gui
from multiprocessing import current_process
from initPath import LoaderPath, UpdateModelPath

if current_process().name == "task":
    LoaderPath.verify_cuda_env()  # 检查cuda环境
    LoaderPath.set_module_path()  # 设置模块路径，解决中文路径问题
    UpdateModelPath().process_model()  # 更新模型
    logger("开源代码仓库地址（已停止维护）：https://github.com/lazydog28/mc_auto_boss")
    logger("Rin版仓库地址：https://github.com/RoseRin0/mc_auto_boss")
    logger("初始化中")
    logger(f"窗口大小：{w}x{h} 当前屏幕缩放：{scale_factor} 游戏分辨率：{real_w}x{real_h}")
    logger(f"项目路径：{root_path}")
    logger(f"将窗口移动至左上角")
    rect = win32gui.GetWindowRect(hwnd)  # 获取窗口区域
    win32gui.MoveWindow(
        hwnd, 0, 0, rect[2] - rect[0], rect[3] - rect[1], True
    )  # 设置窗口位置为0,0

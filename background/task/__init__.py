# -*- coding: utf-8 -*-
"""
@software: PyCharm
@file: __init__.py.py
@time: 2024/6/5 下午1:39
@author SuperLazyDog
"""
from schema import Task
from .pages.general import pages as general_pages
from .pages.boss import pages as boss_pages
from .pages.dreamless import pages as dreamless_pages
from .conditional_actions.boss import conditional_actions as boss_conditional_actions
from .pages.synthesis import pages as synthesis_pages
from .conditional_actions.synthesis import conditional_actions as synthesis_conditional_actions
from .pages.echo_bag_lock import pages as echo_bag_lock_pages

# 合并所有页面
boss_task = Task()
boss_task.pages = general_pages + boss_pages + dreamless_pages  # 合并通用页面和boss页面
boss_task.conditionalActions = boss_conditional_actions  # 添加boss专属条件动作

synthesis_task = Task()
synthesis_task.pages = synthesis_pages  # 合成页面
synthesis_task.conditionalActions = synthesis_conditional_actions  # 合成页面使用boss专属条件动作

echo_bag_lock_task = Task()
echo_bag_lock_task.pages = echo_bag_lock_pages  # 声骸背包页面

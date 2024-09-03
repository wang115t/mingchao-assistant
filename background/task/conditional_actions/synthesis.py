import time

from status import Status, logger
from schema import ConditionalAction
from . import *

conditional_actions = []


def judgment_try_change_to_synthesis_frame_times_over() -> bool:
    if info.tryChangeToSynthesisFrameTimes > 5:
        return True
    else:
        return False


def judgment_try_change_to_synthesis_frame_times_over_action() -> bool:
    logger("尝试切换到合成界面超过5次，返回boss任务", "DEBUG")
    change_task_to_boss()
    return False


judgment_try_change_to_synthesis_frame_times_over_conditional_action = ConditionalAction(
    name="(合成)尝试切换到合成界面超过指定次数",
    condition=judgment_try_change_to_synthesis_frame_times_over,
    action=judgment_try_change_to_synthesis_frame_times_over_action,
)
conditional_actions.append(judgment_try_change_to_synthesis_frame_times_over_conditional_action)


def judgment_main_frame_to_synthesis() -> bool:
    if info.inSynthesisFrame:
        return False
    if check_in_animation() == "is available":
        return True
    else:
        control.esc()
        time.sleep(1.5)
        return False


def judgment_main_frame_to_synthesis_action() -> bool:
    logger("处于游戏主界面，正在切换至合成界面", "WARN")
    info.tryChangeToSynthesisFrameTimes += 1
    time.sleep(2)
    control.esc()
    time.sleep(2)
    region = set_region(0, 0, 260, 120)
    if wait_text_designated_area("终端", 2, region):
        random_click(1440, 500)
        time.sleep(2)
    else:
        logger("未找到终端，停止切换到合成任务", "DEBUG")
        info.needSynthesis = False
        return False
    if wait_text_designated_area("数据坞", 2, region):
        random_click(75, 595)
        time.sleep(2)
    else:
        logger("未找到数据坞，停止切换到合成任务", "DEBUG")
        info.needSynthesis = False
        return False
    if wait_text_designated_area("数据融合", 2, region):
        info.needSynthesis = False
        info.inSynthesisFrame = True
        return True
    else:
        logger("未找到数据融合", "DEBUG")
        info.needSynthesis = False
        return False


judgment_game_stop_conditional_action = ConditionalAction(
    name="(合成)检查游戏界面",
    condition=judgment_main_frame_to_synthesis,
    action=judgment_main_frame_to_synthesis_action,
)
conditional_actions.append(judgment_game_stop_conditional_action)

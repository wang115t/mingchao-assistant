import os
import shutil
import sys
import urllib
import zipfile
from pathlib import Path
import multiprocessing

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import init  # !!此导入删除会导致不会将游戏移动到左上角以及提示当前分辨率!!
import status
import version
import ctypes
from mouse_reset import mouse_reset
from multiprocessing import Event, Queue
from pynput.keyboard import Key, Listener, KeyCode
from schema import Task
from task import boss_task, synthesis_task, echo_bag_lock_task
from utils import *
from config import config, wait_exit
from constant import game_start

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
app_path = config.AppPath
_shared_switch_task_flag = None
_log_window_display = None
log_queue = Queue()  # 日志队列


def init_shared_variables():
    """
    这段代码的主要功能是初始化两个共享变量 _shared_switch_task_flag 和 _log_window_display，
    这两个变量用于在多个进程之间共享数据。通过使用 multiprocessing.Manager，可以确保这些变量在不同进程中的修改是同步的。
    _shared_switch_task_flag 用于控制任务切换的标志。
    _log_window_display 用于控制日志窗口显示的标志。
    这两个变量的初始值都设置为 False，表示默认情况下任务不切换且日志窗口不显示。
    """
    # 使用 global 关键字声明 _shared_switch_task_flag 和 _log_window_display 为全局变量，这样在函数内部对它们的修改会影响到全局范围。
    global _shared_switch_task_flag, _log_window_display
    manager = multiprocessing.Manager()  # 管理共享变量
    # 使用管理器对象的 Value 方法创建一个共享的布尔值变量 _shared_switch_task_flag，初始值为 False。'b' 表示布尔类型
    _shared_switch_task_flag = manager.Value('b', False)
    # 同样使用管理器对象的 Value 方法创建另一个共享的布尔值变量 _log_window_display，初始值也为 False。
    _log_window_display = manager.Value('b', False)


def restart_app(e: Event, restartEvent, log_queue):
    if app_path:
        while True:
            # 在这里修改重启间隔，单位为秒 time.sleep(7200)表示2个小时重启一次
            # time.sleep(1800)
            # manage_application("UnrealWindow", "鸣潮  ", app_path,e)
            time.sleep(config.GameMonitorTime)  # 每秒检测一次，游戏窗口      改为用户自己设置监控间隔时间，默认为5秒，减少占用(RoseRin)
            find_ue4("UnrealWindow", "UE4-Client Game已崩溃  ")
            find_game_windows("UnrealWindow", "鸣潮  ", e, log_queue)
            if restartEvent.is_set():
                break


def find_ue4(class_name, window_title):
    if app_path:
        ue4windows = win32gui.FindWindow(class_name, window_title)
        if ue4windows != 0:  # 检测到游戏发生崩溃-UE4弹窗
            logger("UE4-Client Game已崩溃，尝试重启游戏......")
            win32gui.SendMessage(ue4windows, win32con.WM_CLOSE, 0, 0)
            # 等待崩溃窗口关闭
            time.sleep(2)
            if win32gui.FindWindow(class_name, window_title) == 0:
                return True
        else:
            return False


def find_game_windows(class_name, window_title, taskEvent, log_queue):
    global _shared_switch_task_flag
    if app_path:
        gameWindows = win32gui.FindWindow(class_name, window_title)
        if gameWindows == 0:
            logger("未找到游戏窗口")
            while not restart_application(app_path):  # 如果启动失败，则五秒后重新启动游戏窗口
                logger("启动失败，五秒后尝试重新启动...")
            # 运行方法一需要有前提条件
            # 如果重启成功，执行方法一
            time.sleep(20)
            taskEvent.clear()  # 清理BOSS脚本线程(防止多次重启线程占用-导致无法点击进入游戏)
            logger("自动启动BOSS脚本")
            init_shared_variables()
            shared_switch_task_flag = _shared_switch_task_flag
            shared_switch_task_flag.value = False
            task_thread = multiprocessing.Process(target=run,
                                                  args=(boss_task, taskEvent, shared_switch_task_flag, log_queue),
                                                  name="task")
            task_thread.start()


def close_window(class_name, window_title):
    # 尝试关闭窗口，如果成功返回 True，否则返回 False
    hwnd = win32gui.FindWindow(class_name, window_title)
    if hwnd != 0:
        win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        # 等待窗口关闭
        time.sleep(2)
        if win32gui.FindWindow(class_name, window_title) == 0:
            return True
    return False


def restart_application(app_path):
    if app_path:
        time.sleep(5)
        is_crashes_file = os.path.join(config.user_data_root, "isCrashes.txt")
        is_game_restarting_file = os.path.join(config.user_data_root, "isRestarting.dat")
        # 尝试启动应用程序，如果成功返回 True，否则返回 False
        try:
            game_start(none_log=True)
            logger("游戏疑似发生崩溃，尝试重启游戏......")
            # 判断文件是否存在，如果存在则删除
            if os.path.exists(is_crashes_file):
                os.remove(is_crashes_file)
            # 重新创建文件并写入值
            with open(is_crashes_file, "w") as f:
                f.write(str(True))
            with open(is_game_restarting_file, "w") as f:
                f.write(str("Restarting"))
            return True
        except Exception as e:
            logger(f"启动应用失败: {e}")
            return False


def end_small_game_process(game_process_name=None, memory_threshold_mb=100):
    """
    定义了一个名为 end_small_game_process 的函数。
    接受两个参数：
    game_process_name：一个可选参数，默认为 None，表示要检查的游戏进程名称列表。
    memory_threshold_mb：一个可选参数，默认为 100，表示内存使用阈值（以MB为单位）。
    """
    """
    该代码的主要功能是检查系统中指定游戏进程的内存使用情况，并终止那些内存占用低于指定阈值的进程。
    这有助于清理可能因崩溃而遗留的低内存占用进程，从而优化系统资源的使用。具体步骤包括：
    定义函数并设置默认参数。
    遍历系统中的所有进程。
    获取每个进程的PID、名称和内存使用信息。
    检查进程是否为指定的游戏进程，并且内存使用是否低于阈值。
    如果是，则打印相关信息并终止该进程。
    处理可能的异常情况，确保代码的健壮性。
    """
    # 如果 game_process_name 为 None，
    # 则将其设置为包含两个默认进程名称的列表：["Client-Win64-Shipping.exe", "Wuthering Waves.exe"]。
    if game_process_name is None:
        game_process_name = ["Client-Win64-Shipping.exe", "Wuthering Waves.exe"]
    # 将 game_process_name 列表转换为集合 game_process_names_set，以便快速查找。
    game_process_names_set = set(game_process_name)
    # 使用 psutil.process_iter 遍历系统中所有进程，并获取进程的 pid、name 和 memory_info。
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        # 使用 proc.oneshot() 上下文管理器来高效地获取进程信息。
        # 获取进程的 pid、name 和 memory_info。
        # 计算进程的内存使用量（以MB为单位）。
        try:
            with proc.oneshot():  # 上下文管理器
                pid = proc.pid  # 获取进程ID
                name = proc.name()  # 获取进程名称
                memory_info = proc.memory_info()  # 获取内存信息
                memory_usage_mb = memory_info.rss / (1024 * 1024)  # 转换为MB
                # 如果进程名称在 game_process_names_set 中，并且内存使用量小于 memory_threshold_mb，则认为该进程可能是崩溃遗留进程。
                # 打印相关信息并终止该进程。
            if name in game_process_names_set and memory_usage_mb < memory_threshold_mb:
                print(
                    f"找到游戏进程： {name} (PID: {pid})，使用内存: {memory_usage_mb:.2f} MB，内存占用过小，可能是崩溃遗留进程，终止该进程")
                psutil.Process(pid).terminate()  # 终止进程
        # 捕获并处理可能的异常：
        # psutil.NoSuchProcess：进程不存在。
        # psutil.AccessDenied：访问被拒绝。
        # psutil.ZombieProcess：僵尸进程。
        # 如果发生这些异常，则继续下一个进程的检查。
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


def manage_application(class_name, window_title, app_path, taskEvent):
    global _shared_switch_task_flag
    if app_path:
        # 先停止脚本
        logger("自动暂停脚本！@")
        taskEvent.clear()
        while True:
            if close_window(class_name, window_title):
                # 如果关闭成功，尝试重启应用程序
                logger("窗口关闭成功，正在尝试重新启动...")
                while not restart_application(app_path):
                    logger("启动失败，五秒后尝试重新启动...")
                # 运行方法一需要有前提条件
                # 如果重启成功，执行方法一
                time.sleep(20)
                end_small_game_process()
                logger("自动启动BOSS脚本")
                init_shared_variables()
                shared_switch_task_flag = _shared_switch_task_flag
                shared_switch_task_flag.value = False
                log_queue.value = False
                task_thread = multiprocessing.Process(target=run,
                                                      args=(boss_task, taskEvent, shared_switch_task_flag, log_queue),
                                                      name="task")
                task_thread.start()
                break
            else:
                # 如果关闭失败，检查窗口是否还存在
                if win32gui.FindWindow(class_name, window_title) != 0:
                    logger("关闭失败，窗口仍然存在，正在尝试重新关闭...")
                else:
                    logger("窗口已不存在，尝试重启...")
                    while not restart_application(app_path):
                        logger("启动失败，五秒后尝试重新启动...")
                    break


logger(f"初始化完成")


def set_console_title(title: str):
    ctypes.windll.kernel32.SetConsoleTitleW(title)


set_console_title(f"McTool ver {version.__version__}   ---RinRin自用版本")


def run(task: Task, e: Event, shared_switch_task_flag, log_queue):
    """
    运行
    :return:
    """
    logger("任务进程开始运行")
    logger("请将鼠标移出游戏窗口，避免干扰脚本运行")
    if e.is_set():
        logger("任务进程已经在运行，不需要再次启动")
        return
    e.set()
    while e.is_set():
        img = screenshot()
        result = ocr(img)
        task(img, result, shared_switch_task_flag, e, log_queue)
    # 等待task进程完全结束后 再设置切换共享的任务flag给switch_task函数进行切换，防止还未退出循环就将e又设置为True
    try:
        shared_switch_task_flag.value = True
    except Exception as e:
        pass
    logger("进程停止运行")


def get_key_from_string(key_str):
    try:
        # 尝试从 Key 中获取特殊键
        return getattr(Key, key_str)
    except AttributeError:
        # 如果不是特殊键，返回普通字符键
        return KeyCode.from_char(key_str)


def run_listener(shared_switch_task_flag, log_queue, taskEvent, mouseResetEvent, restartEvent, params):
    def on_press(key):
        # print(f"Pressed key: {key}")  # 调试信息
        """
        默认：
        F5 启动BOSS脚本
        F6 启动融合脚本
        F7 暂停脚本
        F8 启动锁定脚本
        F12 停止脚本
        :param key:
        :return:
        """
        if key == get_key_from_string(config.ShortcutBossTaskStart):
            logger(f"{config.__fields__['ShortcutBossTaskStart'].title}")
            task_thread = multiprocessing.Process(target=run,
                                                  args=(boss_task, taskEvent, shared_switch_task_flag, log_queue),
                                                  name="task")
            task_thread.start()
        if key == get_key_from_string(config.ShortcutSynthesisEchoes):
            logger(f"{config.__fields__['ShortcutSynthesisEchoes'].title}")
            task_thread = multiprocessing.Process(target=run,
                                                  args=(synthesis_task, taskEvent, shared_switch_task_flag, log_queue),
                                                  name="task")
            task_thread.start()
        if key == get_key_from_string(config.ShortcutTaskStop):
            logger(f"{config.__fields__['ShortcutTaskStop'].title}")
            taskEvent.clear()
        if key == get_key_from_string(config.ShortcutLockEchoes):
            logger(f"{config.__fields__['ShortcutLockEchoes'].title}")
            task_thread = multiprocessing.Process(target=run, args=(
                echo_bag_lock_task, taskEvent, shared_switch_task_flag, log_queue), name="task")
            task_thread.start()
        if key == get_key_from_string(config.ShortcutMaskWindowDisplayStatusChange):
            logger(f"{config.__fields__['ShortcutMaskWindowDisplayStatusChange'].title}")
        if key == get_key_from_string(config.ShortcutAllStop):
            logger(f"{config.__fields__['ShortcutAllStop'].title}")
            log_queue.put('exit')
            taskEvent.clear()
            mouseResetEvent.set()
            restartEvent.set()
            return False
        return None

    if params:
        if params == "run" or params is None:
            # 根据params参数执行相应的操作
            on_press(get_key_from_string(config.ShortcutBossTaskStart))
        elif params == "Synthetic":
            on_press(get_key_from_string(config.ShortcutSynthesisEchoes))
        elif params == "BackpackBlock":
            on_press(get_key_from_string(config.ShortcutLockEchoes))
    # 启动键盘监听器
    with Listener(on_press=on_press) as listener:
        listener.join()


def check_confirm_user_permissions():
    user_level = "RinRin"
    secret_key = "957222395"  # 设置启动密钥
    if user_level == "RinRin":
        user_input = "RinRin95"
    else:
        user_input = input("\n请输入启动密钥：")
    if user_input == secret_key:
        print("密钥正确，程序启动。")
        confirm = True
    elif user_input == "RinRin95":
        print("☆RinRin☆")
        confirm = True
    else:
        print("密钥错误，程序退出。")
        confirm = False
    return confirm
    # 在这里添加你的程序逻辑


def check_authorization_validity_period():
    validity_time = datetime(2024, 10, 15, 0, 0, 0)
    print(
        f"授权有效期至{validity_time.year}/{validity_time.month}/{validity_time.day} {validity_time.hour}:{validity_time.minute}:{validity_time.second}")
    remaining_time = validity_time - datetime.now()
    if remaining_time.total_seconds() < 0:
        print("授权已过期")
        return False
    else:
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        print(f"验证成功，剩余{days}天{hours}小时{minutes}分钟。")
        return True


def end_thread(thread_name, thread):
    thread_name.set()
    time.sleep(1)
    thread.join()


def check_read_tutorial():
    is_read_tutorial_file = os.path.join(config.user_data_root, "isReadTutorial.dat")
    read_tutorial_file = os.path.join(config.project_root, "一些简单的问题解答(更新中).txt")
    if not os.path.exists(is_read_tutorial_file):
        user_input = input('是否已经阅读了【一些简单的问题解答(更新中).txt】？(y/n) ')
        if user_input.lower() == "y":
            print("欢迎使用本程序", "INFO")
            with open(is_read_tutorial_file, "w") as f:
                f.write(str("User has read"))
        else:
            try:
                print("请先阅读【问题解答】\n")
                os.startfile(read_tutorial_file)
            except Exception:
                print(f"未找到【问题解答】{read_tutorial_file}，请下载阅读后再运行本程序")
                wait_exit()
    else:
        logger("欢迎使用本程序，有问题请先查看程序目录下的问题解答", "INFO")


switch_event = multiprocessing.Event()  # 切换任务的事件


def start_task_change(new_task, shared_switch_task_flag, task_event, log_queue, task_name: str = ""):
    switch_event.set()  # 触发任务切换事件
    task_change_thread = multiprocessing.Process(
        target=task_change, args=(new_task, task_event, switch_event, task_name, shared_switch_task_flag, log_queue),
        name="task_change"
    )
    task_change_thread.start()


def task_change(new_task, task_event, switch_event, task_name, shared_switch_task_flag, log_queue):
    while True:
        if switch_event.is_set():
            logger(
                f"task_change: 准备切换任务到{task_name}，正在等待当前进程结束" if task_name else f"task_change: 准备切换任务，正在等待当前进程结束",
                "IMPORTANT"
            )
            task_event.clear()
            time.sleep(3)
            if shared_switch_task_flag.value:
                logger(
                    f"正在切换任务到{task_name}" if task_name else "正在切换任务",
                    "IMPORTANT"
                )
                shared_switch_task_flag.value = False
                task_thread = multiprocessing.Process(target=run,
                                                      args=(new_task, task_event, shared_switch_task_flag, log_queue),
                                                      name="task")
                task_thread.start()
                switch_event.clear()
                logger(
                    f"已成功切换任务到{task_name}" if task_name else "切换任务成功",
                    "IMPORTANT"
                )
        time.sleep(1)


if __name__ == "__main__":
    # user = "guest"
    # if user == "Rin":
    #     pass
    # else:
    #     if not check_authorization_validity_period(): # 验证授权有效期
    #         time.sleep(3)
    #         exit()
    #     if not check_confirm_user_permissions():  # 验证启动密钥
    #         time.sleep(3)
    #         exit()
    # check_for_updates() # 检查更新
    # check_read_tutorial()

    init_shared_variables()  # 初始化共享变量
    shared_switch_task_flag = _shared_switch_task_flag  # 共享的任务切换flag
    # log_window_display = _log_window_display
    # log_window_process = multiprocessing.Process(target=start_log_window, args=(log_queue, log_window_display))
    # log_window_process.start()
    taskEvent = multiprocessing.Event()
    mouseResetEvent = multiprocessing.Event()  # 用于停止鼠标重置线程
    mouse_reset_thread = multiprocessing.Process(
        target=mouse_reset, args=(mouseResetEvent,), name="mouse_reset"
    )
    mouse_reset_thread.start()
    restartEvent = multiprocessing.Event()  # 用于停止重启线程
    restart_thread = multiprocessing.Process(
        target=restart_app, args=(taskEvent, restartEvent, log_queue), name="restart_event"
    )
    restart_thread.start()
    listenerEvent = multiprocessing.Event()  # 用于停止监听线程
    listener_thread = multiprocessing.Process(
        target=run_listener,
        args=(shared_switch_task_flag, log_queue, taskEvent, mouseResetEvent, restartEvent,
              sys.argv[1] if len(sys.argv) > 1 else None),
        name="listener"
    )
    listener_thread.start()
    if app_path:
        logger(f"游戏路径：{config.AppPath}")
    else:
        logger("未找到游戏路径", "WARN")
    logger("应用重启进程启动")
    logger(f"version: {version.__version__}")
    logger("鼠标重置进程启动")
    print(
        "\n --------------------------------------------------------------"
        "\n     注意：此版本为RinRin自用版本，如你获得此代码，请立即删除！\n "
        "--------------------------------------------------------------\n"
    )
    print("请确认已经配置好了config.yaml文件\n")
    content = f"""
    使用说明：
        {config.ShortcutBossTaskStart.upper()}\t{config.__fields__['ShortcutBossTaskStart'].title}
        {config.ShortcutSynthesisEchoes.upper()}\t{config.__fields__['ShortcutSynthesisEchoes'].title}
        {config.ShortcutTaskStop.upper()}\t{config.__fields__['ShortcutTaskStop'].title}
        {config.ShortcutLockEchoes.upper()}\t{config.__fields__['ShortcutLockEchoes'].title}
        {config.ShortcutAllStop.upper()}\t{config.__fields__['ShortcutAllStop'].title}
        """
    print(content)
    logger("开始运行")
    print("结束运行")

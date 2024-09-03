import os
import shutil
import sys
import urllib
import zipfile
from pathlib import Path
import ctypes
import logging
import os
import subprocess

import requests
from tqdm import tqdm
from status import logger


class Updater:
    def __init__(self, aria2_path, download_file_path, download_url, exe_path):
        self.aria2_path = aria2_path  # os.path.abspath("./assets/binary/aria2c.exe")
        self.download_file_path = download_file_path  # 下载文件路径
        self.download_url = download_url  # 下载地址
        # 设置7za.exe的路径(必须准备7za.exe)
        self.exe_path = exe_path  # os.path.abspath("./assets/binary/7za.exe")
        # 设置aria2c.exe的路径(必须准备aria2c.exe)
        self.logger = logger
        self.root_path = Path(__file__).parent.parent.parent  # 项目根目录
        self.lib_path = self.root_path / "py310" / "Lib" / "site-packages"  # 第三方库文件夹路径
        self.temp_path = os.path.join(self.root_path, '.tmp')  # 临时文件夹路径
        if not os.path.exists(self.temp_path):  # 如果不存在.temp文件夹，则创建
            os.makedirs(self.temp_path, exist_ok=True)
        # 解压文件夹路径 = 下载文件路径 临时文件夹.tmep路径
        self.extract_folder_path = os.path.join(self.temp_path, os.path.basename(self.download_url).rsplit(".", 1)[0])

    def download_with_progress(self):
        """下载文件并显示进度条。"""
        self.logger(msg="下载", level="DEBUG")
        if os.path.exists(os.path.join(self.temp_path, "paddleocr")) and os.path.exists(
                os.path.join(self.temp_path, ".paddleocr")):
            self.logger(msg="检测到已下载文件，跳过下载", level="DEBUG")
            return
        while True:
            try:
                self.logger(msg="开始下载", level="DEBUG")
                if os.path.exists(self.aria2_path):
                    command = [self.aria2_path, "--max-connection-per-server=16",
                               "--dir={}".format(os.path.dirname(self.download_file_path)),
                               "--out={}".format(os.path.basename(self.download_file_path)), self.download_url]
                    if os.path.exists(self.download_file_path):
                        command.insert(2, "--continue=true")
                    subprocess.run(command, check=True)
                else:
                    response = requests.head(self.download_url)
                    file_size = int(response.headers.get('Content-Length', 0))

                    with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                        with requests.get(self.download_url, stream=True) as r:
                            with open(self.download_file_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=1024):
                                    if chunk:
                                        f.write(chunk)
                                        pbar.update(len(chunk))
                self.logger(msg=f"下载完成{self.download_file_path}", level="DEBUG")

                break
            except Exception as e:
                self.logger(msg=f"下载失败{e}", level="ERROR")

                input("按回车键重试. . .")
                if os.path.exists(self.download_file_path):
                    os.remove(self.download_file_path)
                self.logger(msg=f"完成{e}", level="INFO")
        return

    def cover_folder(self):
        """覆盖安装最新版本的文件。"""
        while True:
            try:
                self.logger(msg="开始修复用户名中文路径报错问题...", level="DEBUG")  # 记录覆盖操作的开始
                download_file_path = os.path.join(self.temp_path, "paddleocr_process.zip")
                if "process" in self.download_url and os.path.exists(download_file_path):  # 如果下载包含"process"且待删除的文件夹存在
                    self.logger(msg=f"待删除压缩包{download_file_path})", level="DEBUG")
                    os.remove(download_file_path)  # 删除下载的zip文件
                    if not os.path.exists(download_file_path):
                        self.logger(msg="已删除压缩包:paddleocr_process.zip", level="DEBUG")
                try:
                    self.logger(msg=f"开始复制文件夹内容从 {self.temp_path} 到 {self.lib_path}",
                                level="DEBUG")
                    if os.path.exists(os.path.join(self.lib_path, "paddleocr")):
                        shutil.rmtree(os.path.join(self.lib_path, "paddleocr"))
                    # os.makedirs(self.lib_path / ".paddleocr", exist_ok=True)  # 判断是否存在，不存在则创建
                    # os.makedirs(self.lib_path / "paddleocr", exist_ok=True)  # 判断是否存在，不存在则创建
                    # shutil.copytree(self.temp_path, self.lib_path, dirs_exist_ok=True)
                    shutil.copytree(os.path.join(self.temp_path), os.path.join(self.lib_path), dirs_exist_ok=True)
                    # shutil.copytree(os.path.join(self.temp_path), os.path.join(self.lib_path), dirs_exist_ok=True)

                    self.logger(msg=f"成功复制文件夹内容到 {self.lib_path}", level="DEBUG")
                    if os.path.exists(os.path.join(self.lib_path, "paddleocr") and os.path.exists(
                            os.path.join(self.lib_path, ".paddleocr"))):
                        self.logger(msg=f"覆盖完成:{os.path.join(self.lib_path, 'paddleocr')}", level="DEBUG")
                        self.logger(msg=f"覆盖完成:{os.path.join(self.lib_path, '.paddleocr')}", level="DEBUG")
                        if os.path.exists(self.temp_path):
                            # 清理临时文件夹
                            shutil.rmtree(self.temp_path)
                            self.logger(msg="清理临时文件夹", level="DEBUG")
                        else:
                            self.logger(msg="临时文件夹不存在，无需清理", level="DEBUG")
                        break  # 完成f覆盖操作,退出循环
                except Exception as e:
                    self.logger(msg=f"复制文件夹内容失败: {e}", level="ERROR")
                    input("按回车键重试. . .")

            except Exception as e:  # 如果覆盖过程中出现其他异常
                self.logger(msg=f"修复【失败】:{e}", level="ERROR")  # 记录覆盖失败及错误信息
                input("按回车键重试. . .")  # 提示用户按回车键重试

    def extract_file(self):
        """
        解压下载的文件。

        该方法负责解压缩之前下载的文件。它首先检查是否存在特定的解压工具（如7z），如果存在，则使用该工具进行解压；
        如果不存在，将使用Python的shutil模块提供的方法进行解压。解压成功后会返回True，失败时会提示用户重新下载。

        Returns:
            bool: 解压成功返回True，失败返回False。
        """
        # if os.path.exists(os.path.join(self.temp_path, "paddleocr") and os.path.exists(
        #         os.path.join(self.temp_path, ".paddleocr"))):
        #     logger(msg="检测到已下载文件，无需解压文件", level="DEBUG")
        #     return True

        # 初始化解压过程
        self.logger(msg="=============解压==============",
                    level="DEBUG")
        while True:
            try:
                # 尝试解压文件
                self.logger(msg="开始解压...", level="DEBUG")
                if os.path.exists(self.exe_path):
                    # 如果特定的解压工具路径存在，使用该工具进行解压
                    subprocess.run([self.exe_path, "x", self.download_file_path, f"-o{self.temp_path}", "-aoa"],
                                   check=True)
                else:
                    # 否则，使用shutil模块提供的解压方法
                    shutil.unpack_archive(self.download_file_path, self.temp_path)
                if os.path.exists(os.path.join(self.temp_path, "paddleocr_process")):
                    # 解压成功日志
                    self.logger(msg=f"解压完成:paddleocr_process", level="DEBUG")
                self.logger(
                    msg="完成",
                    level="DEBUG")
                return True
            except Exception as e:
                # 解压失败处理
                self.logger(msg=f"解压失败: {e}", level="ERROR")
                self.logger(
                    msg="完成",
                    level="DEBUG")
                # 提示用户输入以重新下载
                input("按回车键重新下载. . .")
                # 删除失败的下载文件，准备重新下载
                if os.path.exists(self.download_file_path):
                    os.remove(self.download_file_path)
                return False


class CheckerUserNames:
    @staticmethod
    def is_chinese_char(char):
        """
        判断一个字符是否是中文字符
        """
        return any([
            '\u4e00' <= char <= '\u9fff',  # 基本汉字
            '\u3400' <= char <= '\u4dbf',  # 扩展汉字
            '\u20000' <= char <= '\u2a6df',  # 汉字补充
            '\u2a700' <= char <= '\u2b73f',  # 汉字扩展C
            '\u2b740' <= char <= '\u2b81f',  # 汉字扩展D
            '\u2b820' <= char <= '\u2ceaf',  # 汉字扩展E
            '\u2ceb0' <= char <= '\u2ebef',  # 汉字扩展F
        ])

    @staticmethod
    def contains_chinese(username):
        """
        判断用户名是否包含中文字符
        """
        return any(CheckerUserNames.is_chinese_char(char) for char in username)

    @staticmethod
    def get_current_username():
        """
        获取当前系统用户名
        """
        return os.getlogin()


class LoaderPath:
    @staticmethod
    def process_paddleocr_chinese_name__error(root_path, third__library):
        if not CheckerUserNames.contains_chinese(CheckerUserNames.get_current_username()):  # 如果用户名不包含中文字符，则不进行处理
            logger(msg=f"Hi,{CheckerUserNames.get_current_username()}", level="DEBUG")
            return
        if os.path.exists(os.path.join(third__library, ".paddleocr")):  # 第三方库下的.paddleocr是存在的，不进行处理
            return
        # 第三方库文件夹不存在，则创建
        # if not os.path.exists(third__library):
        #     os.makedirs(third__library)
        #  下载地址
        url = f"https://gitee.com/wang-wenfu1/ming-chao-repair/releases/download/v1-chinesename-repair/paddleocr_process.zip"

        save_path = os.path.join(root_path, ".tmp", "paddleocr_process.zip")  # 保存临时文件夹.temp下

        if not os.path.exists(save_path):
            try:
                logger(msg=f"paddleocr_process.zip文件，请耐心等待...", level="DEBUG")
                aria2_path = os.path.join(root_path, "assets", "binary", "aria2c.exe")
                # 下载文件路径:项目根目录临时文件夹temp文件夹下
                download_file_path = os.path.join(root_path, ".tmp", "paddleocr_process.zip")
                download_url = url
                exe_path = os.path.join(root_path, "assets", "binary", "7za.exe")

                updater = Updater(aria2_path, download_file_path, download_url, exe_path)
                while True:
                    updater.download_with_progress()  # 下载文件
                    if updater.extract_file():  # 解压文件，并返回True  # 解压文件
                        break
                updater.cover_folder()  # 移动文件到第三方库文件夹 修复中文用户名为中文路径的问题
            except Exception as e:
                logger(msg=f"下载paddleocr.zip文件失败: {e}", level="ERROR")
                input("按回车键重新下载. . .")

    @staticmethod
    def set_cuda_cudnn_env(cuda_cudnn_bundle_path):
        """
        设置CUDA和cuDNN的环境变量，使其指向指定的路径。

        参数:
        cuda_cudnn_bundle_path -- CUDA和cuDNN的打包路径
        """
        # 设置环境变量
        os.environ['PATH'] = os.path.join(cuda_cudnn_bundle_path, 'bin') + ';' + os.path.join(cuda_cudnn_bundle_path,
                                                                                              'libnvvp') + ';' + \
                             os.environ[
                                 'PATH']
        os.environ['CUDA_HOME'] = cuda_cudnn_bundle_path
        os.environ['CUDA_PATH'] = cuda_cudnn_bundle_path
        os.environ['CUDNN_PATH'] = os.path.join(cuda_cudnn_bundle_path, 'lib', 'x64')
        os.environ['LD_LIBRARY_PATH'] = os.path.join(cuda_cudnn_bundle_path, 'lib', 'x64') + ';' + os.path.join(
            cuda_cudnn_bundle_path, 'lib') + ';' + os.environ.get('LD_LIBRARY_PATH', '')
        os.environ['INCLUDE'] = os.path.join(cuda_cudnn_bundle_path, 'include') + ';' + os.environ.get('INCLUDE', '')

    @staticmethod
    def verify_cuda_env():
        # 定义CUDA和cuDNN的打包路径
        root_path = Path(__file__).parent.parent.parent  # 项目根目录
        cuda_cudnn_bundle_path = os.path.join(root_path, "cuda_cudnn_bundle")  # CUDA和cuDNN的打包路径
        # 进入静态图模式
        # paddle.enable_static()
        if not os.path.exists(cuda_cudnn_bundle_path):  # 该cuda目录不存在不进行设置环境变量
            return
        # 设置环境变量
        LoaderPath.set_cuda_cudnn_env(cuda_cudnn_bundle_path)

        # 验证PaddlePaddle-GPU和ONNXRuntime-GPU是否使用指定的CUDA和cuDNN
        # try:
        #     paddle.utils.run_check()
        #     print(f"ONNXRuntime device: {rt.get_device()}")
        # except Exception as e:
        #     print(f"An error occurred: {e}")

    @staticmethod
    def set_module_path():

        """
        设置模块导入路径
        """
        #################################################################################
        # 设置环境变量解决 macOS 多线程报错
        os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
        root_path = Path(__file__).parent.parent.parent
        third__library = root_path / "py310" / "Lib" / "site-packages"
        # 处理中文运行报错paddleocr
        LoaderPath.process_paddleocr_chinese_name__error(root_path, third__library)
        # print(f"项目根目录:{root_path}")
        # 指定多个模块导入路径

        module_paths = [
            root_path,  # 项目根目录
            third__library,  # 第三方库目录
        ]

        # 添加DLL文件所在的目录
        for module_path in module_paths:
            if module_path.exists():
                os.add_dll_directory(str(module_path))
                sys.path.append(str(module_path))
                # logger(f"导入模块路径:{module_path}",level="DEBUG")

        # 显式加载zlibwapi.dll文件
        # zlibwapi_dll_path = root_path / "py310" / "lib" / "site-packages" / "zlibwapi.dll"
        # if zlibwapi_dll_path.exists():
        #     try:
        #         ctypes.windll.LoadLibrary(str(zlibwapi_dll_path))
        #     except Exception as e:
        #         print(f"加载zlibwapi.dll文件时发生错误: {e}")
        # else:
        #     print(f"zlibwapi.dll文件不存在: {zlibwapi_dll_path}")


class UpdateModelPath:
    def __init__(self):
        self.root_path = Path(__file__).parent.parent.parent
        self.model_path = self.root_path / "mc_auto_boss-RoseRin" / "models"
        self.model_suffix = ".onnx"

    def process_model(self):
        # 如果项目根目录中的模型文件不存在 .onnx文件，就去下载，并保存到项目根目录中
        if not os.path.exists(os.path.join(self.root_path, "yolo.onnx")):
            logger(msg=f"检测到模型文件不存在，请手动下载模型文件...", level="DEBUG")
            logger(
                msg=f"下载地址:https://www.123pan.com/s/gZjtVv-7lp7d",
                level="DEBUG")
            logger("下载完成后进行解压，将解压后的文件夹下的所有模型文件复制到安装根目录下......")
            input("按回车键退出. . .")
            exit()  # 退出程序
        if not os.path.exists(self.model_path):
            return
        # 判断该文件夹中是否存在文件
        if not os.listdir(self.model_path):
            return
            # 将该发布的模型文件复制到系统根目录中,
            # 优点：没有必要每次都下载模型文件，简化了更新大小
            # 下次更新时，直接将上传好的文件覆盖根目录即可
        shutil.copytree(os.path.join(self.model_path), os.path.join(self.root_path), dirs_exist_ok=True)
        # 将models文件夹中的所有文件删除
        if os.listdir(self.model_path):
            shutil.rmtree(self.model_path)
            logger(msg=f"模型文件初始化完成", level="DEBUG")

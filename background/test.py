import ctypes
import os
import subprocess
import sys
from pathlib import Path

import paddle


def set_cuda_cudnn_env(cuda_cudnn_bundle_path):
    """
    设置CUDA和cuDNN的环境变量，使其指向指定的路径。

    参数:
    cuda_cudnn_bundle_path -- CUDA和cuDNN的打包路径
    """
    # 设置环境变量
    os.environ['PATH'] = os.path.join(cuda_cudnn_bundle_path, 'bin') + ';' + os.path.join(cuda_cudnn_bundle_path,
                                                                                          'libnvvp') + ';' + os.environ[
                             'PATH']
    os.environ['CUDA_HOME'] = cuda_cudnn_bundle_path
    os.environ['CUDA_PATH'] = cuda_cudnn_bundle_path
    os.environ['CUDNN_PATH'] = os.path.join(cuda_cudnn_bundle_path, 'lib', 'x64')
    os.environ['LD_LIBRARY_PATH'] = os.path.join(cuda_cudnn_bundle_path, 'lib', 'x64') + ';' + os.path.join(
        cuda_cudnn_bundle_path, 'lib') + ';' + os.environ.get('LD_LIBRARY_PATH', '')
    os.environ['INCLUDE'] = os.path.join(cuda_cudnn_bundle_path, 'include') + ';' + os.environ.get('INCLUDE', '')


def verify_cuda_env():
    # 定义CUDA和cuDNN的打包路径
    root_path = Path(__file__).parent.parent.parent  # 项目根目录
    cuda_cudnn_bundle_path = os.path.join(root_path, "cuda_cudnn_bundle")  # CUDA和cuDNN的打包路径
    # 进入静态图模式
    paddle.enable_static()
    if not os.path.exists(cuda_cudnn_bundle_path):  # 该cuda目录不存在不进行设置环境变量
        return
    # 设置环境变量
    set_cuda_cudnn_env(cuda_cudnn_bundle_path)

    # 验证PaddlePaddle-GPU和ONNXRuntime-GPU是否使用指定的CUDA和cuDNN
    # try:
    #     paddle.utils.run_check()
    #     print(f"ONNXRuntime device: {rt.get_device()}")
    # except Exception as e:
    #     print(f"An error occurred: {e}")


def set_module_path():
    """
    设置模块导入路径
    """
    #################################################################################
    # 设置环境变量解决 macOS 多线程报错
    os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
    root_path = Path(__file__).parent.parent.parent
    # print(f"项目根目录:{root_path}")
    # 指定多个模块导入路径

    module_paths = [
        root_path,  # 项目根目录
        root_path / "py310" / "lib" / "site-packages",  # 第三方库目录
    ]

    # 添加DLL文件所在的目录
    for module_path in module_paths:
        if module_path.exists():
            os.add_dll_directory(str(module_path))
            sys.path.append(str(module_path))
            # logger(f"导入模块路径:{module_path}",level="DEBUG")

    # 显式加载zlibwapi.dll文件
    zlibwapi_dll_path = root_path / "py310" / "lib" / "site-packages" / "zlibwapi.dll"
    if zlibwapi_dll_path.exists():
        try:
            ctypes.windll.LoadLibrary(str(zlibwapi_dll_path))
        except Exception as e:
            print(f"加载zlibwapi.dll文件时发生错误: {e}")
    else:
        print(f"zlibwapi.dll文件不存在: {zlibwapi_dll_path}")


set_module_path()  # 设置模块导入路径
verify_cuda_env()  # 验证并设置CUDA环境变量

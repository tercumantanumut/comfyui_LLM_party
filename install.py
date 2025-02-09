import importlib
import os
import platform
import re
import subprocess
import sys

import packaging.tags
from requests import get


def get_python_version():
    """Return the Python version in a concise format, e.g., '39' for Python 3.9."""
    version_match = re.match(r"3\.(\d+)", platform.python_version())
    if version_match:
        return "3" + version_match.group(1)
    else:
        return None


def get_system_info():
    system_info = {
        "gpu": False,
        "cuda_version": None,
        "avx2": False,
        "python_version": get_python_version(),
        "os": platform.system(),
        "os_bit": platform.architecture()[0].replace("bit", ""),
        "platform_tag": None,
        "metal": False  # 添加metal参数
    }

    # 检查NVIDIA GPU和CUDA版本
    if importlib.util.find_spec("torch"):
        import torch
        system_info["gpu"] = torch.cuda.is_available()
        if system_info["gpu"]:
            system_info["cuda_version"] = "cu" + torch.version.cuda.replace(".", "").strip()

    # 检查AVX2支持
    if importlib.util.find_spec("cpuinfo"):
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            if cpu_info and "flags" in cpu_info:
                system_info["avx2"] = "avx2" in cpu_info["flags"]
            else:
                system_info["avx2"] = False
        except Exception as e:
            print(f"Error retrieving CPU information: {e}")
            system_info["avx2"] = False
    else:
        print("cpuinfo module not available.")
        system_info["avx2"] = False

    # 使用PyTorch检查macOS上的Metal支持
    if system_info["os"] == "Darwin":
        if importlib.util.find_spec("torch"):
            import torch
            if torch.backends.mps.is_available():
                system_info["metal"] = True
            else:
                system_info["metal"] = False

    # 确定平台标签
    if importlib.util.find_spec("packaging.tags"):
        system_info["platform_tag"] = next(packaging.tags.sys_tags()).platform

    return system_info


def check_and_uninstall_websocket():
    # 获取当前Python解释器的路径
    interpreter = sys.executable

    # 检查websocket库是否已安装
    installed_packages = {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}
    websocket_installed = "websocket" in installed_packages
    websocket_client_installed = "websocket-client" in installed_packages

    # 如果websocket库已安装，卸载websocket和websocket-client库
    if websocket_installed:
        packages_to_uninstall = []
        packages_to_uninstall.append("websocket")
        packages_to_uninstall.append("websocket-client")

        try:
            subprocess.check_call([interpreter, "-m", "pip", "uninstall", "-y"] + packages_to_uninstall)
            print("已成功卸载: " + ", ".join(packages_to_uninstall))
        except subprocess.CalledProcessError as e:
            print("卸载过程中出现错误：", e)
        # 重新安装websocket-client库
        try:
            subprocess.check_call([interpreter, "-m", "pip", "install", "websocket-client"])
            print("websocket-client库已成功重新安装。")
        except subprocess.CalledProcessError as e:
            print("重新安装过程中出现错误：", e)


def init_temp():
    # 构建prompt.json的绝对路径，如果temp文件夹不存在就创建
    current_dir_path = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(current_dir_path, "temp"), exist_ok=True)


def install_homebrew():
    try:
        result = subprocess.run(["brew", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Homebrew is not installed. Please install Homebrew first.")
            print("You can install Homebrew by running the following command:")
            print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            return False
        else:
            print("Homebrew is already installed.")
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking Homebrew installation: {e}")
        return False


def install_portaudio():
    try:
        if os.name == "posix":
            if sys.platform == "linux" or sys.platform == "linux2":
                result = subprocess.run(["cat", "/etc/os-release"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if "EndeavourOS" in result.stdout or "Arch" in result.stdout:
                    result = subprocess.run(["pacman", "-Q", "portaudio"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        os.system("pacman -Sy")
                        os.system("pacman -S --noconfirm portaudio")
                    else:
                        print("portaudio is already installed.")
                elif "CentOS" in result.stdout or "Red Hat" in result.stdout:
                    result = subprocess.run(["rpm", "-q", "portaudio"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        os.system("yum update")
                        os.system("yum install -y portaudio")
                    else:
                        print("portaudio is already installed.")
                elif "Fedora" in result.stdout:
                    result = subprocess.run(["rpm", "-q", "portaudio"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        os.system("dnf update")
                        os.system("dnf install -y portaudio")
                    else:
                        print("portaudio is already installed.")
                elif "openSUSE" in result.stdout:
                    result = subprocess.run(["rpm", "-q", "portaudio"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        os.system("zypper refresh")
                        os.system("zypper install -y portaudio")
                    else:
                        print("portaudio is already installed.")
                else:
                    result = subprocess.run(["dpkg", "-s", "libportaudio2"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        os.system("apt-get update")
                        os.system("apt-get install -y libportaudio2 libasound-dev")
                    else:
                        print("libportaudio2 is already installed.")
            elif sys.platform == "darwin":
                if install_homebrew():
                    result = subprocess.run(["brew", "list", "portaudio"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        os.system("brew update")
                        os.system("brew install portaudio")
                    else:
                        print("portaudio is already installed.")
        elif os.name == "nt":
            pass
        else:
            print("Unsupported operating system")
    except subprocess.CalledProcessError as e:
        print(f"Error installing PortAudio library: {e}")


def uninstall_package(package_name):
    result = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", package_name], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Failed to uninstall {package_name}: {result.stderr}")
    else:
        print(f"Successfully uninstalled {package_name}")


def install_package(package_name):
    result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to install {package_name}: {result.stderr}")
    else:
        print(f"Successfully installed {package_name}")


def manage_discord_packages():
    # 检查并卸载 discord.py 和 discord.py[voice]
    if package_is_installed("discord.py"):
        uninstall_package("discord.py")

    if package_is_installed("discord.py[voice]"):
        uninstall_package("discord.py[voice]")

    # 检查并安装 py-cord[voice]
    if not package_is_installed("py-cord[voice]"):
        install_package("py-cord[voice]")
    else:
        print("py-cord[voice] is already installed")


def package_is_installed(package_name):
    try:
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.P

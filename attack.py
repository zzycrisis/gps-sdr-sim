import subprocess
import os
import time

# 切换到目标目录
#os.chdir("C:\\bladeRF\\x64")
def start():
    # 执行 bladeRF-cli.exe -i 命令
    process = subprocess.Popen(["bladeRF-cli.exe", "-i"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # 后续命令列表
    commands = [
        "set frequency tx1 1575.42M",
        "set samplerate tx1 2.6M",
        "set bandwidth tx1 2.5M",
        "tx config file=gpssim_static.bin format=bin channel=1",
        "tx start",
        "tx start"
    ]
    # 逐条执行后续命令
    for command in commands:
        process.stdin.write(command + '\n')
    # 关闭 stdin
    process.stdin.close()
    # 等待命令执行完成
    process.wait()
    # 获取输出和错误信息
    output, error = process.communicate()
    # 打印输出
    print("Output:", output)
    # 打印错误信息
    if error:
        print("Error:", error)

def stop():
    process = subprocess.Popen(["bladeRF-cli.exe", "-i"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # 执行 tx stop
    process.stdin.write("tx stop\n")
    # 关闭 stdin
    process.stdin.close()
    # 等待命令执行完成
    process.wait()
    # 获取输出和错误信息
    output, error = process.communicate()
    # 打印输出
    print("Output:", output)
    # 打印错误信息
    if error:
        print("Error:", error)

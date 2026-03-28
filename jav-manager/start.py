#!/usr/bin/env python3
"""
JAV Manager 启动脚本
同时启动前端(Vite开发服务器)和后端(Flask)
"""
import os
import sys
import subprocess
import time
import signal

def main():
    # 获取脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 启动后端
    backend_dir = os.path.join(script_dir, 'backend')
    sys.path.insert(0, backend_dir)

    print("=" * 50)
    print("JAV Manager 启动中...")
    print("=" * 50)

    # 启动后端
    print("\n[1/2] 启动后端 (Flask)...")
    backend_env = os.environ.copy()
    backend_env['PYTHONPATH'] = backend_dir

    backend_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=backend_dir,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    # 等待后端启动
    time.sleep(3)

    # 启动前端
    print("\n[2/2] 启动前端 (Vite)...")
    frontend_dir = os.path.join(script_dir, 'frontend')

    frontend_process = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    print("\n" + "=" * 50)
    print("启动完成!")
    print("后端: http://localhost:5000")
    print("前端: http://localhost:5173")
    print("按 Ctrl+C 停止所有服务")
    print("=" * 50)

    def cleanup(signum=None, frame=None):
        print("\n正在停止服务...")
        backend_process.terminate()
        frontend_process.terminate()
        print("已停止")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 监控进程输出
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()

import subprocess
import tempfile
import docker
import os

def run_in_sandbox(code, input_data=None):
    try:
        # 创建一个临时文件来保存代码
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code.encode('utf-8'))
            tmp_filename = tmp_file.name

        # 创建 Docker 客户端
        client = docker.from_env()

        # 运行容器
        container = client.containers.run(
            'python-sandbox',
            command='python /code/script.py',
            volumes={tmp_filename: {'bind': '/code/script.py', 'mode': 'ro'}},
            remove=True,
            mem_limit='100m',
            nano_cpus=500000000,
            stdin_open=True,
            tty=True,
            detach=True
        )

        # 使用 subprocess 执行命令并传递输入
        cmd = ['docker', 'exec', '-i', container.id, 'python', '/code/script.py']
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 传递输入并获取输出
        stdout, stderr = process.communicate(input=input_data)

        # 清理临时文件
        os.unlink(tmp_filename)

        if process.returncode != 0:
            return {
                'returncode': process.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'error': 'Runtime error'
            }

        return {
            'returncode': process.returncode,
            'stdout': stdout,
            'stderr': stderr,
            'success': True
        }

    except Exception as e:
        return {'error': f'Sandbox error: {str(e)}'}
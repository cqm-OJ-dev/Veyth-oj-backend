# 使用现有的 gcc 镜像作为基础镜像
FROM gcc:latest

# 替换为清华大学的 Debian 镜像源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 更新软件包列表并安装额外的工具（例如 make、vim 等）
RUN apt-get update && apt-get install -y \
    make \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /code

# 复制当前目录内容到容器的 /code 目录（可选）
# 如果不需要复制本地文件，可以删除这一行
COPY . /code

# 设置默认用户为非 root 用户（增强安全性）
#RUN useradd -m sandbox && chown -R sandbox:sandbox /code
#USER sandbox

# 默认命令：启动 bash
CMD ["bash"]
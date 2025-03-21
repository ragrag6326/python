# ----------------------------------------------------------------------------------
# tarball 安裝版
python_version=3.8.20

wget https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tgz

tar -zxvf Python-${python_version}.tgz
cd Python-${python_version}

# 可能需要安裝編譯工具
yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel -y

./configure --enable-optimizations
make altinstall

unlink /usr/bin/python3
link python /usr/bin/python3

python3 -V

echo -e "requests
urllib3==1.26.6" > requirements.txt 

python3 -m pip install -r requirements.txt

python3 ldy.py

# ---------------------------------------------------------------------------
# pyenv 
# 1. Automatic installer (Recommended)
curl https://pyenv.run | bash

# 加入 bashrc 並 source
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# 2. 查看 pyenv 可安裝 Python 版本
pyenv install -l

# 可能需要安裝編譯工具
yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel -y

# 3.安裝想選擇的 python 版本
pyenv install -v 3.8

# 4. 查看已經安裝過的 pyenv python 版本
pyenv versions

# 5. 切換 Python 版本，可以選擇用 global、local 或 shell 來執行：
pyenv shell 3.8

echo -e "requests
urllib3==1.26.6" > requirements.txt 

pip3 install -r requirements.txt
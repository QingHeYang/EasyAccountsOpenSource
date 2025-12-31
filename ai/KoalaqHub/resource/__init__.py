# 此文件用于阻止resource目录被当作Python命名空间包
# 防止与标准库resource模块冲突
raise ImportError("This is not a Python package")

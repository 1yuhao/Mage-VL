# Mage-VL 离线传输包

本仓库镜像 Microsoft Mage-VL 的完整模型快照，以每卷最多 **95 MiB（99,614,720 字节）**的普通 Git 文件保存，便于仅能通过 Git 下载的环境获取。不使用 Git LFS，不依赖 Hugging Face 在线下载。

- 来源：https://huggingface.co/microsoft/Mage-VL
- 固定版本：`d88b153285f1633a61b2f693c59c8576693af185`
- 原始文件：78 个，共 10,848,274,369 字节（约 10.85 GB）。
- 模型卡标注许可：Apache-2.0。保留上游文件和模型卡，许可证见 `LICENSE-APACHE-2.0.txt`；附带组件中的许可声明继续适用。
- 本仓库是非官方传输镜像，不代表 Microsoft。

## 内网下载与还原

需要 Git 和 Python 3.9 或更高版本。模型运行依赖不影响下载与还原。

```sh
git clone --depth 1 https://github.com/1yuhao/Mage-VL.git
cd Mage-VL
python3 restore.py
```

Windows 中可以使用 `python restore.py`。脚本先校验全部分卷，再流式解包并校验每个原始文件，输出至 `restored/Mage-VL/`。不会生成额外的完整 tar 中间文件。默认不覆盖已有模型目录。

建议至少预留 35 GB 可用磁盘空间，容纳 Git 对象、分卷和还原后的模型。下载量约 10.85 GB，首次 clone 可能耗时较长。

指定目标目录：

```sh
python3 restore.py --output /path/to/models
```

只验证分卷和归档内容、不解压：

```sh
python3 restore.py --verify-only
```

`manifest.json` 记录来源版本、分卷顺序、文件大小和 SHA-256；`SHA256SUMS` 可供其他校验工具使用。请保持所有分卷的文件名及顺序。

## 本地部署

此包包含模型权重、配置、分词器、自定义模型 Python 代码、神经编解码组件和上游样例。**不包含已安装的 Python/CUDA 运行环境、离线依赖 wheel 或容器镜像**，需根据部署机器的系统、显卡和 CUDA 版本另行准备。

官方推理项目：https://github.com/microsoft/Mage/tree/main/mage_vl

在安装好官方依赖和获取官方推理代码后，将官方命令中的模型标识替换为还原后的绝对路径，例如：

```sh
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
python mage_vl/inference_base.py \
  --mode offline \
  --model /path/to/models/Mage-VL \
  --image mage_vl/assets/examples/dog.jpg \
  --question "Describe this image in detail."
```

模型需要加载随包提供的自定义代码；按官方说明配置 `trust_remote_code=True`。更多说明见 `UPSTREAM-README.md` 与模型目录内原始 README。

## 传输完整性

只有全部分卷下载且 `restore.py` 校验成功后才能使用模型。文件完整性校验不等于 GPU 推理验证；本镜像未验证目标内网机器上的推理环境。

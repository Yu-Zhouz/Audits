## paddleX 安装文档

### 创建 conda 虚拟环境

```shell
conda create --name paddlex python=3.10 -y
conda activate paddlex
```
### 安装paddlepaddle-gpu

1. 安装 paddlepaddle-gpu

版本参考[飞桨官网](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation./docs/zh/install/pip/linux-pip.html)，我们的 CUDA 版本为 12.2，安装命令如下： 

```shell
python -m pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

如果出现错误，大多数情况是网络不够稳定，因此，重新执行即可解决。若是版本问题则需要根据[飞桨官网](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation./docs/zh/install/pip/linux-pip.html)安装适配版本，目前官方已经支持国产芯片部署了。

2. 验证 PaddlePaddle 是否安装成功

使用以下命令可以验证 PaddlePaddle 是否安装成功。

```shell
python -c "import paddle; paddle.utils.run_check()"
```


> [!error] cv2缺少libGL.so.1模块
> **问题描述**
> 
> >ImportError: libgomp. So. 1: cannot open shared object file: No such file or directory
> 
> **解决方案**
> 
> [[cv2缺少libGL.so.1模块]]
> 
> ```bash
> apt-get install sudo
> sudo apt-get install libglvnd-dev libgl1 -y
> ```

> [!error] Title
> 
> **问题描述**
> 
> >/opt/conda/envs/paddlex/lib/python 3.10/site-packages/paddle/utils/cpp_extension/extension_utils. Py:686: UserWarning: No ccache found. Please be aware that recompiling all source files may be required. You can download and install ccache from: https://github.com/ccache/ccache/blob/master/doc/INSTALL.md
> Warnings.Warn (warning_message)
> 
> **解决方案**
> 
> 这个警告信息来自于PaddlePaddle（飞桨）框架，它提示您的系统中没有找到 `ccache`。`ccache` 是一个编译缓存工具，它可以加速C/C++项目的重新编译过程，通过缓存之前的编译结果来避免重复编译相同的源文件。
> 
> ```shell
> (paddlex) python -c "import paddle; paddle.utils.run_check()"
> Running verify PaddlePaddle program ... 
> I1217 07:30:18.775925  1038 pir_interpreter.cc:1480] New Executor is Running ...
> W1217 07:30:18.777175  1038 gpu_resources.cc:119] Please NOTE: device: 0, GPU Compute Capability: 8.0, Driver API Version: 12.2, Runtime API Version: 11.8
> W1217 07:30:18.777792  1038 gpu_resources.cc:164] device: 0, cuDNN Version: 8.9.
> I1217 07:30:19.045917  1038 pir_interpreter.cc:1506] pir interpreter is running by multi-thread mode ...
> PaddlePaddle works well on 1 GPU.
> PaddlePaddle is installed successfully! Let's start deep learning with PaddlePaddle now.
> ```

查看 PaddlePaddle 版本的命令如下：

```shell
python -c "import paddle; print(paddle.__version__)"

# 如果安装成功，将输出如下内容：
3.0.0-beta23.0.0-beta2
```

### 安装PaddleX

参考[官方文档](https://paddlepaddle.github.io/PaddleX/latest/installation/installation.html#222-paddlex)
#### 获取 [PaddleX 源码](https://paddlepaddle.github.io/PaddleX/latest/installation/installation.html#221-paddlex "Permanent link")

接下来，请使用以下命令从 GitHub 获取 PaddleX 最新源码：

```bash
git clone https://github.com/PaddlePaddle/PaddleX.git
```

如果访问 GitHub 网速较慢，可以从 Gitee 下载，命令如下：

```bash
git clone https://gitee.com/paddlepaddle/PaddleX.git
```

获取 PaddleX 最新源码之后，您可以选择Wheel包安装模式或插件安装模式。
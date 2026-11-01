# 来源、许可与发布边界

本仓库为研究复现实验记录，不是三篇论文的官方发行版，也未声明整个集合统一采用 MIT/Apache 许可。

- PhysGaussian：<https://github.com/XPandora/PhysGaussian>；论文 <https://arxiv.org/abs/2311.12198>。
- PAT：Doug L. James、Jernej Barbič、Dinesh K. Pai，Precomputed Acoustic Transfer: Output-sensitive, accurate sound generation for geometrically complex vibration sources，ACM SIGGRAPH 2006，<https://doi.org/10.1145/1179352.1141969>。本项目调用的 ModalSound 是 <https://github.com/cxzheng/ModalSound> 的 2016 教学模块，不是完整 PAT 2006 软件。
- NeuralSound：<https://hellojxt.github.io/NeuralSound/>；<https://github.com/hellojxt/NeuralSound>。
- 原始 Gaussian Splatting：<https://github.com/graphdeco-inria/gaussian-splatting>，保留本地版本完整许可于 `licenses/gaussian-splatting-LICENSE.md`，研究/评估用途限制应参照原文。
- MinkowskiEngine：<https://github.com/NVIDIA/MinkowskiEngine>；使用版本见 `sharing/upstream.json`。
- Eigen 3.3.7：本地依赖头文件保持原 copyright 和 COPYING.*，主要为 MPL2，具体文件例外以原文为准。
- Ficus 输入来自 NeRF Synthetic 公共镜像；固定修订、原项目、原下载地址和逐文件校验在 `01_PhysGaussian/docs/ficus-dataset-provenance.json`。作者场景模型来源在 `01_PhysGaussian/docs/official-model-inventory.json` 与下载记录。

作者源树通过固定提交获取，不在本仓库重复打包；上游许可证及保留声明由获取后的原仓库提供。论文 PDF 和作者数据/预训练输入不重复上传，查阅上述作者/出版方页面。中文阅读笔记中的引用与节选图用于研究说明，原作者权利保留。

本地适配器、训练与科学计算结果都按记录说明其来源；公开可见不意味着获得第三方内容商业使用权。生成的图像/模型依赖相应方法与输入数据，使用时应同时遵守有关来源条款。

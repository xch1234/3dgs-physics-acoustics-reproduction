# CPU 模态振动与声音对照

自建离散质量弹簧实验。只验证模态声音基础；**尚未复现 PAT 的 BEM 与多极子声学传递**。WAV 是观察点速度的可听化，不是真实声压。

## 执行

在项目根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\reproduction\run.ps1 -SkipOfficial
```

使用项目内 `.conda/acoustics` 解释器；环境恢复方式见上一级 README。依赖 NumPy、SciPy、Matplotlib。参数在 `parameters.json`，结果写入 `outputs/`，同名输出会被覆盖。

## 模型与公式

24 个相同质量块沿一维排列，左端通过弹簧连接固定墙，右端自由；每个质量块只有一个平移自由度。它是离散质量弹簧系统，不冒充具体三维材料。

令 B 的对角线为 1、下副对角线为 −1，则 M=mI，K=kBᵀB；刚度单位 N/m，质量单位 kg。
解 Kφᵢ=λᵢMφᵢ，质量归一化 φᵢᵀMφⱼ=δᵢⱼ；ωᵢ=√λᵢ，fᵢ=ωᵢ/(2π)。

离散系统频率有独立闭式参考：

`f_j = sqrt(k/m)/pi * sin((2*j-1)*pi/(4*N+2)), j=1,...,N`。

阻尼 C=αM+βK。初始冲量向量 J 仅在敲击点非零；q(0)=0、q̇(0)=φᵀJ。
每阶满足 q̈ᵢ+2dᵢq̇ᵢ+ωᵢ²qᵢ=0，其中 dᵢ=(α+βλᵢ)/2。
采用欠阻尼精确积分：

`q_i(t) = g_i / omega_d_i * exp(-d_i*t) * sin(omega_d_i*t)`，`omega_d_i = sqrt(omega_i**2-d_i**2)`。

观察点位移 x=Σφᵢqᵢ，速度由解析导数获得。质量、刚度对照保持相同 α、β 阻尼定律；阻尼对照将整个 C 乘 4。

## 验证与音频约定

- 特征对相对残差为 `||Kφ-λMφ||₂ / (||Kφ||₂+|λ| ||Mφ||₂)`，另检查质量正交和闭式频率。
- 用独立物理坐标 DOP853 积分验证基准最初 10 ms，避免仅用同一模态公式互相验证。
- 检查刚度乘 4 / 质量乘 4 的全模态频率比例，以及阻尼衰减、敲击点激发差异、能量非增。
- 保留 `[20, min(20000, 0.45*fs)) Hz` 的固有频率模态。固定左端消除了零模态；本次 24 阶全保留。
- 五个片段统一采样率、时长、冲量、观察位置与全局播放增益，不逐段归一化。
- WAV 为单声道 PCM16，峰值最大 0.85；末尾统一 20 ms 淡出仅用于播放。原始数据未做播放处理。
- 不把播放幅值解释为声压级，不把第一模态 T60 解释成房间混响时间。

## 输出

`baseline.wav`、`stiffness_x4.wav`、`mass_x4.wav`、`damping_x4.wav`、`hit_middle.wav` 为独立片段；`comparison_all.wav` 按此顺序串联，每段后接 0.5 s 静音。

`*_raw.npz` 保存带物理单位的原始响应、模态、矩阵与能量；`*_modes.csv` 保存频率、衰减率和激发强度。
`metrics.json` 包含参数、环境、耗时及实际数值检查结果；`summary.csv` 便于后续读取。
`physical_checks.png`、`waveforms_spectra.png` 为可直接用于组会的图；`RESULTS.zh-CN.md` 为运行自动生成的中文结果。

所有实现均为本地新写，未复制为 PAT 作者代码；上游仓库保存在 `../vendor/`。

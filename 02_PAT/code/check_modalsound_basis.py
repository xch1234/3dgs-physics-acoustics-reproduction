"""Independent SciPy and finite-difference audit of actual C++ basis output."""
import json
from pathlib import Path
import numpy as np
from scipy.special import spherical_jn,spherical_yn,sph_harm
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs/modalsound_basis';rows=np.loadtxt(out/'basis.txt')
n=rows[:,1].astype(int);m=rows[:,2].astype(int);kr=rows[:,3]*rows[:,4]
Y=sph_harm(m,n,rows[:,6],rows[:,5])*np.where(m>0,(-1.)**m,1.)
ref=(spherical_jn(n,kr)+1j*spherical_yn(n,kr))*Y
actual=rows[:,7]+1j*rows[:,8]
derivative=rows[:,9]+1j*rows[:,10];fd=rows[:,11]+1j*rows[:,12]
error=float(np.linalg.norm(actual-ref)/np.linalg.norm(ref))
max_error=float(np.max(np.abs(actual-ref)/np.maximum(np.abs(ref),1e-15)))
grad_error=float(np.linalg.norm(derivative-fd)/np.linalg.norm(fd))
metrics=dict(scope='unchanged ModalSound C++ HelmholtzBasis header, not complete GUI or original PAT application',
    evaluated_basis_values=len(rows),orders=list(range(6)),scipy_relative_L2=error,scipy_max_relative_error=max_error,
    analytic_gradient_vs_centered_difference_relative_L2=grad_error,
    all_checks_passed=error<1e-12 and grad_error<1e-7,
    convention='ModalSound uses h1 and Y_m multiplied by (-1)^m for positive m relative to SciPy; local PAT uses h2 and SciPy Y_m')
payload=json.dumps(metrics,indent=2);(out/'metrics.json').write_text(payload);(ROOT/'docs/modalsound-basis-metrics.json').write_text(payload)
assert metrics['all_checks_passed'],metrics
report=f'''# ModalSound 官方 C++ 基函数运行

已编译并调用未修改的 `ModalSound/src/transfer/HelmholtzBasis.hpp`，使用独立 Conda GSL 2.7 与系统 GCC。此为 SIGGRAPH 2016 教学仓库的数值模块，不是 PAT 2006 原应用，也未假装已编译完整 Qt 图形界面或取得 FastBEM 输入链。

24 个空间点/波数，l=0…5，共 {len(rows)} 个奇异球基函数值，与独立 SciPy 参考相对 L2 误差 {error:.3g}；解析方向导数与中心有限差分相对 L2 误差 {grad_error:.3g}。

重要约定：该代码使用第一类球 Hankel，正 m 球谐比 SciPy 多一个 (-1)^m 因子，负 m 与 SciPy 相同。本项目 PAT 自建实现使用第二类 Hankel 及 SciPy 球谐，二者不能直接混用系数。比较时已显式转换约定。

重跑：先在 WSL 执行 `code/run_modalsound_basis.sh`，再在 acoustics Conda 执行 `python 02_PAT/code/check_modalsound_basis.py`。

- [实际数值指标](modalsound-basis-metrics.json)
- [C++ 输出](../outputs/modalsound_basis/basis.txt)
'''
(ROOT/'docs/MODALSOUND_BASIS.md').write_text(report,encoding='utf-8');print(payload)

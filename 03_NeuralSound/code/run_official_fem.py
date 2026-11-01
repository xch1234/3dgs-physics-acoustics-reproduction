"""Run unchanged NeuralSound FEM assembly and Lanczos code on a tiny CPU case.

The input, clamping adapter, dense reference, and validation are local code.
This is NOT the learned mixed solver, radiation network, or paper benchmark.
"""
from __future__ import annotations

import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[key] = "1"
os.environ["MPLBACKEND"] = "Agg"

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numba
import numpy as np
import scipy
from scipy.linalg import eigh

HERE = Path(__file__).resolve().parent
REPO = HERE / "NeuralSound"
OUT = HERE.parent / "outputs" / "official_fem"
sys.path.insert(0, str(REPO))
from src.classic.fem.femModel import Hexahedron_model, Material
from src.classic.fem.solver import Lanczos_Solver


def build(voxel, length, material):
    model = Hexahedron_model(voxel=voxel, mat=material, length=length)
    K = model.stiff_matrix.tocsr()
    M = model.mass_matrix.tocsr()
    vertices = model.vertices
    fixed = np.flatnonzero(np.isclose(vertices[:, 0], vertices[:, 0].min()))
    fixed_dofs = (fixed[:, None]*3 + np.arange(3)).ravel()
    free_dofs = np.setdiff1d(np.arange(K.shape[0]), fixed_dofs)
    return model, K, M, vertices, free_dofs


def solve(K, M, free):
    kc, mc = K[free][:, free], M[free][:, free]
    # The official sigma=0 Lanczos solver is safe here because clamping removes null modes.
    vals, vecs = Lanczos_Solver(k=12, tol=1e-10, v0=np.random.default_rng(20261031).normal(size=len(free)))(kc, mc)
    order = np.argsort(vals)
    vals, vecs = vals[order], vecs[:, order]
    reference = eigh(kc.toarray(), mc.toarray(), eigvals_only=True)[:12]
    kv, mv = kc @ vecs, mc @ vecs
    residual = np.linalg.norm(kv - mv*vals, axis=0) / (np.linalg.norm(kv, axis=0) + np.abs(vals)*np.linalg.norm(mv, axis=0))
    error = np.max(np.abs(vals/reference-1))
    orth = np.max(np.abs(vecs.T @ mc @ vecs - np.eye(12)))
    assert vals.min() > 0 and error < 1e-7 and residual.max() < 1e-7 and orth < 1e-8
    return vals, vecs, dict(max_relative_eigenpair_residual=float(residual.max()),
                            dense_reference_max_relative_eigenvalue_error=float(error),
                            mass_orthogonality_max_error=float(orth))


def main():
    started = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    voxel = np.zeros((6, 6, 6), dtype=np.int32)
    voxel[:, 2:4, 2:4] = 1
    length = 0.12
    material = Material.Plastic
    np.save(OUT / "input_voxel.npy", voxel)
    model, K, M, vertices, free = build(voxel, length, material)
    vals, vecs, checks = solve(K, M, free)
    frequencies = np.sqrt(vals)/(2*np.pi)
    total_mass = material[0] * int(voxel.sum()) * (length/6)**3
    axis_masses = [float(M[j::3, j::3].sum()) for j in range(3)]
    assert np.allclose(axis_masses, total_mass, rtol=1e-12)
    assert np.allclose(K.toarray(), K.toarray().T, rtol=1e-12, atol=1e-8)
    assert np.allclose(M.toarray(), M.toarray().T, rtol=1e-12, atol=1e-14)

    # Six rigid-body modes must exist before clamping; do not pass them to audio.
    free_vals = eigh(K.toarray(), M.toarray(), eigvals_only=True)
    zero_tol = np.max(np.abs(free_vals)) * 1e-9
    zero_count = int(np.sum(np.abs(free_vals) < zero_tol))
    assert zero_count == 6 and np.min(free_vals) >= -zero_tol
    rigid = model.zero_eigenvalue_vector
    rigid_residual = float(np.linalg.norm(K @ rigid) / (np.linalg.norm(K.toarray()) * np.linalg.norm(rigid)))
    assert rigid_residual < 1e-10

    scales = {}
    for name, mat, size, expected in [
        ("youngs_x4", (material[0], material[1]*4, *material[2:]), length, 2.0),
        ("density_x4", (material[0]*4, *material[1:]), length, 0.5),
        ("size_x2", material, length*2, 0.5),
    ]:
        _, kk, mm, _, ff = build(voxel, size, mat)
        vv, _, local_checks = solve(kk, mm, ff)
        ratio = np.sqrt(vv/vals)
        assert np.allclose(ratio, expected, rtol=1e-7)
        scales[name] = dict(expected_frequency_ratio=expected, frequency_ratios=ratio.tolist(), checks=local_checks)

    np.savez_compressed(OUT / "official_fem_result.npz", voxel=voxel, vertices_m=vertices,
                        K_N_per_m=K.toarray(), M_kg=M.toarray(), free_dofs=free,
                        eigenvalues=vals, frequencies_Hz=frequencies,
                        clamped_modes_mass_normalized=vecs, free_body_eigenvalues=free_vals)
    np.savetxt(OUT / "frequencies.csv", np.column_stack([np.arange(1, 13), frequencies]), delimiter=",", header="mode_1based,undamped_frequency_Hz", comments="")
    hashes = {}
    for relative in ("src/classic/fem/assembler.py", "src/classic/fem/femModel.py", "src/classic/fem/solver.py"):
        hashes[relative] = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
    commit = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
    assert not status, "Upstream tracked code was modified"
    metrics = dict(scope="official traditional FEM assembly + Lanczos, with local input and clamping adapter; not neural inference",
                   all_checks_passed=True, upstream_commit=commit, upstream_tracked_files_unmodified=True,
                   upstream_source_sha256=hashes,
                   input=dict(source="locally generated beam, not paper benchmark", voxel_shape=list(voxel.shape), occupied_voxels=int(voxel.sum()),
                              grid_box_length_m=length, voxel_edge_m=length/6, beam_dimensions_m=[0.12, 0.04, 0.04],
                              density_kg_per_m3=material[0], youngs_modulus_Pa=material[1], poisson_ratio=material[2],
                              boundary="x-min face fixed in all 3 translations"),
                   total_vertices=len(vertices), full_dofs=K.shape[0], free_dofs=len(free),
                   total_mass_kg=total_mass, mass_per_translation_axis_kg=axis_masses,
                   free_body_rigid_mode_count=zero_count, rigid_zero_threshold_eigenvalue=zero_tol,
                   rigid_mode_normalized_stiffness_residual=rigid_residual,
                   frequencies_Hz=frequencies.tolist(), checks=checks, scaling_checks=scales,
                   environment=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__, numba=numba.__version__, device="CPU", threads=1),
                   elapsed_s_including_numba_compile=time.perf_counter()-started)
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    fig = plt.figure(figsize=(12, 4.8), constrained_layout=True)
    ax = fig.add_subplot(121, projection="3d")
    xyz = (np.indices((7, 7, 7)) - 3) * (length/6)
    ax.voxels(*xyz, voxel.astype(bool), facecolors="#4c889c", edgecolor="#d8e0e2", linewidth=0.5)
    fixed_vertices = vertices[np.isclose(vertices[:, 0], vertices[:, 0].min())]
    ax.scatter(*fixed_vertices.T, c="#b24736", s=18, label="Clamped x-min face")
    ax.set(xlabel="x (m)", ylabel="y (m)", zlabel="z (m)", title="Local 24-voxel beam input")
    ax.set_box_aspect(np.ptp(vertices, axis=0))
    ax.set_xticks([-0.06, 0, 0.06])
    ax.set_yticks([-0.02, 0, 0.02])
    ax.set_zticks([-0.02, 0, 0.02])
    ax.tick_params(labelsize=8, pad=1)
    ax.legend(loc="upper left", fontsize=8)
    ax2 = fig.add_subplot(122)
    ax2.plot(np.arange(1, 13), frequencies, "o-", color="#1f6680")
    ax2.set(xlabel="Mode index", ylabel="Natural frequency (Hz)", title="Official FEM + Lanczos: first 12 clamped modes")
    ax2.grid(alpha=0.2)
    fig.suptitle("NeuralSound numerical module only | CPU | no pretrained network", fontsize=13)
    fig.savefig(OUT / "official_fem.png", dpi=170)
    plt.close(fig)
    report = f'''# NeuralSound 官方传统数值模块结果

成功运行提交 `{commit}` 中未修改的 `Hexahedron_model`、有限元矩阵组装及 `Lanczos_Solver`。
输入体素梁、固定端自由度消元、验证与绘图由本地包装脚本提供。未运行神经网络或声辐射模型。

- 输入：6³ 网格中的 24 个占用体素，梁尺寸 0.12×0.04×0.04 m，使用作者 Plastic 参数。
- 节点 {len(vertices)} 个，原始自由度 {K.shape[0]}，固定 x 最小端面后自由度 {len(free)}。
- 总质量 {total_mass:.8f} kg；三个平移方向上的一致质量矩阵求和均匹配理论质量。
- 自由体有 {zero_count} 个刚体零模态；约束后前 12 阶特征值为正。
- 前六阶固有频率（Hz）：{', '.join(f'{x:.4f}' for x in frequencies[:6])}。
- 特征对最大相对残差：{checks['max_relative_eigenpair_residual']:.3e}。
- 与 SciPy 稠密广义特征值求解的最大相对特征值误差：{checks['dense_reference_max_relative_eigenvalue_error']:.3e}。
- Young 模量乘 4 → 频率乘 2；密度乘 4 → 频率减半；所有尺寸乘 2 → 频率减半，前 12 阶均通过。

这里比较的是特征值；对重复特征值未逐元素比较模态向量。该小输入用于数值模块自检，没有网格收敛研究，不能据此证明论文精度。
耗时包含 Numba 首次编译与多组校验，非论文性能基准。CPU 单线程，无 GPU 推理或训练。
见 `official_fem.png`、`metrics.json`、`official_fem_result.npz` 和 `input_voxel.npy`。
'''
    (OUT / "RESULTS.zh-CN.md").write_text(report, encoding="utf-8")
    print(json.dumps({"all_checks_passed": True, "scope": metrics["scope"], "first_six_frequencies_Hz": frequencies[:6].tolist(), "checks": checks, "elapsed_s": metrics["elapsed_s_including_numba_compile"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

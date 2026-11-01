"""Reproducible CPU modal vibration experiment; not an acoustic pressure solver."""
from __future__ import annotations

import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
os.environ["MPLBACKEND"] = "Agg"

import csv
import json
import platform
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.io import wavfile
from scipy.linalg import eigh

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
CASES = [
    ("baseline", "Baseline", 1, 1, 1, 23),
    ("stiffness_x4", "Stiffness x4", 4, 1, 1, 23),
    ("mass_x4", "Mass x4", 1, 4, 1, 23),
    ("damping_x4", "Damping x4", 1, 1, 4, 23),
    ("hit_middle", "Hit at node 12", 1, 1, 1, 11),
]


def matrices(n, mass, stiffness):
    # n moving masses, n springs; left wall fixed, right endpoint free.
    incidence = np.eye(n) - np.eye(n, k=-1)
    return mass * np.eye(n), stiffness * (incidence.T @ incidence)


def eig_checks(K, M, values, vectors):
    kv, mv = K @ vectors, M @ vectors
    residual = np.linalg.norm(kv - mv * values, axis=0) / (
        np.linalg.norm(kv, axis=0) + np.abs(values) * np.linalg.norm(mv, axis=0)
    )
    return float(residual.max()), float(np.max(np.abs(vectors.T @ M @ vectors - np.eye(len(values)))))


def response(t, w, d, g, phi_observer):
    displacement, velocity = np.zeros_like(t), np.zeros_like(t)
    # Exact integration for q(0)=0, q_dot(0)=phi.T @ impulse, underdamped modes.
    for wi, di, gi, po in zip(w, d, g, phi_observer):
        wd = np.sqrt(wi * wi - di * di)
        decay = np.exp(-di * t)
        displacement += po * gi / wd * decay * np.sin(wd * t)
        velocity += po * gi * decay * (np.cos(wd * t) - di / wd * np.sin(wd * t))
    return displacement, velocity


def modal_energy(t, w, d, g):
    energy = np.zeros_like(t)
    for wi, di, gi in zip(w, d, g):
        wd = np.sqrt(wi * wi - di * di)
        decay = np.exp(-di * t)
        q = gi / wd * decay * np.sin(wd * t)
        qd = gi * decay * (np.cos(wd * t) - di / wd * np.sin(wd * t))
        energy += 0.5 * (qd * qd + wi * wi * q * q)
    return energy


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    started = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    p = json.loads((HERE / "parameters.json").read_text(encoding="utf-8"))
    n, fs = p["masses"], p["sample_rate_Hz"]
    if n != 24:
        raise ValueError("Case hit locations currently require 24 masses.")
    t = np.arange(round(p["duration_s"] * fs)) / fs
    et = np.linspace(0, p["duration_s"], 3001)
    results, signals, models, energies = {}, {}, {}, {}
    upper = min(p["maximum_frequency_Hz"], 0.45 * fs)
    for name, label, k_scale, m_scale, d_scale, hit in CASES:
        M, K = matrices(n, p["mass_kg"] * m_scale, p["spring_stiffness_N_per_m"] * k_scale)
        values, phi = eigh(K, M)
        residual, orth_error = eig_checks(K, M, values, phi)
        assert values.min() > 0, "Fixed boundary must remove rigid-body modes"
        w = np.sqrt(values)
        freq = w / (2 * np.pi)
        analytic_f = np.sqrt(p["spring_stiffness_N_per_m"] * k_scale / (p["mass_kg"] * m_scale)) / np.pi * np.sin((2 * np.arange(1, n + 1) - 1) * np.pi / (4 * n + 2))
        analytic_error = float(np.max(np.abs(freq / analytic_f - 1)))
        d = d_scale * (p["rayleigh_alpha_per_s"] + p["rayleigh_beta_s"] * values) / 2
        assert np.all(d < w), "Exact response here assumes underdamping"
        impulse = np.zeros(n)
        impulse[hit] = p["impulse_N_s"]
        g = phi.T @ impulse
        keep = (freq >= p["minimum_frequency_Hz"]) & (freq < upper)
        assert np.any(keep)
        x, v = response(t, w[keep], d[keep], g[keep], phi[-1, keep])
        energy = modal_energy(et, w[keep], d[keep], g[keep])
        assert np.all(np.isfinite(v)) and np.all(np.isfinite(x))
        assert np.max(np.diff(energy)) <= energy[0] * 1e-10
        assert residual < 1e-10 and orth_error < 1e-10 and analytic_error < 1e-10
        np.savez_compressed(OUT / f"{name}_raw.npz", time_s=t, displacement_m=x,
                            velocity_m_per_s=v, M_kg=M, K_N_per_m=K, eigenvalues=values,
                            modes_mass_normalized=phi, frequencies_Hz=freq, retained=keep,
                            modal_initial_velocity=g, decay_rate_per_s=d,
                            energy_time_s=et, energy_J=energy)
        write_csv(OUT / f"{name}_modes.csv",
                  ["mode_1based", "undamped_frequency_Hz", "damped_frequency_Hz", "decay_rate_per_s", "initial_modal_velocity", "observer_mode_value", "retained"],
                  zip(range(1, n + 1), freq, np.sqrt(values - d*d)/(2*np.pi), d, g, phi[-1], keep))
        results[name] = dict(label=label, stiffness_scale=k_scale, mass_scale=m_scale,
                             damping_scale=d_scale, hit_node_1based=hit+1, observer_node_1based=n,
                             first_frequency_Hz=float(freq[0]), highest_frequency_Hz=float(freq[-1]),
                             retained_modes=int(keep.sum()), total_modes=n,
                             eigenpair_max_relative_residual=residual, mass_orthogonality_max_error=orth_error,
                             discrete_analytic_frequency_max_relative_error=analytic_error,
                             first_mode_amplitude_T60_s=float(np.log(1000)/d[0]),
                             initial_retained_energy_J=float(energy[0]), energy_at_1s_J=float(energy[1000]),
                             raw_peak_velocity_m_per_s=float(np.max(np.abs(v))))
        signals[name], models[name], energies[name] = (x, v), (M, K, values, phi, d, g, keep), energy

    # Independent validation against integration in physical coordinates.
    M, K, vals, phi, d, g, keep = models["baseline"]
    C = p["rayleigh_alpha_per_s"] * M + p["rayleigh_beta_s"] * K
    v0 = np.zeros(n)
    v0[-1] = p["impulse_N_s"] / p["mass_kg"]
    tt = np.linspace(0, 0.01, 1001)
    ode = solve_ivp(lambda _, y: np.r_[y[n:], -(K @ y[:n] + C @ y[n:]) / np.diag(M)],
                    (0, tt[-1]), np.r_[np.zeros(n), v0], t_eval=tt, method="DOP853", rtol=1e-10, atol=1e-13)
    assert ode.success
    xx, vv = response(tt, np.sqrt(vals), d, g, phi[-1])
    ode_error = float(np.max(np.abs(vv - ode.y[-1])) / np.max(np.abs(vv)))
    ode_x_error = float(np.max(np.abs(xx - ode.y[n-1])) / np.max(np.abs(xx)))
    assert ode_error < 1e-7 and ode_x_error < 1e-7
    ratios_k = np.sqrt(models["stiffness_x4"][2] / vals)
    ratios_m = np.sqrt(models["mass_x4"][2] / vals)
    assert np.allclose(ratios_k, 2, rtol=1e-10)
    assert np.allclose(ratios_m, 0.5, rtol=1e-10)
    assert np.allclose(models["hit_middle"][2], vals, rtol=1e-12)
    assert not np.allclose(np.abs(models["hit_middle"][5]), np.abs(g))
    assert results["damping_x4"]["first_mode_amplitude_T60_s"] < results["baseline"]["first_mode_amplitude_T60_s"]
    assert energies["damping_x4"][1000] < energies["baseline"][1000]

    peak = max(float(np.max(np.abs(v))) for _, v in signals.values())
    gain = p["playback_peak"] / peak
    fade = np.ones_like(t)
    fade_samples = round(p["playback_tail_fade_s"] * fs)
    fade[-fade_samples:] = np.linspace(1, 0, fade_samples)
    playback = []
    for name, *_ in CASES:
        audio = signals[name][1] * gain * fade
        assert np.isfinite(audio).all() and np.max(np.abs(audio)) < 1
        pcm = np.rint(audio * 32767).astype(np.int16)
        wavfile.write(OUT / f"{name}.wav", fs, pcm)
        read_fs, read_pcm = wavfile.read(OUT / f"{name}.wav")
        assert read_fs == fs and np.array_equal(read_pcm, pcm)
        assert np.max(np.abs(read_pcm.astype(np.int32))) < 32767
        results[name]["playback_peak_full_scale"] = float(np.max(np.abs(pcm.astype(float))) / 32767)
        playback.extend([pcm, np.zeros(fs//2, dtype=np.int16)])
    wavfile.write(OUT / "comparison_all.wav", fs, np.concatenate(playback))

    # Physics figures retain physical amplitudes, never per-case normalization.
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(5, 2, figsize=(12, 12), constrained_layout=True)
    spectral_f = np.fft.rfftfreq(len(t), 1/fs)
    for row, (name, label, *_) in enumerate(CASES):
        v = signals[name][1]
        axes[row, 0].plot(t, v, lw=0.4, color="#1f6680")
        axes[row, 0].set(xlabel="Time (s)", ylabel="Velocity (m/s)", title=label, xlim=(0, 3), ylim=(-peak*1.05, peak*1.05))
        spec = 2 * np.abs(np.fft.rfft(v)) / len(v)
        axes[row, 1].plot(spectral_f, 20*np.log10(np.maximum(spec, 1e-12)), lw=0.7, color="#1f6680")
        axes[row, 1].set(xlabel="Frequency (Hz)", ylabel="Amplitude (dB re 1 m/s)", title=f"{label}: full 3 s FFT", xlim=(0, 10000), ylim=(-125, -35))
    fig.suptitle("Modal vibration sonification | 24 masses | fixed-left / free-right\nRaw observer velocity; one common scale; not radiated sound pressure", fontsize=14)
    fig.savefig(OUT / "waveforms_spectra.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    mode = np.arange(1, n+1)
    for name in ("baseline", "stiffness_x4", "mass_x4"):
        axes[0, 0].plot(mode, np.sqrt(models[name][2])/(2*np.pi), marker=".", label=results[name]["label"])
    axes[0, 0].set(xlabel="Mode index", ylabel="Natural frequency (Hz)", title="Changing stiffness and mass")
    axes[0, 0].legend()
    for name in ("baseline", "damping_x4"):
        axes[0, 1].plot(et, 10*np.log10(np.maximum(energies[name]/energies[name][0], 1e-16)), label=results[name]["label"])
    axes[0, 1].set(xlabel="Time (s)", ylabel="Energy relative to t=0 (dB)", title="Damping and total retained modal energy", ylim=(-100, 0))
    axes[0, 1].legend()
    for name in ("baseline", "hit_middle"):
        axes[1, 0].plot(mode, np.abs(models[name][5]), marker=".", label=results[name]["label"])
    axes[1, 0].set(xlabel="Mode index", ylabel="|Initial modal velocity| (sqrt(kg) m/s)", title="Hit position changes excitation")
    axes[1, 0].legend()
    axes[1, 1].plot(tt*1000, ode.y[-1], label="Physical-coordinate ODE", lw=2)
    axes[1, 1].plot(tt[::10]*1000, vv[::10], ".", label="Modal exact integration", ms=3)
    axes[1, 1].set(xlabel="Time (ms)", ylabel="Velocity (m/s)", title="Independent response validation")
    axes[1, 1].legend()
    fig.suptitle("Physical checks | source: run_experiment.py / parameters.json", fontsize=14)
    fig.savefig(OUT / "physical_checks.png", dpi=170)
    plt.close(fig)

    metrics = dict(scope="self-implemented modal vibration sonification; not PAT/BEM", parameters=p,
                   retained_frequency_band_Hz=[p["minimum_frequency_Hz"], upper],
                   truncation="retain undamped modes in [20 Hz, min(20000 Hz, 0.45*sample_rate)); all current modes retained",
                   playback_common_gain_per_m_per_s=gain, playback="velocity times shared gain; 20 ms end fade; mono PCM16",
                   checks=dict(all_passed=True, ode_velocity_relative_max_error=ode_error,
                               ode_displacement_relative_max_error=ode_x_error,
                               stiffness_frequency_ratio_max_error=float(np.max(np.abs(ratios_k-2))),
                               mass_frequency_ratio_max_error=float(np.max(np.abs(ratios_m-0.5))),
                               energy_nonincreasing=True, wav_roundtrip_passed=True), cases=results,
                   environment=dict(python=sys.version, executable=sys.executable, numpy=np.__version__, scipy=scipy.__version__, matplotlib=matplotlib.__version__, platform=platform.platform(), threads=1),
                   elapsed_s=time.perf_counter()-started)
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = [(name, r["first_frequency_Hz"], r["first_mode_amplitude_T60_s"], r["eigenpair_max_relative_residual"], r["raw_peak_velocity_m_per_s"]) for name, r in results.items()]
    write_csv(OUT / "summary.csv", ["case", "first_frequency_Hz", "first_mode_amplitude_T60_s", "max_relative_residual", "raw_peak_velocity_m_per_s"], rows)
    base = results["baseline"]
    report = f'''# 传统模态声音实验结果

本实验为自建质量弹簧系统的模态振动原理验证与振动可听化，未求解声压，不是 PAT 完整复现。

- 系统：24 个 0.01 kg 质量块、24 根 2×10⁶ N/m 弹簧；左端固定、右端自由。
- 激励：t=0 施加 0.001 N·s 冲量；基准敲击第 24 个质量块，观察第 24 个质量块。
- 阻尼：C = αM + βK，α=4 s⁻¹，β=2×10⁻⁷ s；阻尼对照同时把 α、β 乘 4，即整体 C 乘 4。
- 五组对照只改变指定因素，所有音频为 48 kHz、3 秒，采用同一个播放增益 {gain:.8g} (m/s)⁻¹。
- 保留 20 Hz 至 {upper:g} Hz（不含上界）的模态；当前五组均保留全部 24 个模态，无刚体零模态。

## 数值结果

- 基准第一固有频率：{base['first_frequency_Hz']:.6f} Hz。
- 刚度乘 4：{results['stiffness_x4']['first_frequency_Hz']:.6f} Hz；所有模态频率乘 2。
- 质量乘 4：{results['mass_x4']['first_frequency_Hz']:.6f} Hz；所有模态频率减半。
- 阻尼乘 4：第一模态振幅 T60 从 {base['first_mode_amplitude_T60_s']:.6f} s 减为 {results['damping_x4']['first_mode_amplitude_T60_s']:.6f} s。T60 是解析包络指标，不是混响时间。
- 改为敲击第 12 个质量块：固有频率不变，模态激发强度改变。
- 最大特征对相对残差：{max(r['eigenpair_max_relative_residual'] for r in results.values()):.3e}。
- 模态解与独立物理坐标 DOP853 积分的最大速度相对误差：{ode_error:.3e}（0–10 ms）。
- 五组离散系统频率均通过闭式解校验；质量正交、能量非增、WAV 回读、有限值和无削波检查均通过。

## 如何查看与听音

先看 `physical_checks.png` 和 `waveforms_spectra.png`。逐段听 `baseline.wav`、`stiffness_x4.wav`、`mass_x4.wav`、`damping_x4.wav`、`hit_middle.wav`。
`comparison_all.wav` 按上述顺序串联，每段间隔 0.5 秒；无语音标签。所有片段共享增益，不逐段归一化。
播放文件仅在最后 20 ms 线性淡出避免截断爆音；`*_raw.npz` 保留未经增益和淡出处理的物理位移、速度、矩阵、模态和能量。

## 科学边界

这是离散质量弹簧系统，未声称收敛到真实弹性杆或具体材料。敲击用理想初始冲量；受截断和瞬态影响，音频并非严格带限。
参数变化影响的是固有频率；阻尼也会轻微改变阻尼振荡频率。质量/刚度对照保持 α、β 不变，属于同一 Rayleigh 阻尼定律。
振动频谱以 m/s 为参考，不是声压级。未包含 BEM、多极子传递、听者位置、3DGS 或碰撞求解。
'''
    (OUT / "RESULTS.zh-CN.md").write_text(report, encoding="utf-8")
    print(json.dumps({"all_checks_passed": True, "first_frequency_Hz": base["first_frequency_Hz"], "ode_velocity_relative_error": ode_error, "outputs": str(OUT), "elapsed_s": metrics["elapsed_s"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

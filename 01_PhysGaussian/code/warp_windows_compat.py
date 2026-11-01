"""Warp 0.10.1 NVRTC include-path adapter; no upstream file edits.

The original build_cuda resolves junctions with realpath, producing a Unicode
include path unsupported by this bundled NVRTC. Keep the ASCII junction instead.
All compile flags and the native compiler invocation match Warp 0.10.1.
"""
from pathlib import Path
from importlib.metadata import version
import warp as wp
import warp.build


def enable():
    if version('warp-lang') != '0.10.1':
        raise RuntimeError('This adapter is only validated for Warp 0.10.1')
    include = Path.home()/'.cache'/'3dgs-physgaussian'/'Lib'/'site-packages'/'warp'/'native'
    if not (include/'builtin.h').exists():
        raise RuntimeError('Run via 01_PhysGaussian/run.ps1 to create the ASCII environment junction')
    encoded=str(include).encode('ascii')
    def build_cuda(cu_path,arch,output_path,config='release',verify_fp=False,fast_math=False):
        src=Path(cu_path).read_bytes()
        if wp.config.llvm_cuda:
            wp.context.runtime.llvm.compile_cuda(src,str(cu_path).encode('utf-8'),encoded,str(output_path).encode('utf-8'),False)
        else:
            err=wp.context.runtime.core.cuda_compile_program(src,arch,encoded,config=='debug',wp.config.verbose,verify_fp,fast_math,str(output_path).encode('utf-8'))
            if err:raise RuntimeError(f'Warp NVRTC compile failed: {err}')
    wp.build.build_cuda=build_cuda

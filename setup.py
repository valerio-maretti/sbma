import os
import sys

from setuptools import Extension, setup


def get_ext_modules():
    import numpy

    if sys.platform == "win32":
        # extra_compile_args = ["/O2", "/arch:AVX2", "-std=c++11"]  # "/W4"
        extra_compile_args = ["/std:c++11"]  # "/W4"
    else:
        # extra_compile_args = ["-O2", "-march=native", "-std=c++11"]  # "-Wall"
        extra_compile_args = ["-std=c++11"]  # "-Wall"

    ext_kwargs = {
        "include_dirs": [numpy.get_include()],
        "define_macros": [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        "extra_compile_args": extra_compile_args,
    }

    main_solver = Extension(
        "sbma._solver",
        language="c++",
        sources=[
            "src/sbma/_auxiliaries.cpp",
            "src/sbma/_util.cpp",
            "src/sbma/_starting_point.cpp",
            "src/sbma/_solver.cpp",
        ],
        **ext_kwargs,
    )

    ret = [main_solver]

    if os.environ.get('BUILD_WITH_BRUTE_FORCE'):
        brute_force_solver = Extension(
            "sbma._brute_force_solver",
            language="c++",
            sources=["src/sbma/_brute_force.cpp"],
            **ext_kwargs,
        )
        ret.append(brute_force_solver)

    return ret


if __name__ == "__main__":
    setup(ext_modules=get_ext_modules())

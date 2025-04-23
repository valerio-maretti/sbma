import sys

from setuptools import Extension, setup


def get_ext_modules():
    import numpy

    if sys.platform == "win32":  # no c++11 for cl
        extra_compile_args = ["/O2", "/arch:AVX2"]  # "/W4"
    else:  # for back compatibility
        extra_compile_args = ["-O2", "-march=native", "-std=c++11"]  # "-Wall"

    ext_kwargs = {
        "include_dirs": [numpy.get_include()],
        "define_macros": [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        "extra_compile_args": extra_compile_args,
    }

    return [
        Extension(
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
    ]


if __name__ == "__main__":
    setup(ext_modules=get_ext_modules())

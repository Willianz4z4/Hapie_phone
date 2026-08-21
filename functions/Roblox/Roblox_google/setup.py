from setuptools import setup
from Cython.Build import cythonize

directives = {
    'language_level': "3",
    'bind_c_methods': False,
    'binding': False
}

setup(ext_modules=cythonize("phone_assistance.py", compiler_directives=directives))

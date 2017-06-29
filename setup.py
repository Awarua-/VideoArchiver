from setuptools import setup

setup(
    name="VideoArchiver",
    version='0.1',
    py_modules=['VideoArchiver'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        VideoArchiver=VideoArchiver:read
        ''',
)

from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="nbsplayer",
    version="1.0.0",
    description="A discord.py cog that adds Minecraft note block song playback functionality to your bot.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=["nbsplayer"],
    package_dir={'': "src"},
    url="https://github.com/FaddyManatee/nbsplayer",
    author="FaddyManatee",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Typing :: Typed',
    ]
)

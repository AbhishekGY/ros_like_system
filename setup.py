from setuptools import setup, find_packages

setup(
    name="ros_like_system",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pygame>=2.5.2",
        "asyncio>=3.4.3",
    ],
    author="Abhishek G Y",
    description="A ROS-like distributed system implementation in Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ros-like-system",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.7",
)

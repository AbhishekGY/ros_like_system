from setuptools import setup, find_packages

setup(
    name="custom_ros_node",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "ros_like_system",  # The main package as dependency
    ],
    entry_points={
        'console_scripts': [
            'custom-node=custom_node.my_node:main',
        ],
    },
    author="Abhishek",
    description="A custom node for the ROS-like system",
    python_requires=">=3.7",
)

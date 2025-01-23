# ROS-Like Distributed System

A Python implementation of a distributed system inspired by ROS (Robot Operating System), featuring a publish-subscribe architecture with a central master node for coordination. This system provides a lightweight framework for building distributed robotic applications with real-time communication capabilities.

## Features

- **Master Node Architecture**: Centralized coordination system for managing node registration and message routing
- **Publish-Subscribe Messaging**: Flexible topic-based communication between nodes
- **Asynchronous Communication**: Built on Python's asyncio for efficient concurrent operations
- **Network Serialization**: Robust message passing with automatic serialization
- **Interactive Master Shell**: Command-line interface for system monitoring and control
- **Example Applications**: 
  - Robot arm state publisher
  - Real-time visualization node with PyGame
  - Extensible base node implementation
- **Custom Node Template**: Easy-to-use template for creating new nodes

## Prerequisites

- Python 3.7 or higher
- pip package manager

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ros_like_system.git
cd ros_like_system
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install .
```

## Quick Start

1. Start the master node:
```bash
ros-master
```

2. In separate terminals, run the example nodes:

Run the robot arm state publisher:
```bash
ros-publisher
```

Run the visualization node:
```bash
ros-visualizer
```

## Creating Custom Nodes

1. Copy the template from `templates/custom_ros_node_template`
```bash
cp -r templates/custom_ros_node_template my_custom_node
cd my_custom_node
```

2. Customize your node:
   - Modify the node code in `src/custom_node/my_node.py`
   - Update `setup.py` with your information

3. Install your custom node:
```bash
pip install -e .
```

4. Run your node:
```bash
custom-node
```
More info inside the template folder

## System Architecture

The system consists of three main components:

1. **Master Node**: Manages node registration and message routing
2. **Base Node**: Provides core functionality for all nodes in the system
3. **Network Layer**: Handles communication and message serialization

```
Master Node
    ↑↓
Network Layer
    ↑↓
Node 1 ↔ Node 2 ↔ Node 3
```

## Project Structure
```
ros_like_system/
├── src/
│   ├── core/          # Core networking and message handling
│   ├── nodes/         # Base node implementations
│   └── examples/      # Example applications
├── templates/         # Custom node templates
│   └── custom_ros_node_template/
├── tests/            # Test suite
└── setup.py         # Package configuration
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Creating a New Template
See the existing template in `templates/custom_ros_node_template` as a reference for creating new node templates.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Acknowledgments

- Inspired by ROS (Robot Operating System)
- Built with Python's asyncio library
- Visualization powered by PyGame

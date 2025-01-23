# ROS-like Distributed System

A lightweight implementation of a ROS-like (Robot Operating System) distributed system in Python, featuring a publish-subscribe architecture with a central master node.

## Features

- Central master node for system coordination
- Publish-subscribe messaging pattern
- Asynchronous communication using asyncio
- Network serialization for message passing
- Interactive shell for master node control
- Example nodes including a robot arm visualizer

## Requirements

- Python 3.7+
- pygame
- asyncio

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ros-like-system.git
cd ros-like-system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the master node:
```bash
python src/nodes/master_node.py
```

2. In separate terminals, run example nodes:

Run the arm state publisher:
```bash
python src/examples/test_publisher.py
```

Run the visualizer:
```bash
python src/examples/robot_visualizer.py
```

## Project Structure

- `src/core/`: Core functionality including networking and message handling
- `src/nodes/`: Base node implementations including master node
- `src/examples/`: Example implementations including robot arm simulation
- `tests/`: Test directory (to be implemented)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

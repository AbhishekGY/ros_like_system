# Custom ROS-Like Node Template

This is a template for creating custom nodes for the ROS-like system.

## Installation

1. Make sure you have the main ROS-like system installed:
```bash
pip install ros_like_system
```

2. Install this node package:
```bash
pip install -e .
```

## Usage

1. First, ensure the master node is running.

2. Run this node:
```bash
custom-node
```

## Customizing

1. Modify the `MyCustomNode` class in `src/custom_node/my_node.py`
2. Add your own methods and functionality
3. Update the `setup.py` with your information

## Example Publishing

This template node publishes messages to "custom_topic" every second.
To modify the publishing behavior, edit the `custom_publisher` method.

## Example Subscribing

To add a subscriber, add this to your node:

```python
async def message_callback(self, message):
    print(f"Received: {message.data}")

# In your start_node method:
await self.subscribe("some_topic", self.message_callback)
```

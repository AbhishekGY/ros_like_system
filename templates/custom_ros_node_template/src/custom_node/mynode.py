import asyncio
from ros_like_system.core import NetworkAddress, Message, logger
from ros_like_system.nodes import Node

class MyCustomNode(Node):
    """
    Template for a custom node.
    This example shows how to create a node that publishes messages periodically.
    """
    def __init__(self, name: str, address: NetworkAddress, master_address: NetworkAddress):
        super().__init__(name, address, master_address)
        self.is_running = True

    async def custom_publisher(self):
        """Example publisher that sends messages every second"""
        count = 0
        while self.is_running:
            message = f"Message {count} from {self.name}"
            await self.publish("custom_topic", message)
            count += 1
            await asyncio.sleep(1)

    async def start_node(self):
        """Start the node and its publisher"""
        try:
            # Start the node's network handling
            node_task = await self.start()
            
            # Start the publisher
            publish_task = asyncio.create_task(self.custom_publisher())
            
            # Run until interrupted
            await asyncio.gather(node_task, publish_task)
            
        except KeyboardInterrupt:
            self.is_running = False
            self.stop()
        except Exception as e:
            logger.error(f"Error in node: {e}")
            self.stop()

async def run_node():
    """Initialize and run the custom node"""
    node_address = NetworkAddress("localhost", 0)  # 0 means auto-assign port
    master_address = NetworkAddress("localhost", 11511)
    node = MyCustomNode("custom_node", node_address, master_address)
    await node.start_node()

def main():
    """Entry point for the node"""
    try:
        asyncio.run(run_node())
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()

import asyncio
import math
from ..core.ros_core import NetworkAddress, Message
from ..nodes.node import Node

class ArmStatePublisher(Node):
    def __init__(self, name: str, address: NetworkAddress, master_address: NetworkAddress):
        super().__init__(name, address, master_address)
        self.running = True

    async def publish_arm_state(self):
        """Publish simulated arm movement"""
        time = 0.0
        while self.running:
            # Simulate simple circular motion
            joint1_angle = 0.5 * math.sin(time)  # +/- 0.5 radians for joint 1
            joint2_angle = 0.3 * math.cos(time)  # +/- 0.3 radians for joint 2
            
            state = {
                "joint1_angle": joint1_angle,
                "joint2_angle": joint2_angle
            }
            
            await self.publish("arm_state", state)
            time += 0.05
            await asyncio.sleep(1.0/60)  # 20Hz update rate

async def main():
    node_address = NetworkAddress("localhost", 0)
    master_address = NetworkAddress("localhost", 11511)
    publisher = ArmStatePublisher("arm_state_publisher", node_address, master_address)
    
    # Start node
    node_task = await publisher.start()
    
    # Start publishing task
    publish_task = asyncio.create_task(publisher.publish_arm_state())
    
    try:
        await asyncio.gather(node_task, publish_task)
    except KeyboardInterrupt:
        publisher.running = False
        publisher.stop()

if __name__ == "__main__":
    asyncio.run(main())

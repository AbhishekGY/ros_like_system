import pygame
import asyncio
import threading
from queue import Queue, Empty
import math
from dataclasses import dataclass
from core.ros_core import NetworkAddress, NetworkNode, Message, logger
from nodes.node import Node

@dataclass
class ArmState:
    """Represents the state of the 2-DOF arm"""
    joint1_angle: float  # radians
    joint2_angle: float  # radians

class RobotArmVisualizer(Node):
    def __init__(self, name: str, address: NetworkAddress, master_address: NetworkAddress):
        super().__init__(name, address, master_address)
        self.state_queue = Queue(maxsize=100)
        self.running = True
        
        # Visualization parameters
        self.screen_width = 800
        self.screen_height = 600
        self.background_color = (255, 255, 255)
        self.arm_color = (0, 0, 255)
        
        # Arm parameters
        self.link1_length = 100  # pixels
        self.link2_length = 80   # pixels
        self.origin = (self.screen_width // 2, self.screen_height // 2)

    def handle_arm_state(self, message: Message):
        """Callback for arm state messages"""
        try:
            # Extract joint angles from message data
            state = ArmState(
                joint1_angle=message.data["joint1_angle"],
                joint2_angle=message.data["joint2_angle"]
            )
            try:
                self.state_queue.put_nowait(state)
                logger.debug(f"Queued arm state: {state}")
            except Queue.Full:
                logger.warning("State queue full, dropping message")
        except Exception as e:
            logger.error(f"Error handling arm state: {e}")

def calculate_arm_positions(origin, theta1, theta2, l1, l2):
    """Calculate positions of arm joints given angles"""
    # Convert from standard mathematical angles to pygame coordinates
    # In pygame, y increases downward, so we negate the y components
    
    # First joint position
    joint1_x = origin[0] + l1 * math.cos(theta1)
    joint1_y = origin[1] - l1 * math.sin(theta1)  # Negated for pygame coordinates
    
    # End effector position
    joint2_x = joint1_x + l2 * math.cos(theta1 + theta2)
    joint2_y = joint1_y - l2 * math.sin(theta1 + theta2)  # Negated for pygame coordinates
    
    return (int(joint1_x), int(joint1_y)), (int(joint2_x), int(joint2_y))

def run_visualization(state_queue: Queue, screen_width=800, screen_height=600):
    """Run the PyGame visualization loop"""
    logger.info("Starting visualization loop")
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("2-DOF Robot Arm Visualizer")
    clock = pygame.time.Clock()
    
    # Arm parameters
    link1_length = 100
    link2_length = 80
    origin = (screen_width // 2, screen_height // 2)
    
    running = True
    current_state = ArmState(0.0, 0.0)  # Initial state
    
    while running:
        # Handle PyGame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                return
        
        # Check for new arm state
        try:
            new_state = state_queue.get_nowait()
            current_state = new_state
            logger.debug(f"Updated to new state: {current_state}")
        except Empty:
            pass  # Use previous state if no new state available
            
        # Clear screen
        screen.fill((255, 255, 255))  # White background
        
        # Calculate joint positions
        joint1_pos, joint2_pos = calculate_arm_positions(
            origin,
            current_state.joint1_angle,
            current_state.joint2_angle,
            link1_length,
            link2_length
        )
        
        # Draw arm with thicker lines and larger joints for better visibility
        # Draw base
        pygame.draw.circle(screen, (0, 0, 0), origin, 8)
        
        # Draw link 1
        pygame.draw.line(screen, (0, 0, 255), origin, joint1_pos, 6)
        
        # Draw joint 1
        pygame.draw.circle(screen, (0, 0, 0), joint1_pos, 6)
        
        # Draw link 2
        pygame.draw.line(screen, (0, 0, 255), joint1_pos, joint2_pos, 6)
        
        # Draw end effector
        pygame.draw.circle(screen, (255, 0, 0), joint2_pos, 6)
        
        # Add coordinate axes for reference
        pygame.draw.line(screen, (200, 200, 200), (origin[0]-50, origin[1]), (origin[0]+50, origin[1]), 1)  # X axis
        pygame.draw.line(screen, (200, 200, 200), (origin[0], origin[1]-50), (origin[0], origin[1]+50), 1)  # Y axis
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
        logger.debug(f"Rendered frame with joint angles: {current_state.joint1_angle:.2f}, {current_state.joint2_angle:.2f}")

async def run_node():
    # Create and start visualizer node
    node_address = NetworkAddress("localhost", 0)  # Random port
    master_address = NetworkAddress("localhost", 11511)
    visualizer = RobotArmVisualizer("arm_visualizer", node_address, master_address)
    
    # Start node
    node_task = await visualizer.start()
    
    # Subscribe to arm state topic
    await visualizer.subscribe("arm_state", visualizer.handle_arm_state)
    
    # Start PyGame visualization in separate thread
    viz_thread = threading.Thread(
        target=run_visualization,
        args=(visualizer.state_queue,),
        daemon=True
    )
    viz_thread.start()
    
    try:
        await node_task
    except KeyboardInterrupt:
        visualizer.running = False
        visualizer.stop()
    finally:
        pygame.quit()

def main():
    try:
        asyncio.run(run_node())
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()

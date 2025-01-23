import asyncio
import cmd
import threading
import queue
from ..core.ros_core import NetworkAddress, NetworkNode, Message, logger

class Master:
    """Master node that manages the entire distributed system"""
    def __init__(self, address: NetworkAddress):
        self.address = address
        self.nodes = {}  # node_name -> NetworkAddress
        self.publishers = {}  # topic -> List[(node_name, address)]
        self.subscribers = {}  # topic -> List[(node_name, address)]
        self.network = NetworkNode(address)
        self.command_queue = queue.Queue()
        
    async def handle_message(self, message: Message):
        """Handle incoming messages"""
        try:
            logger.debug(f"Master received message: {message.topic} from {message.source_node}")
            
            if message.topic == "__registration__":
                await self.handle_registration(message)
            elif message.topic == "__publisher_registration__":
                await self.handle_publisher_registration(message)
            elif message.topic == "__subscriber_registration__":
                await self.handle_subscriber_registration(message)
            else:
                await self.distribute_message(message)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
    async def send_registration_confirmation(self, node_name: str, node_address: NetworkAddress):
        """Send registration confirmation to a node"""
        confirmation = Message(
            topic="__registration_confirm__",
            data={"status": "confirmed"},
            source_node="master"
        )
        await self.network.send_message(confirmation, node_address)

    async def handle_registration(self, message: Message):
        """Handle node registration"""
        try:
            data = message.data
            node_name = data["node_name"]
            node_address = NetworkAddress.from_string(data["address"])
            self.nodes[node_name] = node_address
            logger.info(f"Registered node: {node_name} at {node_address}")
            
            # Send confirmation immediately
            confirmation = Message(
                topic="__registration_confirm__",
                data={"status": "confirmed"},
                source_node="master"
            )
            await self.network.send_message(confirmation, node_address)
            
        except Exception as e:
            logger.error(f"Error handling registration: {e}")

    async def handle_publisher_registration(self, message: Message):
        """Handle publisher registration"""
        try:
            data = message.data
            node_name = data["node_name"]
            topic = data["topic"]
            
            if node_name not in self.nodes:
                logger.error(f"Unknown node trying to register publisher: {node_name}")
                return
                
            if topic not in self.publishers:
                self.publishers[topic] = []
            self.publishers[topic].append((node_name, self.nodes[node_name]))
            logger.info(f"Registered publisher: {node_name} for topic {topic}")
            
        except Exception as e:
            logger.error(f"Error handling publisher registration: {e}")

    async def handle_subscriber_registration(self, message: Message):
        """Handle subscriber registration and facilitate connection"""
        try:
            data = message.data
            node_name = data["node_name"]
            topic = data["topic"]
            
            if topic in self.publishers:
                # For each publisher of this topic, send its details to the subscriber
                for pub_name, pub_address in self.publishers[topic]:
                    connection_info = Message(
                        topic="__publisher_info__",
                        data={
                            "publisher_name": pub_name,
                            "publisher_address": str(pub_address),
                            "topic": topic
                        },
                        source_node="master"
                    )
                    # Send publisher's info to the subscriber
                    await self.network.send_message(
                        connection_info, 
                        self.nodes[node_name]
                    )
            
            # Register the subscriber
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append((node_name, self.nodes[node_name]))
            
        except Exception as e:
            logger.error(f"Error handling subscriber registration: {e}")

    async def distribute_message(self, message: Message):
        """Distribute a message to all subscribers of its topic"""
        topic = message.topic
        if topic in self.subscribers:
            for _, sub_address in self.subscribers[topic]:
                await self.network.send_message(message, sub_address)

    async def process_command_queue(self):
        """Process commands from the interactive shell and other sources"""
        while True:
            try:
                command, *args = self.command_queue.get_nowait()
                
                if command == 'registration':
                    await self.handle_registration(args[0])
                elif command == 'publisher_registration':
                    await self.handle_publisher_registration(args[0])
                elif command == 'subscriber_registration':
                    await self.handle_subscriber_registration(args[0])
                elif command == 'distribute':
                    await self.distribute_message(args[0])
                elif command == 'publish':
                    topic, data = args
                    message = Message(topic=topic, data=data, source_node="master")
                    await self.distribute_message(message)
                    
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                
    async def start(self):
        """Start the master node"""
        try:
            # Start network handling
            network_task = asyncio.create_task(
                self.network.start(self.handle_message)
            )
            
            # Start command processing
            command_task = asyncio.create_task(
                self.process_command_queue()
            )
            
            # Wait for both tasks
            await asyncio.gather(network_task, command_task)
            
        except Exception as e:
            logger.error(f"Error in master node: {e}")
            raise

class MasterShell(cmd.Cmd):
    """Interactive shell for the master node"""
    intro = 'Welcome to the ROS-like Master Shell. Type help or ? to list commands.\n'
    prompt = '(master) '

    def __init__(self, master: Master):
        super().__init__()
        self.master = master

    def do_list_nodes(self, arg):
        """List all registered nodes"""
        print("\nRegistered Nodes:")
        for node_name, address in self.master.nodes.items():
            print(f"  {node_name}: {address}")

    def do_list_topics(self, arg):
        """List all topics with their publishers and subscribers"""
        print("\nPublishers:")
        for topic, pubs in self.master.publishers.items():
            print(f"  Topic: {topic}")
            for node_name, addr in pubs:
                print(f"    - {node_name} at {addr}")
        
        print("\nSubscribers:")
        for topic, subs in self.master.subscribers.items():
            print(f"  Topic: {topic}")
            for node_name, addr in subs:
                print(f"    - {node_name} at {addr}")

    def do_publish(self, arg):
        """Publish a message to a topic. Usage: publish <topic> <message>"""
        try:
            topic, message_str = arg.split(' ', 1)
            # Parse the message string as JSON
            try:
                import json
                message_data = json.loads(message_str)
                self.master.command_queue.put(('publish', topic, message_data))
                print(f"Published message to topic: {topic}")
                print(f"Message data: {message_data}")
            except json.JSONDecodeError:
                print("Error: Message must be valid JSON")
                print("Example: publish arm_state {\"joint1_angle\": 0.5, \"joint2_angle\": 0.3}")
        except ValueError:
            print("Usage: publish <topic> <message>")
            print("Example: publish arm_state {\"joint1_angle\": 0.5, \"joint2_angle\": 0.3}")

    def do_exit(self, arg):
        """Exit the master shell"""
        print("Shutting down master node...")
        return True

async def run_master():
    """Run the master node"""
    master_address = NetworkAddress("localhost", 11511)
    master = Master(master_address)
    
    # Start the shell in a separate thread
    shell_thread = threading.Thread(target=lambda: MasterShell(master).cmdloop())
    shell_thread.daemon = True
    shell_thread.start()
    
    # Run the master node
    await master.start()

if __name__ == "__main__":
    try:
        asyncio.run(run_master())
    except KeyboardInterrupt:
        print("\nShutting down...")

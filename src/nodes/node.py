# node.py
import asyncio
import argparse
import signal
from core.ros_core import NetworkAddress, NetworkNode, Message, logger

class Node:
    def __init__(self, name: str, address: NetworkAddress, master_address: NetworkAddress):
        self.name = name
        self.address = address
        self.master_address = master_address
        self.network = NetworkNode(address)
        self.subscribers = {}
        self.publishers = set()  # Track which topics we publish to
        self.is_running = True
        self.registered = asyncio.Event()
        self.actual_address = None  # Store the actual address after server starts
        self.publisher_connections = {}
        self.subscriber_connections = {}

    async def publish(self, topic: str, data):
	    """Publish a message directly to all subscribers"""
	    if topic not in self.publishers:
	        await self.register_publisher(topic)
	        self.publishers.add(topic)
	        
	    message = Message(topic=topic, data=data, source_node=self.name)
	    
	    # Send message to master node for distribution
	    await self.network.send_message(message, self.master_address)
	    
	    # Also send to any direct subscribers
	    if topic in self.publisher_connections:
	        for subscriber, writer in self.publisher_connections[topic].items():
	            print(f"Sending directly to subscriber {subscriber}: {message.topic}")
	            try:
	                await self.network.send_message(message, writer)
	            except Exception as e:
	                logger.error(f"Error sending to subscriber {subscriber}: {e}")

    async def register_publisher(self, topic: str):
        """Register with master as a publisher for a topic"""
        registration = Message(
            topic="__publisher_registration__",
            data={
                "node_name": self.name,
                "topic": topic
            },
            source_node=self.name
        )
        
        success = await self.network.send_message(registration, self.master_address)
        if not success:
            raise ConnectionError(f"Failed to register as publisher for topic: {topic}")
        
    async def handle_message(self, message: Message):
        print(f"DEBUGGING: Message received in handle_message: {message.topic}")
        """Handle incoming messages"""
        try:
            logger.debug(f"Handling message: {message.topic} from {message.source_node}")
            
            if message.topic == "__subscribe__":
                # Handle new subscriber connection
                topic = message.data["topic"]
                subscriber = message.data["subscriber"]
                if topic not in self.publisher_connections:
                    self.publisher_connections[topic] = {}
                # Store writer with subscriber info
                self.publisher_connections[topic][subscriber] = message.writer
                logger.info(f"Added subscriber {subscriber} for topic {topic}")
                return
                
            if message.topic == "__publisher_info__":
                await self.connect_to_publisher(message.data)
                return
            
            if message.topic == "__registration_confirm__":
                self.registered.set()
                logger.info("Registration confirmed by master")
                return           
                
            if message.topic in self.subscribers:
                callback = self.subscribers[message.topic]
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")


    async def wait_for_registration(self, timeout=5):
        """Wait for registration confirmation from master"""
        try:
            await asyncio.wait_for(self.registered.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            logger.error("Registration timeout")
            return False

    async def register_with_master(self):
        """Register this node with the master"""
        registration = Message(
            topic="__registration__",
            data={
                "node_name": self.name,
                "address": str(self.actual_address or self.address)
            },
            source_node=self.name
        )
        
        success = await self.network.send_message(registration, self.master_address)
        if not success:
            raise ConnectionError("Failed to send registration message")
        
        # Wait for confirmation
        if not await self.wait_for_registration():
            raise ConnectionError("Registration not confirmed by master")
            
    async def connect_to_publisher(self, connection_info):
        """Establish direct connection to a publisher"""
        try:
            topic = connection_info["topic"]
            pub_address = NetworkAddress.from_string(connection_info["publisher_address"])
            
            logger.info(f"Connecting to publisher at {pub_address} for topic {topic}")
            
            # Establish direct connection
            reader, writer = await self.network.connect_to(pub_address)
            self.subscriber_connections[topic] = (reader, writer)
            
            # Send subscription request
            subscription = Message(
                topic="__subscribe__",
                data={
                    "topic": topic,
                    "subscriber": self.name
                },
                source_node=self.name
            )
            await self.network.send_message(subscription, pub_address)
            logger.info(f"Sent subscription request for topic {topic}")
            
        except Exception as e:
            logger.error(f"Error connecting to publisher: {e}")

    async def subscribe(self, topic: str, callback):
        """Subscribe to a topic"""
        self.subscribers[topic] = callback
        
        # Register with master
        registration = Message(
            topic="__subscriber_registration__",
            data={
                "node_name": self.name,
                "topic": topic
            },
            source_node=self.name
        )
        success = await self.network.send_message(registration, self.master_address)
        if success:
            logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to subscribe to topic: {topic}")
            raise ConnectionError("Subscription failed")

    async def start(self):
        """Start the node"""
        try:
            # Start network handling
            network_task = asyncio.create_task(
                self.network.start(self.handle_message)
            )
            
            # Give the server a moment to start
            await asyncio.sleep(0.1)
            
            # Get the actual address (with assigned port)
            if self.network.server:
                sockets = self.network.server.sockets
                if sockets:
                    socket = sockets[0]
                    _, port = socket.getsockname()
                    self.actual_address = NetworkAddress(self.address.host, port)
            
            # Register with master
            await self.register_with_master()
            
            return network_task
            
        except Exception as e:
            logger.error(f"Error starting node: {e}")
            self.stop()
            raise

    def stop(self):
        """Stop the node"""
        self.is_running = False
        self.network.stop()

async def main():
    parser = argparse.ArgumentParser(description='Start a ROS-like node')
    parser.add_argument('name', help='Name of the node')
    parser.add_argument('--port', type=int, default=0, help='Port to run on (0 for auto)')
    parser.add_argument('--sub-topic', help='Topic to subscribe to')
    parser.add_argument('--pub-topic', help='Topic to publish to')
    parser.add_argument('--master-port', type=int, default=11511, help='Master node port')
    args = parser.parse_args()

    # Create node
    node_address = NetworkAddress("localhost", args.port)
    master_address = NetworkAddress("localhost", args.master_port)
    node = Node(args.name, node_address, master_address)
    
    try:
        network_task = await node.start()
        
        # Set up subscription if requested
        if args.sub_topic:
            def callback(message: Message):
                print(f"Received on {message.topic}: {message.data}")
            await node.subscribe(args.sub_topic, callback)
            
            try:
                await network_task
            except asyncio.CancelledError:
                logger.info("Subscriber shutting down...")
                
        # Example publisher if requested
        if args.pub_topic:
            # Publish a message every 5 seconds
            async def publish_loop():
                count = 0
                while node.is_running:
                    await node.publish(args.pub_topic, f"Message {count}")
                    count += 1
                    await asyncio.sleep(5)
            
            publish_task = asyncio.create_task(publish_loop())   
            await asyncio.gather(network_task)
        else:
            await network_task
            
    except KeyboardInterrupt:
        node.stop()
    except Exception as e:
        logger.error(f"Error running node: {e}")
        node.stop()
    finally:
        logger.info("Node shutdown complete")
if __name__ == "__main__":
    asyncio.run(main())

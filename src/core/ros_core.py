import asyncio
import json
import logging
import threading
import queue
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NetworkAddress:
    """Represents a network address with host and port"""
    host: str
    port: int
    
    def __str__(self) -> str:
        return f"{self.host}:{self.port}"
    
    @staticmethod
    def from_string(address_str: str) -> 'NetworkAddress':
        host, port = address_str.split(':')
        return NetworkAddress(host, int(port))

class NetworkSerializer:
    """Handles serialization and deserialization of messages"""
    @staticmethod
    def serialize(obj: Any) -> bytes:
        try:
            if hasattr(obj, '__dataclass_fields__'):
                obj_dict = asdict(obj)
                obj_dict['__dataclass__'] = obj.__class__.__name__
            else:
                obj_dict = obj
            return json.dumps(obj_dict).encode('utf-8')
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    @staticmethod
    def deserialize(data: bytes) -> Any:
        try:
            obj_dict = json.loads(data.decode('utf-8'))
            if '__dataclass__' in obj_dict:
                dataclass_name = obj_dict.pop('__dataclass__')
                dataclass_type = globals()[dataclass_name]
                return dataclass_type(**obj_dict)
            return obj_dict
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise

@dataclass
class Message:
    """Base class for all messages in the system"""
    topic: str
    data: Any
    timestamp: float = time.time()
    message_id: str = str(uuid.uuid4())
    source_node: Optional[str] = None
    
    def to_network(self) -> bytes:
        return NetworkSerializer.serialize(self)
    
    @staticmethod
    def from_network(data: bytes) -> 'Message':
        return NetworkSerializer.deserialize(data)

class NodeProtocol(asyncio.Protocol):
    """Network protocol for handling node communications"""
    def __init__(self, message_handler: Callable[[Message], None]):
        self.message_handler = message_handler
        self.buffer = b""
        self.transport = None

    def connection_made(self, transport: asyncio.Transport):
        self.transport = transport
        peer = transport.get_extra_info('peername')
        logger.info(f"Connection established with {peer}")

    def data_received(self, data: bytes):
        self.buffer += data
        try:
            message = Message.from_network(self.buffer)
            self.message_handler(message)
            self.buffer = b""
        except Exception as e:
            if not str(e).startswith("Deserialization error"):
                logger.error(f"Error processing received data: {e}")
                self.buffer = b""

    def connection_lost(self, exc):
        logger.info("Connection lost")
        if exc:
            logger.error(f"Error: {exc}")

class NetworkNode:
    """Base networking functionality for both master and regular nodes"""
    def __init__(self, address: NetworkAddress):
        self.address = address
        self.clients: Dict[str, asyncio.StreamWriter] = {}
        self.server = None
        self.running = False
        self.message_queue = queue.Queue()
        self.connection_retries = 3  # Number of retries for connections
        
    async def start(self, message_handler: Callable[[Message], None]):
        """Start the network node"""
        try:
            # Create server
            self.server = await asyncio.start_server(
                lambda r, w: self.handle_connection(r, w, message_handler),
                self.address.host,
                self.address.port
            )
            
            # Update address with actual port if it was 0
            if self.address.port == 0:
                sockets = self.server.sockets
                if sockets:
                    socket = sockets[0]
                    _, port = socket.getsockname()
                    self.address = NetworkAddress(self.address.host, port)
            
            async with self.server:
                self.running = True
                logger.info(f"Server started on {self.address}")
                await self.server.serve_forever()
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

    async def handle_connection(self, reader: asyncio.StreamReader, 
                      writer: asyncio.StreamWriter, 
                      message_handler: Callable[[Message], None]):
        peer = writer.get_extra_info('peername')
        try:
            while self.running:
                try:
                    # Use readexactly to ensure we get all 4 bytes
                    size_data = await reader.readexactly(4)
                    if not size_data:
                        break
                
                    message_size = int.from_bytes(size_data, 'big')
                    # Read exact message size
                    data = await reader.readexactly(message_size)
                
                    message = Message.from_network(data)
                    message.writer = writer
                
                    if asyncio.iscoroutinefunction(message_handler):
                        await message_handler(message)
                    else:
                        message_handler(message)
                    
                except asyncio.IncompleteReadError:
                    logger.warning(f"Incomplete read from {peer}")
                    break
                except Exception as e:
                    logger.error(f"Error processing message from {peer}: {e}")
                    continue
                    
        finally:
            writer.close()
            await writer.wait_closed()

    async def connect_to(self, remote_address: NetworkAddress) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Connect to a remote node with retries"""
        last_exception = None
        
        for attempt in range(self.connection_retries):
            try:
                reader, writer = await asyncio.open_connection(
                    remote_address.host,
                    remote_address.port
                )
                self.clients[str(remote_address)] = writer
                logger.info(f"Connected to {remote_address}")
                return reader, writer
            except Exception as e:
                last_exception = e
                if attempt < self.connection_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(1)  # Wait before retrying
                
        logger.error(f"Failed to connect to {remote_address} after {self.connection_retries} attempts")
        raise last_exception

    async def send_message(self, message: Message, destination: Union[NetworkAddress, asyncio.StreamWriter]):
        """Send a message to a specific destination"""
        try:
            if isinstance(destination, NetworkAddress):
                writer = self.clients.get(str(destination))
                if not writer:
                    logger.debug(f"No existing connection to {destination}, creating new one")
                    _, writer = await self.connect_to(destination)
            else:
                writer = destination
                logger.debug("Using existing writer connection")

            data = message.to_network()
            size_bytes = len(data).to_bytes(4, 'big')
            
            logger.debug(f"Sending message: size={len(data)} bytes, topic={message.topic}")
            writer.write(size_bytes + data)
            await writer.drain()
            logger.debug("Message sent and drained")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def stop(self):
        """Stop the network node"""
        self.running = False
        if self.server:
            self.server.close()
        
        # Close all client connections
        for writer in self.clients.values():
            try:
                writer.close()
            except Exception:
                pass  # Ignore errors during cleanup

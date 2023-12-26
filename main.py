import json
import uuid

from middleware import udp_broadcast_listener, send_broadcast_message, tcp_unicast_listener
from person import Person
from roomState import RoomState
from ticket import Ticket
from instruction import Instruction
import threading
import queue

TIME_TIL_RESPONSE_IN_SECONDS = 5

if __name__ == "__main__":
    user = Person(str(uuid.uuid4()), False)
    roomState: RoomState = RoomState()
    broadcast_queue = queue.Queue()

    udp_listener_thread = threading.Thread(target=udp_broadcast_listener, args=(broadcast_queue,))
    udp_listener_thread.start()

    tcp_listener_thread = threading.Thread(target=tcp_unicast_listener)
    tcp_listener_thread.start()

    # send join request
    joinInstruction = Instruction("join", user.id)
    message = json.dumps(joinInstruction, default=vars)
    send_broadcast_message(message, 61424)

    # wait for response of the request
    try:
        while True:
            received_message: Instruction = broadcast_queue.get(timeout=TIME_TIL_RESPONSE_IN_SECONDS)
            # ignore my own messages
            if received_message.body != user.id:
                roomState = json.loads(received_message.body, object_hook=lambda d: RoomState())
                print(f"Received message: {received_message.action}:{received_message.body}")
                break
    except queue.Empty:
        print("No message received within the timeout")

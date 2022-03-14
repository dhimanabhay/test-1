import socket
import random
import pickle
import time

seedTiming = int(input("The seed for determining timing arrival of data from the application:"))
if seedTiming < 2 or seedTiming > 32000:
    seedTiming = 111
    print("Input out of range, default value 111 is used.")

seedACKCorr = int(input("Seed for determining if ACKs have been lost or corrupted:"))
if seedACKCorr <= 2 or seedACKCorr >= 32000:
    seedACKCorr = 222
    print("Input out of range, default value 222 is used.")

seedData = int(input("Seed for generating the data in the packet:"))
if seedData <= 2 or seedData >= 32000:
    seedData = 333
    print("Input out of range, default value 333 is used.")

numPackets = int(input("The number of packets to send:"))
if numPackets <= 1 or numPackets >= 100:
    numPackets = 10
    print("Input out of range, default value 10 is used.")

probACKLost = float(input("The probability that a packet or an ACK have been lost:"))
if probACKLost < 0.0 or probACKLost >= 1.0:
    probACKLost = 0.0005
    print("Input out of range, default value 0.0005 is used.")

probACKCorrupt = float(input("The probability that an ACK has been corrupted:"))
if probACKCorrupt < 0.0 or probACKCorrupt >= 1.0:
    probACKCorrupt = 0.001
    print("Input out of range, default value 0.001 is used.")

RTT = float(input("The round trip travel time:"))
if RTT <= 0.1 or RTT > 10.0:
    RTT = 5
    print("Input out of range, default value 5 is used")

if probACKCorrupt < probACKLost:
    probACKLost = 0.0005
    probACKCorrupt = 0.001
    print("Invalid input due to probACKLost > probACKCorrupt, value is set to default instead.")



# Generate random values
def generate_arrival_time():
    return random.uniform(0.0, 6.0)

def generate_ack_state():
    out = random.uniform(0.0, 1.0)
    if out < probACKLost:
        return 2  #ACK lost
    elif probACKCorrupt > out >= probACKLost:
        return 3  #ACK corrupted
    else:
        return 1  #ACK received

def generate_data():
    return random.randrange(25, 100)

serverAddressPort = ("127.0.0.1", 33333)
bufferSize = 1024
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

state = 1
processed_packets = 0
prev_ACK = 1
timer = time.time()

while processed_packets < numPackets:

    # data from application
    if state == 1:
        print("The sender is moving to state WAIT FOR CALL 0 FROM ABOVE")
        data = generate_data()
        segment = [data, 0, False]
        bytesToSend = pickle.dumps(segment)

        print("A packet with sequence number 0 is about to be sent")
        print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(segment[1]) + " isack=" + str(segment[2]))
        print("Starting timeout timer for ACK0")

        ret = UDPClientSocket.sendto(bytesToSend, serverAddressPort)
        if ret == 0:
            time.sleep(5)
            continue

        state = 2

    elif state == 2:
        print("The sender is moving to state WAIT FOR ACK0")
        data = generate_data()
        segment = [data, 0, False]
        bytesToSend = pickle.dumps(segment)

        while True:
            try:
                timer = time.time()
                UDPClientSocket.settimeout(RTT)
                stringMsgFromServer = UDPClientSocket.recvfrom(bufferSize)
            except socket.timeout:
                print("ACK0 timeout timer expired (packet lost)")
                print("A packet with sequence number 0 is about to be resent")
                print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(segment[1]) + " isack=" + str(segment[2]))
                print("Starting timeout timer for ACK0")
                UDPClientSocket.sendto(bytesToSend, serverAddressPort)
                print("The sender is moving back to state WAIT FOR ACK0")
                continue
            msgFromServer = pickle.loads(stringMsgFromServer[0])

            # Duplicate ACK
            if msgFromServer[2] and msgFromServer[1] == 1:
                print("A duplicate ACK1 packet has just been received")
                print("Packet received contains: data = " + str(msgFromServer[0]) + " seq = " + str(msgFromServer[1]) + " isack = " + str(msgFromServer[2]))
                print("Stopping timeout timer for ACK0")

            # If the next message is an ACK 0
            if msgFromServer[2] and msgFromServer[1] == 0:
                ackState = generate_ack_state()
                if ackState == 3:  # ACK is corrupted
                    print("A Corrupted ACK packet has just been received")
                    print("A packet with sequence number 0 is about to be resent")
                    print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(segment[1]) + " isack=" + str(segment[2]))
                    print("Starting timeout timer for ACK0")
                    print("The sender is moving back to state WAIT FOR ACK0")
                    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
                elif ackState == 2:  # ACK is lost
                    remaining_time = (timer + RTT) - time.time()
                    time.sleep(remaining_time)
                    print("ACK0 timeout timer expired (ACK lost)")
                    print("A packet with sequence number 0 is about to be resent")
                    print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(segment[1]) + " isack=" + str(segment[2]))
                    print("Starting timeout timer for ACK0")
                    print("The sender is moving back to state WAIT FOR ACK0")
                    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
                elif ackState == 1:
                    print("An ACK0 packet has just been received")
                    print("Packet received contains: data = " + str(msgFromServer[0]) + " seq = " + str(msgFromServer[1]) + " isack = " + str(msgFromServer[2]))
                    print("Stopping timeout timer for ACK0")
                    state = 3
                    processed_packets += 1
                    break

    #Waiting for data from application
    elif state == 3:
        print("The sender is moving to state WAIT FOR CALL 1 FROM ABOVE")
        data = generate_data()
        segment = [data, 1, False]
        bytesToSend = pickle.dumps(segment)

        print("A packet with sequence number 1 is about to be sent")
        print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(segment[1]) + " isack=" + str(segment[2]))
        print("Starting timeout timer for ACK1")

        if (UDPClientSocket.sendto(bytesToSend, serverAddressPort)) == 0:
            time.sleep(RTT)
            continue

        state = 4

    #Waiting for ACK 1
    elif state == 4:
        print("The sender is moving to state WAIT FOR ACK1")
        data = generate_data()
        segment = [data, 1, False]
        bytesToSend = pickle.dumps(segment)

        while True:
            try:
                timer = time.time()
                UDPClientSocket.settimeout(RTT)
                stringMsgFromServer = UDPClientSocket.recvfrom(bufferSize)
            except socket.timeout:
                # ACK Timeout and re-transmit
                print("ACK1 timeout timer expired (packet lost)")
                # Print necessary messages
                print("A packet with sequence number 1 is about to be resent")
                print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(
                    segment[1]) + " isack=" + str(segment[2]))
                print("Starting timeout timer for ACK1")
                UDPClientSocket.sendto(bytesToSend, serverAddressPort)
                print("The sender is moving back to state WAIT FOR ACK1")
                continue
            msgFromServer = pickle.loads(stringMsgFromServer[0])

            # Duplicate ACK
            if msgFromServer[2] and msgFromServer[1] == 0:
                print("A duplicate ACK0 packet has just been received")
                print("Packet received contains: data = " + str(msgFromServer[0]) + " seq = " + str(msgFromServer[1]) + " isack = " + str(msgFromServer[2]))
                print("Stopping timeout timer for ACK1")

            # If the next message is an ACK 1
            if msgFromServer[2] and msgFromServer[1] == 1:
                ackState = generate_ack_state()
                if ackState == 3:  # ACK is corrupted
                    print("A Corrupted ACK packet has just been received")
                    print("A packet with sequence number 1 is about to be resent")
                    print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(segment[1]) + " isack=" + str(segment[2]))
                    print("Starting timeout timer for ACK1")
                    print("The sender is moving back to state WAIT FOR ACK1")
                    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
                elif ackState == 2:  # ACK is lost
                    remaining_time = (timer + RTT) - time.time()
                    time.sleep(remaining_time)
                    print("ACK1 timeout timer expired (ACK lost)")
                    print("A packet with sequence number 1 is about to be resent")
                    print("Packet to send contains: data = " + str(segment[0]) + " seq = " + str(segment[1]) + " isack=" + str(segment[2]))
                    print("Starting timeout timer for ACK1")
                    print("The sender is moving back to state WAIT FOR ACK1")
                    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
                elif ackState == 1:
                    print("An ACK1 packet has just been received")
                    print("Packet received contains: data = " + str(msgFromServer[0]) + " seq = " + str(msgFromServer[1]) + " isack = " + str(msgFromServer[2]))
                    print("Stopping timeout timer for ACK1")
                    state = 1
                    processed_packets += 1
                    break

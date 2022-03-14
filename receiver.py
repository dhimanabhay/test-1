from socket import *
import pickle
import decimal
import random


RDT3_RECEIVER_PORT = 33333

expectedMessageNumber = 0
packetStatus = 0
seed = 0
probability_packet_corrupted = 0
probability_packet_lost = 0
probability_ack_corrupted = 0


def generate_packet_status():
    global packetStatus
    packetStatus = decimal.Decimal(random.randint(0, 9))/10

def set_packet_status_probabilities():
    global seed, probability_packet_corrupted, probability_packet_lost, probability_ack_corrupted

    seed = int(input("Seed for random number generator: "))
    if (seed < 2 or seed > 32000):
        print("Input out of range, default value 555 is used.")
        seed = 555
    random.seed(seed)

    probability_packet_corrupted = decimal.Decimal(input("Probability that packet is corrupted: "))
    if (probability_packet_corrupted < 0.0 or probability_packet_corrupted > 1.0):
        print("Input out of range, default value 0.2 is used.")
        probability_packet_corrupted = 0.2

    probability_packet_lost = decimal.Decimal(input("Probability that packet is lost: "))
    if (probability_packet_lost < 0.0 or probability_packet_lost >= probability_packet_corrupted):
        print("Input out of range, default value 0.0005 is used.")
        probability_packet_lost = 0.0005    

    probability_ack_corrupted = decimal.Decimal(input("Probability that ACK is corrupted: "))
    if (probability_ack_corrupted <= 0.0 or probability_ack_corrupted > 1.0):
        print("Input out of range, default value 222 is used.")
        probability_ack_corrupted = 0.001

def rdt_receiver_init():
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(("", RDT3_RECEIVER_PORT))
    return serverSocket

def resend_ack(ackNumber, clientAddress, serverSocket):
    print("An ACK" + str(ackNumber) + " is about to be resent")
    print("Packet to send contains: data = 0   seq = " + str(ackNumber) +"  isack = True")
    rawMessage = [0, ackNumber, True]
    message = pickle.dumps(rawMessage)
    serverSocket.sendto(message, clientAddress)

def send_ack(ackNumber, clientAddress, serverSocket):
    print("An ACK" + str(ackNumber) + " is about to be sent")
    print("Packet to send contains: data = 0   seq = " + str(ackNumber) +"  isack = True")
    rawMessage = [0, ackNumber, True]
    message = pickle.dumps(rawMessage)
    serverSocket.sendto(message, clientAddress)

def run_rdt3_receiver():
    global expectedMessageNumber, packetStatus, seed, probability_packet_corrupted, probability_packet_lost, probability_ack_corrupted

    set_packet_status_probabilities()
    serverSocket = rdt_receiver_init()

    while True:
        rawMessage, clientAddress = serverSocket.recvfrom(2048)
        message = pickle.loads(rawMessage)
        generate_packet_status()

        # Check for lost or corrupted packets
        if packetStatus < probability_packet_lost:
            print("A packet has been lost")
            print("The receiver is moving back to state WAIT FOR " + str(expectedMessageNumber) + " FROM BELOW")
        elif packetStatus < probability_packet_corrupted:
            print("A Corrupted packet has just been received")
            print("The receiver is moving back to state WAIT FOR " + str(expectedMessageNumber) + " FROM BELOW")
            if (message[1] == 0):
                resend_ack(1, clientAddress, serverSocket)
            else:
                resend_ack(0, clientAddress, serverSocket)

        # State 0: Expecting F0
        elif expectedMessageNumber == 0:
            if message[1] == 1:
                print("A duplicate packet with sequence number 1 has been received")
                print("Packet received contains: data " + str(message[0]) + "    seq = 1     isack = False")
                resend_ack(1, clientAddress, serverSocket)
                print("The receiver is moving back to state WAIT FOR " + str(expectedMessageNumber) + " FROM BELOW")
            elif message[1] == 0:
                print("A packet with sequence number 0 has been received")
                print("Packet received contains: data " + str(message[0]) + "    seq = 0     isack = False")
                send_ack(0, clientAddress, serverSocket)
                expectedMessageNumber = 1
                print("The receiver is moving to state WAIT FOR " + str(expectedMessageNumber) + " FROM BELOW")

        # State 1: Expecting F1
        elif expectedMessageNumber == 1:
            if message[1] == 0:
                print("A duplicate packet with sequence number 0 has been received")
                print("Packet received contains: data " + str(message[0]) + "    seq = 0     isack = False")
                resend_ack(0, clientAddress, serverSocket)
                print("The receiver is moving back to state WAIT FOR " + str(expectedMessageNumber) + " FROM BELOW")
            elif message[1] == 1:
                print("A duplicate packet with sequence number 1 has been received")
                print("Packet received contains: data " + str(message[0]) + "    seq = 1     isack = False")
                send_ack(1, clientAddress, serverSocket)
                expectedMessageNumber = 0
                print("The receiver is moving to state WAIT FOR " + str(expectedMessageNumber) + " FROM BELOW")


run_rdt3_receiver()
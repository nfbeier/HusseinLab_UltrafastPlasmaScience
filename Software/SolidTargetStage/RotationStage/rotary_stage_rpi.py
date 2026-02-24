#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  9 09:40:02 2025

@author: christina
"""

from guizero import App, Box, Text, TextBox, Combo, PushButton
import numpy as np
import RPi.GPIO as io
import sys, tty, termios, time
from time import sleep
import socket

# Connecting to the PC
HOST = ''  # Listen on all interfaces
PORT = 5000      # Choose a consistent port

# Making the connection to the RPi first
#  Direction pin from controller
DIR = 10

# Step pin
STEP = 8

#Enable pin
ENA = 7

#Trigger pin
TRIG = 11

# using 0/1  to indicate cw or ccw
CW = 1
CCW = 0

#setting up pin layout on pi
io.setmode(io.BOARD)

#Establishing pins in software
io.setup(DIR, io.OUT)
io.setup(STEP, io.OUT)
io.setup(ENA, io.OUT)

# setting the direction to spin
io.output(DIR,CW)

#Setting up the trig pin
io.setup(TRIG, io.IN)

# Setting the enable pin to off until the user turns it on
io.output(ENA, True)

#Establishing connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


#Setting Blank Parameters to be determined by the user
delay = 0
shot_num = 0
freq = 0
shot_mode = ''
step_per_rev = 1600
extra_step = 0

def start_measurement():
    # Timeout for waiting for the trigger signal (in seconds)
    TRIGGER_TIMEOUT = 5.0
    
    if (freq != 0) and (extra_step != 0):    
        extra_steps_2_take = (extra_step) * freq
        triggered = False
        
        if shot_mode == "Single Rotation":
            steps_2_take = int(extra_steps_2_take) + (step_per_rev * 2)
            # Turning on the system
            io.output(ENA, False)
            
            # Waiting for the trigger with a time-based timeout
            start_time = time.time()
            while (time.time() - start_time) < TRIGGER_TIMEOUT:
                sleep(1e-6)
                if io.input(TRIG):
                    for x in range(steps_2_take):
                        io.output(STEP, io.HIGH)
                        sleep(delay)
                        io.output(STEP, io.LOW)
                        sleep(delay)
                    triggered = True
                    break
                    
            # Disabling the system again once done
            io.output(ENA, True)
            
            # Only send DONE if the motor actually ran
            if triggered:
                conn.sendall(b"DONE")
            else:
                conn.sendall(b"FAIL")

        elif (shot_mode == "N Shot") and (shot_num != 0):
            steps_2_take = int(extra_steps_2_take) + int(shot_num)
            
            # Turning on the system
            io.output(ENA, False)
            
            # Waiting for the trigger with a time-based timeout
            start_time = time.time()
            while (time.time() - start_time) < TRIGGER_TIMEOUT:
                sleep(1e-6)
                if io.input(TRIG):
                    for x in range(steps_2_take):
                        io.output(STEP, io.HIGH)
                        sleep(delay)
                        io.output(STEP, io.LOW)
                        sleep(delay)
                    triggered = True
                    break
            
            # Disabling the system again once done
            io.output(ENA, True)
            
            # Only send DONE if the motor actually ran
            if triggered:
                conn.sendall(b"DONE")
            else:
                conn.sendall(b"FAIL")
                

def handle_connection(conn):
    with conn:
        print("Client connected.")
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    print("Client disconnected.")
                    break
                message = data.decode().strip()
                print("Received:", message)

                # Handling the input values now
                global shot_mode
                global delay
                global freq
                global shot_num
                global extra_step
                
                
                if message == "Single Rotation":
                    shot_mode = message
                    #print(shot_mode)
                elif message == "N Shot":
                    shot_mode = message
                    #print(shot_mode)
                elif message == "START":
                    start_measurement()
                elif message == "DISCONNECT":
                    #io.cleanup()
                    sys.exit()
                    break
                
                else:
                    message_1 = message.split('+')[0]
                    if message_1 == "DELAY":
                        value = float(message.split('+')[1])
                        delay = value
                        freq = (1/(2*delay))
                        #print(delay)
                        #print(freq)
                    elif message_1 == "SHOTNO":
                        value = float(message.split('+')[1])
                        shot_num = value
                        #print(shot_num)
                    elif message_1 == "DELAYROT":
                        value = float(message.split('+')[1])
                        extra_step = value
                        #print(extra_step)
                        
                        

            except ConnectionResetError:
                print("Connection was reset by the client.")
                break

          
    
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            global conn
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            handle_connection(conn)

if __name__ == "__main__":
    start_server()

        

io.cleanup()         
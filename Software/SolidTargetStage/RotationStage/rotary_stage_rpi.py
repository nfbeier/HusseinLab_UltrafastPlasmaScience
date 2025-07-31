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

# Setting the enable pin to off until the user turns it on
io.output(ENA, True)

#Setting Blank Parameters to be determined by the user
delay = 0
shot_num = 0
freq = 0
shot_mode = ''
step_per_rev = 400

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
                
                if message == "Single Rotation":
                    shot_mode = message
                elif message == "N Shot":
                    shot_mode = message
                else: 
                    message = message.split('+')[0]
                    value = float(message.split('+')[1])
                    if message == "DELAY":
                        delay = value
                        freq = (1/(2*delay))
                    elif message == "SHOTNO":
                        shot_num = value
                        
                if message == "START":
                    start_measurement()
                    

            except ConnectionResetError:
                print("Connection was reset by the client.")
                break

def start_measurement():
    if freq != 0:
        extra_step = (30*1e-3)*freq
        if shot_mode == "Single Rotation":
            steps_2_take = int(extra_step)+step_per_rev
            # Turning on the system
            io.output(ENA, False)
            for x in range(steps_2_take):
                io.output(STEP, io.HIGH) # sets one coil winding to high
                sleep(delay)
                io.output(STEP, io.LOW)
                sleep(delay)
            #Disabling the system again once the rotations have been done
            io.output(ENA, True)
        elif (shot_mode == "N Shot") and (shot_num != 0):
            steps_2_take = int(extra_step)+ shot_num
            
            # Turning on the system
            io.output(ENA, False)
            for x in range(steps_2_take):
                io.output(STEP, io.HIGH) # sets one coil winding to high
                sleep(delay)
                io.output(STEP, io.LOW)
                sleep(delay)
            #Disabling the system again once the rotations have been done
            io.output(ENA, True)
            
            
    
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            handle_connection(conn)

if __name__ == "__main__":
    start_server()

        

io.cleanup()
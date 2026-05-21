#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  9 09:40:02 2025

@author: christina
"""

from guizero import App, Box, Text, TextBox, Combo, PushButton
import numpy as np
import RPi.GPIO as io
import sys, tty, termios, time, signal
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

# Flag set to True when a clean DISCONNECT is requested
shutdown_requested = False


def gpio_cleanup():
    """Ensure motor is disabled and GPIO is released."""
    try:
        io.output(ENA, True)   # disable motor driver
    except Exception:
        pass
    io.cleanup()
    print("GPIO cleaned up.")


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl-C) and SIGTERM cleanly."""
    print(f"Signal {sig} received – cleaning up GPIO and exiting.")
    gpio_cleanup()
    sys.exit(0)

# Register signal handlers so Ctrl-C / kill always cleans up
signal.signal(signal.SIGINT,  signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def precise_delay(duration):
    """
    Accurate delay for stepper motor step timing.

    time.sleep() on Linux has ~1 ms minimum resolution due to OS scheduling.
    For sub-millisecond delays (e.g. 265 µs at 75 RPM on a 27 mm target) this
    causes the motor to run 3-5× too slowly.

    This function busy-waits using time.perf_counter() for accurate timing.
    For delays >= 5 ms it sleeps for most of the duration first to save CPU
    (useful for very low RPM or N-Shot modes).
    """
    BUSYWAIT_THRESHOLD = 5e-3   # pure busy-wait below 5 ms
    SLEEP_HEADROOM     = 0.5e-3 # leave 0.5 ms of busy-wait at the end of long delays
    end = time.perf_counter() + duration
    if duration > BUSYWAIT_THRESHOLD:
        sleep(duration - SLEEP_HEADROOM)
    while time.perf_counter() < end:
        pass


def start_measurement():
    # Timeout for waiting for the trigger signal (in seconds)
    TRIGGER_TIMEOUT = 5.0
    
    # freq must be set (DELAY command received); extra_step may legitimately be 0
    if freq != 0:
        extra_steps_2_take = (extra_step) * freq
        triggered = False
        
        if shot_mode == "Single Rotation":
            # extra_steps_2_take: steps during the ref_delay pre-window (laser gate not yet open)
            # step_per_rev:        exactly one full rotation while the DG645 laser gate is open
            steps_2_take = int(extra_steps_2_take) + step_per_rev
            # Turning on the system
            io.output(ENA, False)
            
            # Waiting for the trigger with a time-based timeout
            start_time = time.time()
            while (time.time() - start_time) < TRIGGER_TIMEOUT:
                sleep(1e-6)
                if io.input(TRIG):
                    for x in range(steps_2_take):
                        io.output(STEP, io.HIGH)
                        precise_delay(delay)
                        io.output(STEP, io.LOW)
                        precise_delay(delay)
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
                        precise_delay(delay)
                        io.output(STEP, io.LOW)
                        precise_delay(delay)
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
    global shutdown_requested
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
                    # Close this client session and loop back to accept a new
                    # connection. Do NOT set shutdown_requested — the server
                    # stays running so the PC can reconnect without restarting
                    # the RPi script. Use SIGTERM/Ctrl-C to fully stop the server.
                    print("Client disconnected cleanly. Waiting for next connection.")
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
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Allow immediate reuse of the port after a close (avoids
            # "Address already in use" when restarting quickly)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()
            print(f"Server listening on {HOST}:{PORT}")
            while not shutdown_requested:
                global conn
                conn, addr = s.accept()
                print(f"Connected by {addr}")
                handle_connection(conn)
                if shutdown_requested:
                    break
    finally:
        # Always runs: clean shutdown whether DISCONNECT, Ctrl-C, or crash
        gpio_cleanup()

if __name__ == "__main__":
    start_server()
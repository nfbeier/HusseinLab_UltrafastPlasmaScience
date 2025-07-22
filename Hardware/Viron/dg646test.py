import instruments as ik
import time 
import threading
dg = ik.srs.SRSDG645.open_serial('COM7', 9600) 
time.sleep(2)

print(dg.query('*IDN?'))

# set to ext rising and 2v threshold
dg.sendcmd("TSRC 3")
dg.sendcmd("TLVL 2")


class fireThread(threading.Thread):
    def __init__(self):
        super(fireThread, self).__init__()
        dg.sendcmd("*TRG")
        time.sleep(0.1)
        insr = int(dg.query("INSR?"))
        time.sleep(0.1)
        while not insr & 0b1:
            insr = int(dg.query("INSR?"))
            time.sleep(0.05)
        print("yeet we fired")

Fire = threading.Thread(target=fireThread)
print("Starting fire thread")
Fire.start()

Fire.join()
print("fire joined")
    


# reset
dg.sendcmd("IFRS 0")
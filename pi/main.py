from multiprocessing import Process, Queue
from vision.vision_process import vision_process
#from control.controller import controller_process
from control.stupid_alt import controller_process
from comms.serial_manager import serial_process

if __name__ == "__main__":
    ultrasonic_q = Queue()
    vision_q = Queue(maxsize=1)
    motor_q = Queue()
    sound_q = Queue()

    processes = [
        Process(target=vision_process, args=(vision_q,)),
        Process(target=controller_process, args=(ultrasonic_q, vision_q, motor_q, sound_q)),
        Process(target=serial_process, args=(ultrasonic_q, motor_q, sound_q))
    ]

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()

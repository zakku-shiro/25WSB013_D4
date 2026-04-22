from multiprocessing import Process, Queue, Event, Manager
from vision.vision_process import vision_process
from control.controller import controller_process
from comms.serial_manager import serial_process
from sound.sound import sound_process

if __name__ == "__main__":
    ultrasonic_q = Queue()
    vision_q = Queue(maxsize=1)
    motor_q = Queue()
    sound_in_q = Queue()
    sound_out_q = Queue()
    manager = Manager()
    mode_settings = manager.dict()
    init_event = Event()

    processes = [
        Process(target=vision_process, args=(init_event, mode_settings, vision_q,)),
        Process(target=controller_process, args=(init_event, mode_settings, ultrasonic_q, vision_q, motor_q, sound_out_q)),
        Process(target=serial_process, args=(init_event, mode_settings, ultrasonic_q, motor_q, sound_in_q)),
        Process(target=sound_process, args=(init_event, mode_settings, sound_in_q, sound_out_q))
    ]

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()

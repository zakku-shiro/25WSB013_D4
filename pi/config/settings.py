# --- Camera ---
FRAME_WIDTH = 854
FRAME_HEIGHT = 480
FRAME_RATE = 30
WIN_ABS_EXPOSURE = -10
PI_ABS_EXPOSURE = -8

# --- Detection ---
MIN_AREA = 10
MAX_AREA = 80000
MIN_CIRCULARITY_FAR  = 0.75
MIN_CIRCULARITY_CLOSE = 0.25
CIRCULARITY_AREA_SCALE = 12000
VALUE_MIN = 60              
SMOOTHING_ALPHA = 0.3       

# --- Control ---
LOST_TIMEOUT = 3.0          

KP = 0.40
KI = 0.0
KD = 0.12

BASE_SPEED = 180
APPROACH_SPEED = 80
MIN_MOVE = 100              
MAX_MOVE = 255

TRACK_DEADBAND = 10        
AREA_THRESHOLD = 5000
APPROACH_DISTANCE = 40

# --- Servo Sweep ---
SERVO_SWEEP_INTERVAL = 2.0  

# --- Ultrasonic ---
US_STOP_DISTANCE = 15
US_CLOSE_MIN = 15        
US_CLOSE_MAX = 40           # cm - above this is not a close obstacle
US_JUMP_THRESHOLD = 30      # cm - max believable single-frame jump
US_HITS_REQUIRED = 4        # consecutive stable hits to trigger VERIFY
US_TIMEOUT = 1.0            # seconds of silence before clearing hit counter

DISTANCE_QUEUE_SIZE = 5
DISTANCE_SMOOTHING_ALPHA = 0.3
STABILITY_THRESHOLD = 3.0   # cm - max variance in queue to be considered stable

# --- Verify State ---
VERIFY_TIMEOUT = 0.5        # seconds - if vision doesn't confirm, treat as obstacle
VERIFY_MIN_HITS = 3         # vision area confirmations needed to enter ULTRASONIC

# --- Sound System ---
NUM_MICS = 3
SAMPLE_RATE = 4000  # estimated sample rate
MIC_BUFFER_SIZE = 1024
MIC_CONFIDENCE_THRESHOLD = 0.25
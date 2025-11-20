import cv2
from matplotlib import pyplot as plt

image_smile_rgb = cv2.imread("res/smile.jpg", cv2.IMREAD_COLOR_RGB)
image_no_smile_rgb = cv2.imread("res/no-smile.jpg", cv2.IMREAD_COLOR_RGB)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")

def detect_smiles(image_rgb):
    image_gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    faces_found = face_cascade.detectMultiScale(image_gray, 1.3, 5)
    for (face_x, face_y, face_w, face_h) in faces_found:
        cv2.rectangle(image_rgb, (face_x, face_y), (face_x + face_w, face_y + face_h), (0, 0, 255), 5)
        image_face_bounded = image_gray[face_y:(face_y + face_h), face_x:(face_x + face_w)]

        smiles_found = smile_cascade.detectMultiScale(image_face_bounded, 2.1, 27, minSize=(100, 100))
        for (smile_x, smile_y, smile_w, smile_h) in smiles_found:
            cv2.rectangle(image_rgb, (face_x + smile_x, face_y + smile_y),
                          (face_x + smile_x + smile_w, face_y + smile_y + smile_h), (0, 255, 0), 3)

detect_smiles(image_smile_rgb)
detect_smiles(image_no_smile_rgb)

plt.suptitle("OpenCV Smile Detection (with size adjustment)")
plt.subplot(121)
plt.title("Smiling Image")
plt.imshow(image_smile_rgb)
plt.subplot(122)
plt.title("Smile-less Image")
plt.imshow(image_no_smile_rgb)
plt.show()
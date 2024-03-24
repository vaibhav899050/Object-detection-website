from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import cv2

from datetime import datetime 

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(input_path, output_path):
    # Example image processing (convert to grayscale)
    image = cv2.imread(input_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(output_path, gray_image)
# classNames = {
#     0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
#     5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
#     10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench',
#     14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow',
#     20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack',
#     25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee',
#     30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat',
#     35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket',
#     39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife',
#     44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich',
#     49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza',
#     54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant',
#     59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop',
#     64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave',
#     69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book',
#     74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier',
#     79: 'toothbrush'
# }
model_path = "models/frozen_inference_graph.pb"
config_path = "models/ssd_mobilenet_v3_large_coco.pbtxt"
def get_image_description(image_path):
    class_names = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck",
                   "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
                   "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
                   "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
                   "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
                   "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
                   "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
                   "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant",
                   "bed", "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard",
                   "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock",
                   "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]

    # Load pre-trained model and configuration for object detection
    net = cv2.dnn_DetectionModel(model_path, config_path)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)

    # Load image
    image = cv2.imread(image_path)

    # Perform object detection
    classes, confidences, boxes = net.detect(image, confThreshold=0.5)

    # Extract and return detected objects as a string
    detected_objects = []
    if len(classes) > 0:
        for class_id, confidence, box in zip(classes.flatten(), confidences.flatten(), boxes):
            detected_objects.append(class_names[class_id - 1])

    return ', '.join(detected_objects)
    
    
    
    

@app.route('/')
def index():
    # Get the list of uploaded images
    uploaded_images = os.listdir(app.config['UPLOAD_FOLDER'])
    # Get the last uploaded image
    if uploaded_images:
        last_uploaded_image = uploaded_images[-1]
        # Process the last uploaded image
        process_image_path = os.path.join(app.config['PROCESSED_FOLDER'], last_uploaded_image)
        if not os.path.exists(process_image_path):
            original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], last_uploaded_image)
            process_image(original_image_path, process_image_path)
        # Get image descriptions
        description_original = get_image_description(os.path.join(app.config['UPLOAD_FOLDER'], last_uploaded_image))
        description_processed = get_image_description(process_image_path)
    else:
        last_uploaded_image = None
        description_original = None
        description_processed = None
    
    return render_template('index.html', last_uploaded_image=last_uploaded_image, 
                           description_original=description_original,
                           description_processed=description_processed)

# 
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            
            # Append timestamp to filename to avoid overwriting existing files
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{filename}"
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            
            file.save(input_path)
            return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

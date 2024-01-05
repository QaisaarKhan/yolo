# USAGE
# python yolo.py --image images/baggage_claim.jpg --yolo yolo-coco

# import the necessary packages
import numpy as np
import argparse
import urllib
import time
import cv2
import os

class Yolo:

	def __init__(self, printing=False):

		self.argparser()

		self.printing = printing

		# load the COCO class labels our YOLO model was trained on
		self.labelsPath = os.path.sep.join([self.args["yolo"], "coco.names"])
		# self.labelsPath = os.path.sep.join([self.args["yolo"], "imagenet.shortnames.list"])
		# self.labelsPath = '/home/codistan/Desktop/yolo-server/yolo-object-detection/imagenet/imagenet.shortnames.list'
		self.LABELS = open(self.labelsPath).read().strip().split("\n")
		# print("SELF.LABELS: ", self.LABELS)

		# initialize a list of colors to represent each possible class label
		np.random.seed(42)
		self.COLORS = np.random.randint(0, 255, size=(len(self.LABELS), 3),
			dtype="uint8")

		# derive the paths to the YOLO weights and model configuration
		self.weightsPath = os.path.sep.join([self.args["yolo"], "yolov3.weights"])
		self.configPath = os.path.sep.join([self.args["yolo"], "yolov3.cfg"])

		# self.weightsPath = os.path.sep.join([self.args["yolo"], "darknet19.weights"])
		# self.configPath = os.path.sep.join([self.args["yolo"], "darknet19.cfg"])
		# self.weightsPath = '/home/codistan/Desktop/yolo-server/yolo-object-detection/imagenet/darknet19.weights'
		# self.configPath = '/home/codistan/Desktop/yolo-server/yolo-object-detection/imagenet/darknet19.cfg'

		# load our YOLO object detector trained on COCO dataset (80 classes)
		print("[INFO] loading YOLO from disk...")
		self.net = cv2.dnn.readNet(self.configPath, self.weightsPath)
		print("[INFO] YOLO loaded...")

		# determine only the *output* layer names that we need from YOLO
		self.ln = self.net.getLayerNames()
		# print("Layer names - NN -: ", self.ln)

		self.ln = [self.ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

		# print("OUTPUT Layer names - NN -: ", self.ln)


	def argparser(self):
		# construct the argument parse and parse the arguments
		self.ap = argparse.ArgumentParser()
		# self.ap.add_argument("-i", "--image", required=True,
		# 	help="path to input image")
		self.ap.add_argument("-y", "--yolo", required=True,
			help="base path to YOLO directory")
		self.ap.add_argument("-c", "--confidence", type=float, default=0.5,
			help="minimum probability to filter weak detections")
		self.ap.add_argument("-t", "--threshold", type=float, default=0.3,
			help="threshold when applyong non-maxima suppression")

		self.args = vars(self.ap.parse_args())

	
	# METHOD #1: OpenCV, NumPy, and urllib
	def url_to_image(self, url):
	# download the image, convert it to a NumPy array, and then read
	# it into OpenCV format
		resp = urllib.urlopen(url)
		image = np.asarray(bytearray(resp.read()), dtype="uint8")
		image = cv2.imdecode(image, cv2.IMREAD_COLOR)

		# return the image
		return image

	def download_image(self, url):
	# download image from storage
		start = time.time()
		# image = url_to_image('https://firebasestorage.googleapis.com/v0/b/madness-29ef4.appspot.com/o/CloudVision%2Fmadhunt%2Fcat100.jpg?alt=media&token=c1e8a4d9-0887-4caf-949e-43155a8d0fe5')
		image = self.url_to_image(url)
		end = time.time()
		if self.printing==True: print("[INFO] Download took {:.6f} seconds".format(end - start))

		(H, W) = image.shape[:2]

		return (image, H, W)

	def forward_pass(self, image):
		# load our input image and grab its spatial dimensions
		
		# image = cv2.imread(args["image"])
		# (H, W) = image.shape[:2]

		# print("Image: ", image)

		# construct a blob from the input image and then perform a forward
		# pass of the YOLO object detector, giving us our bounding boxes and
		# associated probabilities
		blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
			swapRB=True, crop=False)
		self.net.setInput(blob)
		start = time.time()
		layerOutputs = self.net.forward(self.ln)
		end = time.time()

		# show timing information on YOLO
		if self.printing==True: print("[INFO] YOLO took {:.6f} seconds".format(end - start))

		# print("layerOutputs: ", layerOutputs)

		return layerOutputs

	def bounding_boxes(self, layerOutputs, H, W):

		# initialize our lists of detected bounding boxes, confidences, and
		# class IDs, respectively
		boxes = []
		confidences = []
		classIDs = []

		# loop over each of the layer outputs
		for output in layerOutputs:
			# loop over each of the detections
			for detection in output:
				# extract the class ID and confidence (i.e., probability) of
				# the current object detection
				scores = detection[5:]
				classID = np.argmax(scores)
				confidence = scores[classID]	

				# filter out weak predictions by ensuring the detected
				# probability is greater than the minimum probability
				if confidence > self.args["confidence"]:
					# if self.printing==True: print("confidence: ", confidence)

					# scale the bounding box coordinates back relative to the
					# size of the image, keeping in mind that YOLO actually
					# returns the center (x, y)-coordinates of the bounding
					# box followed by the boxes' width and height
			
					box = detection[0:4] * np.array([W, H, W, H])
					(centerX, centerY, width, height) = box.astype("int")

					# use the center (x, y)-coordinates to derive the top and
					# and left corner of the bounding box
					x = int(centerX - (width / 2))
					y = int(centerY - (height / 2))

					# update our list of bounding box coordinates, confidences,
					# and class IDs
					boxes.append([x, y, int(width), int(height)])
					confidences.append(float(confidence))
					classIDs.append(classID)

		if self.printing==True: print("Class ids : ", classIDs)

		return (boxes, confidences, classIDs)

	def print_original_labels(self, classIDs):
		for i in classIDs:
			print("orig label: ", self.LABELS[i])


	def non_max_supression(self, boxes, confidences, classIDs):
		# apply non-maxima suppression to suppress weak, overlapping bounding
		# boxes
		idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.args["confidence"],
			self.args["threshold"])

		# print("idxs: ", idxs)


		# self.print_original_labels(classIDs)

		labels_list = []

		if len(idxs) > 0:
			# loop over the indexes we are keeping
			for i in idxs.flatten():
				# print("box label non-max supression: ", self.LABELS[classIDs[i]])
				if self.LABELS[classIDs[i]] not in labels_list:
					labels_list.append(self.LABELS[classIDs[i]])

				text = "{}: {:.4f}".format(self.LABELS[classIDs[i]], confidences[i])
				if self.printing==True: print("label: ", text)

		print("labels_list: ", labels_list)

		return labels_list


	def object_detection(self, url):
		img, H, W = self.download_image(url)
		layerOutputs= self.forward_pass(img)
		boxes, confidences, classIDs = self.bounding_boxes(layerOutputs, H, W)
		labels_list = self.non_max_supression(boxes, confidences, classIDs)
		return labels_list

# yolo_obj = Yolo()
# labels_list = yolo_obj.object_detection('https://firebasestorage.googleapis.com/v0/b/madness-29ef4.appspot.com/o/CloudVision%2Fmadhunt%2Fimages_dining_table.jpg?alt=media&token=a102193f-d3d7-4dcf-9734-6eb385561758')
# labels_list = yolo_obj.object_detection('https://firebasestorage.googleapis.com/v0/b/madness-29ef4.appspot.com/o/CloudVision%2Fmadhunt%2Fimages_baggage_claim.jpg?alt=media&token=036a0950-c3b0-4965-90f0-4e73195e80ab')

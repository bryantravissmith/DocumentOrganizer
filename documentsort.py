#/usr/bin/python
import argparse
import os
import glob
import numpy as np
import cv2
from wand.image import Image
from wand.color import Color
import shutil

def convertPdfToImage(file_loc):
	new_dir = file_loc.split(".")[0]
	if not os.path.exists(new_dir):
		os.makedirs(new_dir)
	doc = Image(filename=file_loc,resolution=200)
	doc.compression_quality = 80
	for i, page in enumerate(doc.sequence):
		with Image(page) as page_image:
			page_image.alpha_channel = False
			page_image.background_color = Color('white')
			save_location =  new_dir+"/img-{}.jpg".format(str(i).zfill(4))
			page_image.save(filename=save_location)


def readImagesForPdf(file_loc,img_read_method=cv2.IMREAD_UNCHANGED):
    new_dir = file_loc.split(".")[0]
    images = []
    for f in glob.glob(new_dir+"/*.jpg"):
        images.append(cv2.imread(f,img_read_method))
    return images

def detectKeyInImage(key_image,doc_image,max_features=1000000,min_matches=10):
	
	sift = cv2.ORB_create() #cv2.SIFT()
	sift.setMaxFeatures(max_features)
	# find the keypoints and descriptors with SIFT
	kp1, des1 = sift.detectAndCompute(key_image,None)
	kp2, des2 = sift.detectAndCompute(doc_image,None)

	#FLANN_INDEX_KDTREE = 0
	#index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
	#search_params = dict(checks = 500)
	if not kp1:
		return False
	if not kp2:
		return False

	FLANN_INDEX_KDTREE = 0
	index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 50)
	search_params = dict(checks=50)   # or pass empty dictionary

	flann = cv2.FlannBasedMatcher(index_params,search_params)

	matches = flann.knnMatch(np.float32(des1),np.float32(des2),k=2)

	# ratio test as per Lowe's paper
	count = 0
	for i,(m,n) in enumerate(matches):
	    if m.distance < 0.7*n.distance:
	        count += 1
	
	if count > min_matches:
		return True
	return False


def check_file_directory(key,value):
	if not value:
		parser.error("--{} must to set to a directory".format(key))
	elif not os.path.isdir(value):
		parser.error("--{} must be set to a valid directory".format(key))
	else:
		has_files = False
		for dirpath, dirnames, files in os.walk(value):
			if files:
				has_files = True
				break
		if not has_files:
			parser.error("--{} must contain files".format(key))

def check_sort_directory(key,value):
	if not value:
		parser.error("--{} must to set to a directory".format(key))
	else:
		if not os.path.isdir(value):
			print "{} does not exist. Create path?[y/n]".format(value)
			response = raw_input().lower()
			if response == "y":
				os.mkdir(value)
			else:
				parser.error("--{} must be set to a valid directory".format(key))
		
		has_files = False
		for dirpath, dirnames, files in os.walk(value):
			if files:
				has_files = True
				break

		if has_files:
			parser.error("--{} must be an empty directory".format(key))

def valid_image(imgfile_name):
	valid_endings = [".jpg",".png"]
	valid = False
	for ending in valid_endings:
		if ending in imgfile_name:
			return True
	return False

parser = argparse.ArgumentParser()
parser.add_argument("--key_dir", type=str, help="directory where keys are located")
parser.add_argument("--doc_dir", type=str, help="directory where documents are located")
parser.add_argument("--sort_dir", type=str, help="directory where sorted documents are located")

args = parser.parse_args()

for key,value in vars(args).iteritems():
	if key in ['key_dir','doc_dir']:
		check_file_directory(key,value)
	if key in ['sort_dir']:
		check_sort_directory(key, value)


if __name__ == "__main__":
	
	#Generate a list of keys to search for
	key_img_dict = dict()
	for i, (dirpath, dirnames, files) in enumerate(os.walk(args.key_dir)):
		if i > 0:
			valid_files = [f for f in files if valid_image(f)]
			valid_imgs = [cv2.imread(dirpath+"/"+f,0) for f in valid_files]
			key_name = dirpath.split(os.path.sep)[-1]
			key_img_dict[key_name] = valid_imgs
			#Create sorted key folders
			if not os.path.isdir(args.sort_dir+os.path.sep+key_name):
				os.mkdir(args.sort_dir+os.path.sep+key_name)
	#Create unsorted key folder
	if not os.path.isdir(args.sort_dir+os.path.sep+"unsorted"):
		os.mkdir(args.sort_dir+os.path.sep+"unsorted")
	

	#Generate a list of documents
	documents = glob.glob(args.doc_dir+os.path.sep+"*.pdf")

	#Convert documents to images
	print "Converting Documents..."
	for doc in documents:
		print "Converting {} to images...".format(doc)
		convertPdfToImage(doc)
		print "Sorting {} into folders".format(doc)
		images = readImagesForPdf(doc,0)
		classified = False
		for key_name,key_images in key_img_dict.iteritems():
			for key_image in key_images:
				for doc_image in images:
					if detectKeyInImage(key_image, doc_image):
						print "{} is classified as {}".format(doc,key_name)
						doc_name = doc.split(os.path.sep)[-1]
						new_loc = args.sort_dir+os.path.sep+key_name+os.path.sep+doc_name
						shutil.copyfile(doc,new_loc)
						classified = True
					
					if classified:
						break
				if classified:
					break
			if classified:
				break

		if not classified:
			print "{} is unclassified".format(doc)
			new_loc = args.sort_dir+os.path.sep+"unsorted"+os.path.sep+doc_name
			shutil.copyfile(doc,new_loc)

	#TO DO
	

	#Iterate Trough Keys
	#Iterate Through Key Images
	#Iterate Through Documents
	#Iterate Through Document Images
	#If Key Image/Doc Image Match Move to sorted folder

	#Done




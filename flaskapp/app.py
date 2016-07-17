from flask import Flask, request, flash, url_for, redirect, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import uuid
import os
import argparse
import glob
import numpy as np
import cv2
from wand.image import Image
from wand.color import Color
import shutil
import subprocess
import threading

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = "random string"
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

matches = db.Table('matches',
    db.Column('doc_id', db.Integer, db.ForeignKey('doc.id')),
    db.Column('key_id', db.Integer, db.ForeignKey('key.id'))
)

class doc(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50))
	uuid = db.Column(db.String(50))
	file_location = db.Column(db.String(250))
	keys = db.relationship('key', secondary=matches,backref=db.backref('doc'))
	text = db.Column(db.Text)

	def __repr__(self):
		  return '{}'.format(self.name)

	def __str__(self):
		  return '{}'.format(self.name)



class key(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50))
	terms = db.relationship('key_term', order_by='key_term.term', backref='key')
	imgs = db.relationship('key_img', order_by='key_img.file_location', backref='key')
	docs = db.relationship('doc', secondary=matches,backref=db.backref('key'))

	def __repr__(self):
		for img in self.imgs:
			print str(img)
		for term in self.terms:
			print str(term)
		return '<Key: {},{},{}>'.format(self.name," ".join([str(term) for term in self.terms])," ".join([str(img) for img in self.imgs]))

class key_img(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	file_location = db.Column(db.String(250))
	uuid = db.Column(db.String(50))
	key_id = db.Column(db.Integer, db.ForeignKey('key.id'))

	def __repr__(self):
		  return '{}'.format(self.file_location)

	def __str__(self):
		  return '{}'.format(self.file_location)

class key_term(db.Model):
	id = db.Column(db.Integer,  primary_key=True)
	term = db.Column(db.String(50))
	key_id = db.Column(db.Integer, db.ForeignKey('key.id'))

	def __repr__(self):
		  return '{}'.format(self.term)

	def __str__(self):
		  return '{}'.format(self.term)

def allowed_file(filename):
	 return '.' in filename and \
			  filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def detectKeyInImage(key_image_location,doc_image_location,max_features=1000000,min_matches=10):
	print key_image_location, doc_image_location
	key_image = cv2.imread(key_image_location,0)
	doc_image = cv2.imread(doc_image_location,0)

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

def get_doc_img_locations(doc):
	folder, ending = doc.file_location.rsplit(".",1)
	imgs = glob.glob(os.path.join(folder,"*.jpg"))
	return imgs

def updateMatchesForNewKey(key_id):
	Key = key.query.filter_by(id=key_id).all()
	KeyImg = key_img.query.filter_by(key_id=key_id).all()
	for Doc in doc.query.all(): 	
		match = False
		for doc_image_location in get_doc_img_locations(Doc):
			for keyImg in KeyImg:
				if detectKeyInImage(keyImg.file_location, doc_image_location):
					Doc.keys = Key
					db.session.commit()
					match = True
				if match:
					break
			if match:
				break	

def updateMatchesForNewDoc():
	pass

def extractTextInImage(doc_location,doc_id):
	print doc_id
	folder, ending = doc_location.rsplit(".",1)
	imgs = glob.glob(os.path.join(folder,"*.jpg"))
	img_text = ""
	for img in imgs:
		command = ["tesseract",img,"stdout"]
		proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
		temp = proc.stdout.read()
		img_text = "{}\n{}".format(img_text,temp)
	Doc = doc.query.filter_by(id=doc_id).first()
	Doc.text = unicode(img_text, "utf-8")
	db.session.add(Doc)
	db.session.commit()


def convertPdfToImage(file_loc,doc_id):
	print doc_id
	new_dir, file_ending = file_loc.split(".")
	if file_ending == 'pdf':
		if not os.path.exists(new_dir):
			os.makedirs(new_dir)
		doc = Image(filename=file_loc,resolution=300)
		doc.compression_quality = 20
		for i, page in enumerate(doc.sequence):
			with Image(page) as page_image:
				page_image.alpha_channel = False
				page_image.background_color = Color('white')
				save_location =  new_dir+"/img-{}.jpg".format(str(i).zfill(4))
				page_image.save(filename=save_location)
		t1 = threading.Thread(target=extractTextInImage,args=(file_loc,doc_id))
		t1.start()

@app.route('/uploads/docs/<filename>')
def send_doc(filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER,"docs"), filename)

@app.route('/uploads/keys/<filename>')
def send_key(filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER,"keys"), filename)

@app.route('/doc/<doc_id>',methods = ['GET','POST'])
def delete_doc(doc_id):
	if request.method == 'POST':
		if not request.form['delete']:
			return redirect(url_for('show_all'))
		docToDelete = doc.query.filter_by(id=int(doc_id)).first()
		if os.path.exists(docToDelete.file_location):
			os.remove(docToDelete.file_location)
		directory = docToDelete.file_location.rsplit('.',1)[0]
		if os.path.isdir(directory):
			shutil.rmtree(directory)
		db.session.delete(docToDelete)
		db.session.commit()
	return redirect(url_for('show_all_docs'))

@app.route('/key/<key_id>',methods = ['GET','POST'])
def delete_key(key_id):
	if request.method == 'POST':
		if not request.form['delete']:
			return redirect(url_for('show_all'))
		keyToDelete = key.query.filter_by(id=int(key_id)).first()
		for keyImg in keyToDelete.imgs:
			os.remove(keyImg.file_location)
		db.session.delete(keyToDelete)
		db.session.commit()
	return redirect(url_for('show_all_keys'))

@app.route('/doc',methods = ['GET', 'POST'])
def show_all_docs():
	if request.method == 'POST':

		if not request.form['name'] or 'file' not in request.files or not request.files['file'].filename or not allowed_file(request.files['file'].filename):
			flash('Please enter all the fields', 'error')
		else:
			file = request.files['file']
		  	filename = secure_filename(file.filename)
		  	uid = uuid.uuid4()
		  	file_ending = filename.rsplit('.', 1)[1]
		  	new_filename = str(uid)+"."+file_ending
		  	location = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'],"docs"), new_filename)
			file.save(location)
			#convertPdfToImage(location)
			Doc = doc(name=request.form['name'],uuid=str(uid), file_location=location)
			db.session.add(Doc)
			db.session.commit()
			Doc = doc.query.filter_by(file_location=location).first()
			t = threading.Thread(target=convertPdfToImage,args=(location,Doc.id))
			t.start()
			flash('Record was successfully added')
			return redirect(url_for('show_all_docs'))

	return render_template('docs.html', docs = doc.query.all() )

@app.route('/key',methods = ['GET', 'POST'])
def show_all_keys():
	print request.url_root
	if request.method == 'POST':

		if not request.form['name'] or not request.form['text'] or 'file' not in request.files or not request.files['file'].filename or not allowed_file(request.files['file'].filename):
			flash('Please enter all the fields', 'error')
		else:
			file = request.files['file']
		  	filename = secure_filename(file.filename)
		  	uid = uuid.uuid4()
		  	new_filename = str(uid)+"."+filename.rsplit('.', 1)[1]
		  	location = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'],"keys"), new_filename)
			file.save(location)
			imgs = [key_img(file_location=location,uuid=str(uid))]
			terms = [key_term(term=text) for text in request.form['text'].split(",")]
			Key = key(name=request.form['name'])
			Key.terms = terms
			Key.imgs = imgs
			db.session.add(Key)
			db.session.commit()
			t = threading.Thread(target=updateMatchesForNewKey,args=(Key.id,))
			t.start()
			flash('Record was successfully added')
			return redirect(url_for('show_all_keys'))
	return render_template('keys.html', keys = key.query.all() )



if __name__ == '__main__':
	db.create_all()
	app.run(host='0.0.0.0', port=8888,debug = True, threaded=True)

# Flask App - Document Tagger Project

This is a toy web app to prototype the use of 'keys' to auto tag documents as they are uploaded to a website.   A key a combination of branded images and keywords to search for in a document.  If the branding image or key words is found, the document is tagged with the key.   When a new key is uploaded, all documents are scanned for the new branding image and keywords.  

## Dependencies

This program runs successfully on Ubuntu 14.04 with

- Python 2.7
- OpenCV (built from source)
- Wand (pip)
- Tesseract (apt-get)
- ImageMagik (apt-get)
- flask (pip)
- flask_sqlalchemy (pip)
- werkzeug (pip)
- numpy (apt-get)

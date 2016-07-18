# Document Sorter

This is a toy project that attempts to match Key Images in documents to identify and sort the source of the document.   The use case is to auto-sort financial documents by institution using branded images.

Based on feedback I have recieved, I have slightly expanded the project from a command-line based tool to a toy webapp and have a webapp for creating keys and uploading documents, with matching processes spawned into separate threads, as well as extracting text from documents using OCR methods. This extension is in the flask-app folder.

## Dependencies

This program runs successfully on Ubuntu 14.04 with 

- Python 2.7
- OpenCV (built from source)
- Wand (pip) 
- Tesseract (apt-get)
- ImageMagik (apt-get)


## Command Line Use

```bash
python documentsort.py \
	--key_dir="<key-direct>" \
	--doc_dir="<document-directory>"
	--sort_dir="<sorted-document-directory>"
```

## Directory Structure:

The script will convert each page in the PDF in the doc_dir to images, and attempt to feature match the images from the key directory.  If there is a successful match, the script will copy the file to the appropriate directory in the sort_dir.   If there is not a match, it will be copied to the unsorted directory.   

```bash
|-- documents
|   '-- tiaa.pdf
|   |-- tiaa
|   |   |-- img-0000.jpg
|   |   |-- img-0001.jpg
|   |   |-- img-0002.jpg
|   |   `-- img-0003.jpg
|   `-- wf01.pdf  
|   |-- wf01
|   |   |-- img-0000.jpg
|   |   |-- img-0001.jpg
|   |   |-- img-0002.jpg
|   |   |-- img-0003.jpg
|   |   |-- img-0004.jpg
|   |   `-- img-0005.jpg
|-- keys
|   |-- tiaa
|   |   `-- tiaa.png
|   `-- wellsfargo
|       `-- wellsfargo.png
`-- sorted
    |-- tiaa
    |   `-- tiaa.pdf
    |-- unsorted
    `-- wellsfargo
        `-- wf01.pdf
```
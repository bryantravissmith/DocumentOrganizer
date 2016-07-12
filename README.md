# Document Sorter

This is a toy project that tempts to match Key Images in documents to identify and sort the source of the document.   The use case is to auto-sort financial documents by institution using branded images

## Dependencies

This program runs successfully on Ubuntu 14.04 with 

- OpenCV
- Wand
- Tesseract
- ImageMagik


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
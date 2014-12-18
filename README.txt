Welcome! Perfect Produce Picker is a program that allows users to easily identify items from a database (that can be expanded) using a combination of handwritten input (using the Leap Motion to write with index finger in the air and Tesseract OCR) and webcam RGB information using OpenCV.
Users also get around the program by using the Leap Motion controller, and can add custom items to the database with pictures either uploaded
from the computer or taken from the webcam.  Finally, users can browse their current database and narrow the search parameters to find specific items.

PLEASE DO THE FOLLOWING BEFORE ATTEMPTING TO LAUNCH THE PROGRAM:

1. Extract this folder if you haven't already.
2. Install PIL 1.1.7 if you havne't already. Download can be found here: http://www.pythonware.com/products/pil/
3. Install Tesseract 3.02 to the "pytesser" folder located in this download. Download can be found here: https://code.google.com/p/tesseract-ocr/downloads/detail?name=tesseract-ocr-setup-3.02.02.exe&can=2&q=
4. Download the LeapMotion SDK, v2.1.x.xxxxx (for Python), directly to the LeapProject folder from this download. Download can be found here: https://developer.leapmotion.com/
5. In the "project.py" file, near the top, rename the variable "sdkFolder" to the name of the folder you just downloaded.
6. Also included in this download is the file "Leap.py" and the folder "tessdata". Go into your LeapDeveloperKit folder, then into the folder "LeapSDK", then into the "lib" folder, and replace the "Leap.py" file there with the one provided.
7. Go into the "pytesser" folder, into "Tesseract-OCR", and merge the "tessdata" folder there with the one provided.
8. Download OpenCV, following the instructions found here: http://docs.opencv.org/trunk/doc/py_tutorials/py_setup/py_setup_in_windows/py_setup_in_windows.html#install-opencv-python-in-windows
9. However, make sure to download this version of Numpy instead of the one provided in the OpenCV documentation: http://sourceforge.net/projects/numpy/files/NumPy/1.9.1/numpy-1.9.1-win32-superpack-python2.7.exe/download

You are good to go!

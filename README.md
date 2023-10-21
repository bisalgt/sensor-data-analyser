# sensor-data-analyser


## The main goal of this project is to create datasets used for training a ML model. The dataset will be labelled as `empty` or `return`. A data will be labelled as empty if it is not a part of the `first return signal from ultrasonic sensor` and a data will be labelled as return if it is a part of the `first return signal from ultrasonic sensor`. 

### The end result of this project is to create dataset which can be used for ML models to extract the first return signal from the raw adc data from ultrasonic sensor.


### Using the GUI with PyQt6, the first return signal is manually selected. The signal is then segmented into smaller segments of predefined length. The segmented signal undergoes through Hamming window. Each segmented signal is then passed to a STFT (Short Time Fourier Transform) function which will result in spectrogram of the segmented signal. Based on the selected region using the python gui, we label the output data from STFT as `empty` or `return`. All the segmented signal which falls under the selected region in GUI is labelled as `return` and the rests are labelled as `empty`.


To run the project : `python project/app.py` from the root folder.
The program will wait for connection with the redpitaya sensor udp server in a specific socket.

Tools Used :
pyqt6, pyqtgraph, sockets
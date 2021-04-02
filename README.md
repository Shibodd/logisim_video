# logisim_video

The python script can be used to export a video to logisim's native library ROMs, in black-white row bitarray format, to be displayed in the native LED matrix.

Python module requirements (available from pip): av, numpy, pillow

# Script arguments: 

python video_to_logisim_rom.py video_path width height

# Usage:

screen.circ is an example logisim 64x64 video player using this format. First export the video using python video_to_logisim_rom.py video_path 64 64.
Then, if the ROMs address width is too low compared to the "Minimum address width" in the script output, increase it on each ROM.
For each ROM you can right click on it and click on "Load Image" - then load the corresponding outx (out0, out1, ...) file as per output instructions 
(it outputs each screen's filename and position). After that, you can play the video using logisim's Simulate menu.

Be aware that screen.circ doesn't know the framerate of your video nor can sync with time (syncing with music is a PITA for this reason) - you can benchmark at what FPS your PC is playing the video using the bottom-right button and a stopwatch of your choice, then convert your video to that framerate and load it into Logisim.

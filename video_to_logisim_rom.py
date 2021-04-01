import av
from PIL import Image, ImageOps
import numpy as np
import math
import argparse
import pathlib
import traceback



def calculate_32x32_areas(size):
    """ Returns a list of areas dividing a rectangle sized size, and the count for each axis. """
    w_parts = math.ceil(resolution[0] / 32)
    h_parts = math.ceil(resolution[1] / 32)

    areas = []

    for x_t in range(w_parts):
        for y_t in range(h_parts):
            x = x_t * 32
            y = y_t * 32

            areas.append((x, y, min(x + 32, size[0]), min(y + 32, size[1])))

    return (areas, w_parts, h_parts)


def image_to_bitarray(frame, threshold):
    """ Converts an image to a bitarray """

    frame = ImageOps.mirror(frame)
    frame = ImageOps.grayscale(frame)
    
    grayscale_array = np.array(frame)

    # Transform the grayscale array to a bitarray
    grayscale_array[grayscale_array < threshold] = 0
    grayscale_array[grayscale_array >= threshold] = 1

    return grayscale_array



POWERS_OF_TWO = 2 ** np.arange(32)
def bitarray_to_number(bitarr):
    """ Converts a bitarray of maximum 32 bits to an integer """

    # The conversion can be thought as a dot product 
    # between the bitarray and the corresponding powers of two.
    # e.g.  [1 0 1] * [4, 2, 1] = 1 * 4 + 0 * 2 + 1 * 1
    return bitarr.dot(POWERS_OF_TWO[:len(bitarr)])


def num_to_logisim_text(num, width):
    """ Converts a width-bit number to a HEX string used by logisim """

    numlen = math.ceil(width / 4)
    numstr = ('{:0' + str(numlen) + 'X}')

    return numstr.format(num & 0xffffffff)


class OutputFilesManager:
    def __init__(self, filename_fmt, file_count):
        self.opened_files = []
        for i in range(file_count):
            self.opened_files.append(open(filename_fmt.format(i), "w"))

    def __enter__(self):
        return self.opened_files

    def __exit__(self, type, value, traceback):
        for file in self.opened_files:
            file.close()
        


OUTFILE_FMT = "out{}"


# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument('video_path', type=pathlib.Path)
parser.add_argument('w', type=int)
parser.add_argument('h', type=int)
args = parser.parse_args()





resolution = (args.w, args.h)
areas, w_parts, y_parts = calculate_32x32_areas(resolution)



# Work
print("Working...")

frame_count = 0
with OutputFilesManager(OUTFILE_FMT, w_parts * y_parts) as files:
    for file in files:
        file.write("v2.0 raw\n")

    with av.open("video.mkv") as container:
        for frame in container.decode(video=0):
            img = frame.to_image().resize(resolution)

            for i, area in enumerate(areas):
                part = img.crop(area)

                nums = map(bitarray_to_number, image_to_bitarray(part, 127))
                files[i].write(" ".join(map(lambda x: num_to_logisim_text(x, part.width), nums)) + " ")

            frame_count = frame_count + 1



# Info
print("Done! Configuration:")
print("Minimum address width:", math.ceil(math.log2(max(32, resolution[0]) * frame_count)), "\n")
for i, area in enumerate(areas):
    x = int(i / y_parts)
    y = i % y_parts

    print("Screen ({}, {}):".format(x, y))
    print("Filename:", OUTFILE_FMT.format(i))
    # (min_x, min_y, max_x, max_y)
    print("Data and screen width:", area[2] - area[0]) 
    print("Screen height:", area[3] - area[1], "\n")
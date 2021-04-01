# ffmpeg -i .\video.mkv -vf fps=1/1 $filename%03d.bmp

import pathlib
import argparse
import subprocess
from PIL import Image, ImageOps
import numpy as np
import math
import itertools
import traceback

FRAME_EXT = "png"

def extract(out_folder, video_path, fps):
    if out_folder.is_dir():
        return False
    
    out_folder.mkdir()

    out_file_path = out_folder / ('%03d.' + FRAME_EXT)
    fps_str = str(fps) + "/1"

    subprocess.run(["ffmpeg", "-i", str(video_path), "-vf", "fps=" + fps_str, "-y", str(out_file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def load_resize_divide_image(image_path, resolution):
    image = Image.open(image_path)
    resized = image.resize(resolution)

    w_parts = math.ceil(resolution[0] / 32)
    h_parts = math.ceil(resolution[1] / 32)

    parts = []
    for x_t in range(w_parts):
        for y_t in range(h_parts):
            x = x_t * 32
            y = y_t * 32

            area = (x, y, min(x * 32 + 32, resolution[0]), min(y + 32, resolution[1]))
            parts.append(resized.crop(area))


    return parts



def image_to_bitarray(frame, threshold):
    frame = ImageOps.mirror(frame)
    frame = ImageOps.grayscale(frame)
    
    grayscale_array = np.array(frame)

    # Transform the grayscale array to a bitarray
    grayscale_array[grayscale_array < threshold] = 0
    grayscale_array[grayscale_array >= threshold] = 1

    return grayscale_array



POWERS_OF_TWO = 2 ** np.arange(32)
def bitarray_to_number(bitarr):
    return bitarr.dot(POWERS_OF_TWO[:len(bitarr)])


def grouper(iterable, n, fillvalue=None):
    " Groups iterable in n-sized chunks "

    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)



def work(frame_folder, resolution):
    w_parts = math.ceil(resolution[0] / 32)
    y_parts = math.ceil(resolution[1] / 32)

    frame_count = len(list(frame_folder.glob("*." + FRAME_EXT)))

    files = [open("out" + str(i), "w") for i in range(w_parts * y_parts)]
    for file in files:
        file.write("v2.0 raw\n")

    err = False
    try:
        for i in range(frame_count):
            frame_path = frame_folder / (str(i + 1).rjust(3, '0') + '.' + FRAME_EXT)
 
            parts = load_resize_divide_image(frame_path, resolution)

            for i, part in enumerate(parts):
                data_width = part.width
                
                data = list(map(bitarray_to_number, image_to_bitarray(part, 127)))
                
                numlen = math.ceil(data_width / 4)
                numstr = ('{:0' + str(numlen) + 'X}')

                # Write everything
                files[i].write(" ".join(map(  lambda x: numstr.format(x & 0xffffffff),  data)) + " ")
            frame_count = frame_count + 1
    except Exception as e:
        traceback.print_exc()
        err = True
    
    for file in files:
        file.close()

    if err:
        exit(1)

    return (w_parts * y_parts, data_width, frame_count)



parser = argparse.ArgumentParser()
parser.add_argument('video_path', type=pathlib.Path)
parser.add_argument('w', type=int)
parser.add_argument('h', type=int)
parser.add_argument('fps', type=float)
args = parser.parse_args()



resolution = (args.w, args.h)

frame_folder = pathlib.Path(args.video_path.name + "_" + str(args.fps))


print('Extracting the video frames...')
if not extract(frame_folder, args.video_path, args.fps):
    print("Skipping the extraction (delete the", frame_folder, "directory to re-extract).")
else:
    print("Extracted the video frames.")



part_count, data_width, frame_count = work(frame_folder, resolution)


address_width = math.ceil(math.log2(resolution[1] * frame_count))


print("\nDone! The required configuration is as follows:")
print("Screens and ROMs required:", part_count)
print("Data width:", data_width)
print("Address width:", address_width)
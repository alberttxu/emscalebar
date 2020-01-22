#!/usr/bin/env python3
import argparse
import logging
from multiprocessing import Pool
import os
import tempfile
import traceback

from PIL import Image
from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
from skimage import exposure
from skimage.util import img_as_ubyte
import mrcfile
import numpy as np

parser = argparse.ArgumentParser(
    description="add scale bar to electron microscopy images"
)
parser.add_argument("mrcfiles", help="input mrc files", nargs="+")
parser.add_argument(
    "--outputdir", help="output directory for created jpg images", default=os.getcwd(),
)
parser.add_argument(
    "--maxsize", help="maximum image dimension for jpg images", default=1250, type=int,
)
parser.add_argument("--numprocs", help="number of parallel processes to run", type=int)
args = parser.parse_args()
if not os.path.exists(args.outputdir):
    print(f"{args.outputdir} was not found. Exiting.")
    exit()
if not os.path.isdir(args.outputdir):
    print(f"{args.outputdir} is not a directory. Exiting.")
    exit()


def read_mrc(path_to_mrc):
    if not os.path.exists(path_to_mrc):
        print(f"{path_to_mrc} was not found. Skipping.")
        return None
    if not os.path.isfile(path_to_mrc):
        print(f"{path_to_mrc} is not a regular file. Skipping.")
        return None
    try:
        with mrcfile.open(path_to_mrc) as mrc:
            img = mrc.data
            # get pixel sizes and convert to meters
            pixel_size_x = mrc.header["cella"]["x"] / mrc.header["mx"] * 10 ** -10
            pixel_size_y = mrc.header["cella"]["y"] / mrc.header["my"] * 10 ** -10
        if not np.isclose(pixel_size_x, pixel_size_y):
            print("Pixel sizes in x and y are not equal. Using pixel size in x.")
        return img, pixel_size_x
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Error occured in reading {path_to_mrc}. Skipping.")
        return None


def reduce_img(img: "ndarray", shrink_factor) -> "ndarray":
    if shrink_factor == 1:
        return img
    new_shape = (int(img.shape[1] / shrink_factor), int(img.shape[0] / shrink_factor))
    return np.array(Image.fromarray(img).resize(new_shape, Image.LANCZOS))


def make_jpg_with_scalebar(img, pixel_size, outputdir, outputname):
    img = img[::-1]  # follows imod orientation
    img = exposure.equalize_adapthist(img)
    img = img_as_ubyte(img)

    plt.figure()
    scalebar = ScaleBar(
        pixel_size,
        location="lower right",
        frameon=True,
        color="black",
        pad=0.3,
        box_alpha=0,
        border_pad=0.3,
        height_fraction=0.009,
    )
    scalebar2 = ScaleBar(
        pixel_size,
        location="lower right",
        frameon=True,
        color="white",
        box_alpha=0,
        border_pad=0.3,
        height_fraction=0.005,
    )
    plt.gca().add_artist(scalebar)
    plt.gca().add_artist(scalebar2)
    plt.imshow(img, cmap="gray")
    plt.axis("off")
    temp_img = tempfile.TemporaryFile()
    plt.savefig(temp_img, bbox_inches="tight", pad_inches=0, dpi=300)
    print(f"creating jpg image {os.path.join(outputdir, outputname)}")
    Image.open(temp_img).convert("RGB").save(
        os.path.join(outputdir, outputname), "JPEG"
    )


def process_mrc(path_to_mrc):
    mrc_data = read_mrc(path_to_mrc)
    if mrc_data is None:
        return
    img = mrc_data[0]
    pixel_size = mrc_data[1]
    if max(*img.shape[-2:]) > args.maxsize:
        shrink_factor = max(*img.shape[-2:]) / args.maxsize
        pixel_size *= shrink_factor
    else:
        shrink_factor = 1

    filename = os.path.split(path_to_mrc)[-1]
    if len(img.shape) == 2:
        img = reduce_img(img, shrink_factor)
        outputname = f"{filename}.jpg"
        make_jpg_with_scalebar(img, pixel_size, args.outputdir, outputname)
    elif len(img.shape) == 3:
        for i in range(img.shape[0]):
            outputname = f"{filename}_section{i}.jpg"
            section = img[i]
            section = reduce_img(section, shrink_factor)
            make_jpg_with_scalebar(section, pixel_size, args.outputdir, outputname)


if __name__ == "__main__":
    with Pool(processes=args.numprocs) as pool:
        pool.map(process_mrc, args.mrcfiles)

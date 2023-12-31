import os
import numpy as np
import cv2
import argparse
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.widgets import PolygonSelector
from matplotlib.collections import PatchCollection
from shapely.geometry import box
from shapely.geometry import Polygon as shapely_poly

points = []
prev_points = []
patches = []
total_points = []
breaker = False

class SelectFromCollection(object):
    def __init__(self, ax):
        self.canvas = ax.figure.canvas
        self.poly = PolygonSelector(ax, self.onselect)
        self.ind = []

    def onselect(self, verts):
        global points
        points = verts
        self.canvas.draw_idle()

    def disconnect(self):
        self.poly.disconnect_events()
        self.canvas.draw_idle()

def break_loop(event):
    global breaker
    global globSelect
    global savePath
    if event.key == 'b':
        globSelect.disconnect()
        if os.path.exists(savePath):
            os.remove(savePath)

        with open(savePath, 'w') as f:
            for i, pts in enumerate(total_points, start=1):
                data = str(i) + "," + str(pts[0][0]) + "," + str(pts[0][1]) + "," + str(pts[1][0]) + "," + str(pts[1][1]) + "," + str(pts[2][0]) + "," + str(pts[2][1]) + "," + str(pts[3][0]) + "," + str(pts[3][1]) + "\n"
                f.write(data)

        print("Data saved in " + savePath + " files")
        exit()

def onkeypress(event):
    global points, prev_points, total_points, patches
    if event.key == 'n':
        pts = np.array(points, dtype=np.int32)
        if points != prev_points and len(set(points)) == 4:
            print("Points : " + str(pts))
            patches.append(Polygon(pts))
            total_points.append(pts)
            prev_points = points
            # Clear the patches list to remove previous quadrilaterals
            patches = []

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image_path', help="Path of image file")
    parser.add_argument('--out_file', help="Name of the output file", default="regions.txt")
    args = parser.parse_args()

    global globSelect
    global savePath
    savePath = args.out_file if args.out_file.endswith(".txt") else args.out_file + ".txt"

    print("\n> Select a region in the figure by enclosing them within a quadrilateral.")
    print("> Press the 'f' key to go full screen.")
    print("> Press the 'esc' key to discard the current quadrilateral.")
    print("> Try holding the 'shift' key to move all of the vertices.")
    print("> Try holding the 'ctrl' key to move a single vertex.")
    print("> After marking a quadrilateral, press 'n' to save the current quadrilateral, and then press 'q' to start marking a new quadrilateral")
    print("> When you are done, press 'b' to exit the program\n")

    while True:
        image = cv2.imread(args.image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        fig, ax = plt.subplots()
        ax.imshow(rgb_image)
        p = PatchCollection(patches, alpha=0.7)
        p.set_array(10 * np.ones(len(patches)))
        ax.add_collection(p)

        globSelect = SelectFromCollection(ax)
        bbox = plt.connect('key_press_event', onkeypress)
        break_event = plt.connect('key_press_event', break_loop)
        plt.show()
        globSelect.disconnect()
        # Clear the patches list after each quadrilateral is marked
        patches = []

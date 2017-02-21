#!/usr/bin/env python3

import cv2
import sys
import copy
import random
import numpy


import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit('install Pillow to run this code')

def find_ball(opencv_image, debug=False):
    """Find the ball in an image.
        
        Arguments:
        opencv_image -- the image
        debug -- an optional argument which can be used to control whether
                debugging information is displayed.
        
        Returns [x, y, radius] of the ball, and [0,0,0] or None if no ball is found.
    """

    ball = None
    
    ## INSERT SOLUTION
    one = 134
    two = 28

    # pil_image = Image.fromarray(cv2.Canny(opencv_image, one, two))
    # pil_image.show()
    image = cv2.GaussianBlur(opencv_image, (7, 7), 2)

    circles = cv2.HoughCircles(image,cv2.HOUGH_GRADIENT,0.75, 25,
                            param1=one,param2=two,minRadius=5,maxRadius=200)

    # if circles is not None:
    #     display_circles(opencv_image, circles[0])
    # else:
    #     pil_image = Image.fromarray(opencv_image)
    #     pil_image.show()

    if circles is not None and opencv_image[circles[0][0][1]][circles[0][0][0]] < 30: # CHANGE VALUE BASED ON LIGHT
    #display_circles(opencv_image, [circles[0][0]])
    #if circles is not None:
        #display_circles(opencv_image, circles[0])
        # print(len(circles[0]))
        return circles[0][0]



        # sample = []
        # for x in range(10):
        #     i = random.random() * circles[0][0][2] - circles[0][0][2] / 2
        #     j = random.random() * circles[0][0][2] - circles[0][0][2] / 2
        #     print("I", i)
        #     print("J", j)
        #     if circles[0][0][1] + i < len(opencv_image) and circles[0][0][1] + i >= 0 and \
        #                             circles[0][0][0] + j < len(opencv_image) and circles[0][0][0] + j >= 0:
        #         sample.append(opencv_image[circles[0][0][1] + i][circles[0][0][0] + j])
        # avg = sum(sample) / len(sample)
        # dev = 0
        # for x in sample:
        #     dev += abs(x - avg) ** 2
        # dev = dev ** (1/2)
        #
        # print("Average", avg)
        # print("DEV", dev)
        # if dev < 25 :
        #     return circles[0][0]




def display_circles(opencv_image, circles, best=None):
    """Display a copy of the image with superimposed circles.
        
       Provided for debugging purposes, feel free to edit as needed.
       
       Arguments:
        opencv_image -- the image
        circles -- list of circles, each specified as [x,y,radius]
        best -- an optional argument which may specify a single circle that will
                be drawn in a different color.  Meant to be used to help show which
                circle is ranked as best if there are multiple candidates.
        
    """
    #make a copy of the image to draw on
    circle_image = copy.deepcopy(opencv_image)
    circle_image = cv2.cvtColor(circle_image, cv2.COLOR_GRAY2RGB, circle_image)
    
    for c in circles:
        # draw the outer circle
        cv2.circle(circle_image,(c[0],c[1]),c[2],(255,255,0),2)
        # draw the center of the circle
        cv2.circle(circle_image,(c[0],c[1]),2,(0,255,255),3) 
        # write coords
        cv2.putText(circle_image,str(c),(c[0],c[1]),cv2.FONT_HERSHEY_SIMPLEX,
                    .5,(255,255,255),2,cv2.LINE_AA)            
    
    #highlight the best circle in a different color
    if best is not None:
        # draw the outer circle
        cv2.circle(circle_image,(best[0],best[1]),best[2],(0,0,255),2)
        # draw the center of the circle
        cv2.circle(circle_image,(best[0],best[1]),2,(0,0,255),3) 
        # write coords
        cv2.putText(circle_image,str(best),(best[0],best[1]),cv2.FONT_HERSHEY_SIMPLEX,
                    .5,(255,255,255),2,cv2.LINE_AA)            
        
    
    #display the image
    pil_image = Image.fromarray(circle_image)
    pil_image.show()             
      
if __name__ == "__main__":
    pass
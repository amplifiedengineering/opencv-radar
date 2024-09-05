import numpy as np
import cv2
import imutils
import os
import progressbar
import torch
from collections import defaultdict

from ultralytics import YOLO

from ultralytics import settings
import time 


class TrafficCounter(object):
    def __init__(self,video_source=0,
                 line_direction='H',
                 line_position_start=900,
                 line_position_end=1300,
                 distance=320,
                 threshold_speed=100,
                 min_area = 200,
                 video_out='',
                 out_video_params={},
                 starting_frame=10,
                 headless=False,):
        self.font              = cv2.FONT_HERSHEY_SIMPLEX

        self.counter           = 0
        self.line_direction    = line_direction       
        self.line_position_start = min(line_position_start, line_position_end)
        self.line_position_end = max(line_position_end, line_position_start)
        self.distance          = distance
        self.starting_frame    = starting_frame
        self.video_source      = cv2.VideoCapture(video_source)    
        self.headless = headless

        self.threshold_speed = threshold_speed
        self.frame_count = 0
        self.frame_count_total = 0
        self.any_object_detected_total = 0
        self.track_history = defaultdict(lambda: [])
        self.frame_history = defaultdict(int)
        self.frame_history_start = defaultdict(int)
        self.frame_history_total = defaultdict(int)

        if torch.cuda.is_available():
            torch.cuda.set_device(0)

        self.model = YOLO("yolov8n.pt")

    def draw_text(self, img, text,
                  font=cv2.FONT_HERSHEY_PLAIN,
                  pos=(0, 0),
                  font_scale=3,
                  font_thickness=2,
                  text_color=(255, 255, 0),
                  text_color_bg=(0, 0, 0)
                  ):

        x, y = pos
        text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
        text_w, text_h = text_size
        cv2.rectangle(img, pos, (x + text_w, y + text_h), text_color_bg, -1)
        cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)

        return img

    def _draw_line(self, img, direction, position):
        if direction == "H":
            #print(F"H {(position, 0), (position, img.shape[1])}")
            img = cv2.line(img, (0, position), (img.shape[1], position), (0, 255, 0),
                           thickness=3)
        else:

            img = cv2.line(img, (position, 0), (position, img.shape[0]), (0, 255, 0),
                           thickness=3)
        return img

    def _set_up_lines(self):

        grabbed,img = self.video_source.read()
        while not grabbed:
            grabbed,img = self.video_source.read()
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        self._vid_height = img.shape[0]

        ##-------Show setup window
        k = None
        cv2.namedWindow('setup2',1)

        # Using cv2.putText() method
        img = self.draw_text(img,text="ensure lines are correct, q to finish")
        img = self._draw_line(img, self.line_direction, self.line_position_start)
        img = self._draw_line(img, self.line_direction, self.line_position_end)

        cv2.imshow('setup2',img)

        orImg= img
        # during setup, just verify that you have correctly positioned start / end lines
        while k != ord('q') and k != ord('Q') and k != 27 and k != ('\n'):
            k = cv2.waitKey(0) & 0xFF

        cv2.destroyWindow('setup2')


    def main_loop(self):
        print(self.headless)
        self._set_up_lines()
        rate_of_influence = 0.01
        FRAME_CROPPED = False
        totalFrames = int(self.video_source.get(cv2.CAP_PROP_FRAME_COUNT))
        with progressbar.ProgressBar(max_value=totalFrames) as bar:
            while True:
                #print("in main loop")
                grabbed,img = self.video_source.read()
                if not grabbed:
                    break
                #--------------


                frame_id = int(self.video_source.get(1))        #get current frame index
                self.frame_count_total += 1
                bar.update(self.frame_count_total)

                results = self.model.track(img, persist=True, verbose=False, classes=[2, 3, 7])

                boxes = results[0].boxes.xywh.cpu()
                # Visualize the results on the frame
                annotated_frame = results[0].plot()
                annotated_frame = self._draw_line(annotated_frame, self.line_direction, self.line_position_start)
                annotated_frame = self._draw_line(annotated_frame, self.line_direction, self.line_position_end)

                if results[0].boxes.id != None:
                    self.any_object_detected_total += 1
                    track_ids = results[0].boxes.id.tolist()

                    # Plot the tracks
                    for box, track_id in zip(boxes, track_ids):
                        x, y, w, h = box
                        track = self.track_history[track_id]
                        if self.frame_history_start[track_id] == 0:
                            self.frame_history_start[track_id] = frame_id
                        self.frame_history_total[track_id] += 1
                        if self.line_direction.upper() == "H":
                            if y > self.line_position_start and y < self.line_position_end:
                                self.frame_history[track_id] += 1
                        else:
                            if x > self.line_position_start and x < self.line_position_end:
                                self.frame_history[track_id] += 1
                        track.append((float(x), float(y)))  # x, y center point
                        if len(track) > 30:  # retain 90 tracks for 90 frames
                            track.pop(0)

                        # Draw the tracking lines
                        points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                        cv2.polylines(annotated_frame, [points], isClosed=False, color=(230, 230, 230), thickness=10)

                # Display the annotated frame
                if not self.headless:
                    cv2.imshow("YOLOv8 Tracking", annotated_frame)

                ##-------Termination Conditions
                k = cv2.waitKey(25) & 0xFF
                if k == 27 or k == ord('q') or k == ord('Q'):
                    break
                if k == ord(' '):   #if spacebar is pressed
                    paused_key = cv2.waitKey(0) & 0xFF       #program is paused for a while
                    if paused_key == ord(' '):    #pressing space again unpauses the program
                        pass

            for k, v in self.frame_history.items():
                if v > 0:
                    mphCalc = self.distance / 5280 / (v * 1 / 30 * 1 / 3600) #distance in feet divided by feet per miles, divided by frames counted, divided by FPS (30), divided by 1 / seconds per hour
                    # may need a different FPS calc based upon the video
                    if mphCalc < self.threshold_speed:
                        print (f"{self.distance} {v}")
                        print(f"id: {k} speed (mph): {self.distance / 5280 / (v * 1 / 30 * 1 / 3600)} total frames tracked: {self.frame_history_total[k]}")
                        print(
                            f"frame start id: {self.frame_history_start[k]}")

        print( f"Total detections: {self.any_object_detected_total} Total frame count: {self.frame_count_total} % of time detected: {self.any_object_detected_total / self.frame_count_total}")

        self.video_source.release()

        cv2.destroyAllWindows()
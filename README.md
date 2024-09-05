# opencv-radar
This project draws heavily upon the project https://github.com/andresberejnoi/OpenCV_Traffic_Counter by https://github.com/andresberejnoi. Thanks for the inspiration!

Using opencv and yolo to create a speed check on videos tracking cars, trucks, etc.

Workflow should be similar to this:

1) Grab a video which allows you to see a street where you know the distance between two points on the street
2) Execute the Python script with 
   a) d(irection) of measurement either H (horizontal) (start, end) or V (vertical (start, end))
      - start and end should be the pixel where the measurement of the distance begins / ends
   b) l(ength) (in feet) between the two points
      - I used Google maps to calculate this distance in my videos
   c) p(ath) <path to video>
   d) e.g. python3 main.py -d H 924 1400 -l 320 -p ~/Documents/calibrated-33-30-rotator.mov --headless
3) Once executed, the first screen will show the two lines you have chosen, if these are incorrectly placed the measurements
   WILL be inaccurate. I calibrated the start / stop by using my cruise control on my car to be set to 33/30 MPH, and then recorded
   my car between those two points, and fiddled with the start / end points until it was calibrated correctly (33/30 mph). 
   I have included the video of that calibrated run for completion purposes (tracked car 2 and 4)
4) The output of running a video through the system will be which objects were tracked, how fast they are going (according to the
    to the calculated distance between the points), and the starting frame for longer videos to help you pinpoint where
    the vehicle was found. I set an arbitrary limit of 100 mph, as in some of my initial videos the vehicles are only present for
    part of the transit between the two points which results in garbage measurements.


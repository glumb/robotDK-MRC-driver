# RobotDK MRC-driver and Post Processor

The [MRIL](https://github.com/glumb/mrcp) post processor (`MRCL.py`) is used to export a program to static machine code.
The driver (`driver.py`) is used to dynamically/online control a connected robot by sending the MRIL instructions via serial to the [MRC](https://github.com/glumb/mrc) controller.

# Post Processor
Place the post processor (`MRCL.py`) in the post directory of RobotDK. On MacOS it is:
<img width="576" alt="pastedgraphic-3" src="https://user-images.githubusercontent.com/3062564/38248067-7fdc6ae4-3747-11e8-9913-4202f4472a0a.png">
To invoke the post `right click` on the program in RoboDK and select `CreateProgram` then chose the MRCL post.

# Online Driver
Place the driver in a directory of your choice. E.g. :
<img width="565" alt="pastedgraphic-4" src="https://user-images.githubusercontent.com/3062564/38248069-815bfb6e-3747-11e8-9d15-bbbeb4126114.png">

`Right click/connect` to start a connection. On the left a panel with connection information should open.

<img width="565" alt="pastedgraphic-4" src="https://user-images.githubusercontent.com/3062564/38248122-a98d4610-3747-11e8-9c00-bfa629cea10b.png">

Enter the path to the driver at `API path`.  
Enter the COM port of your Teensy under `Robot IP/COM`  
Click `Connect`.  
Click `Move Joints (P2P)` or `Move Linear (LINEAR)` to send the movement commands to the robot.  

![pastedgraphic-2](https://user-images.githubusercontent.com/3062564/38248132-ae7c6d7c-3747-11e8-8923-f73c7af6d100.png)

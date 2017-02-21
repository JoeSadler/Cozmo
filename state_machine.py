import asyncio
import sys
import time
import cv2
import numpy as np
import find_ball
import cozmo
try:
    from PIL import ImageDraw, ImageFont, Image
except ImportError:
    sys.exit('run `pip3 install --user Pillow numpy` to run this example')


def make_text_image(text_to_draw, x, y, font=None):

    text_image = Image.new('RGBA', cozmo.oled_face.dimensions(), (0, 0, 0, 255))
    dc = ImageDraw.Draw(text_image)
    if x == 0 and y == 0:
        text_size = dc.textsize(text_to_draw) 
        screen_size = cozmo.oled_face.dimensions()
        x = int(screen_size[0] / 2 - text_size[0] / 2)
        y = int(screen_size[1] / 2 - text_size[1] / 2)

    dc.text((x, y), text_to_draw, fill=(255, 255, 255, 255), font=font)

    return text_image


class BatteryAnnotator(cozmo.annotate.Annotator):
    def apply(self, image, scale):
        d = ImageDraw.Draw(image)
        bounds = (0, 0, image.width, image.height)
        batt = self.world.robot.battery_voltage
        text = cozmo.annotate.ImageText('BATT %.1fv' % batt, color='green')
        text.render(d, bounds)

# Define a decorator as a subclass of Annotator; displays the ball
class BallAnnotator(cozmo.annotate.Annotator):

    ball = None

    def apply(self, image, scale):
        d = ImageDraw.Draw(image)
        bounds = (0, 0, image.width, image.height)

        if BallAnnotator.ball is not None:

            #double size of bounding box to match size of rendered image
            BallAnnotator.ball = np.multiply(BallAnnotator.ball,2)

            #define and display bounding box with params:
            #msg.img_topLeft_x, msg.img_topLeft_y, msg.img_width, msg.img_height
            box = cozmo.util.ImageBox(BallAnnotator.ball[0]-BallAnnotator.ball[2],
                                      BallAnnotator.ball[1]-BallAnnotator.ball[2],
                                      BallAnnotator.ball[2]*2, BallAnnotator.ball[2]*2)
            cozmo.annotate.add_img_box_to_image(image, box, "green", text=None)

            BallAnnotator.ball = None




class State:

    def run(self, params, robot):
        print(self.name)

    async def set_face_image(self, robot):
        state_name_image = make_text_image(self.name, 0, 0)
        oled_face_data = cozmo.oled_face.convert_image_to_screen_data(state_name_image)
        robot.display_oled_face_image(oled_face_data, 1000.0, in_parallel = True)


    def getName(self):
        return self.name


class Search(State):

    def __init__(self):
        self.name = "Search"
        self.found = False
        self.direction = 1


    async def run(self, next_param, robot):
        vel = 50
        acc = 100

        if len(next_param) is not 0:
            self.direction = next_param[0]

        robot.set_head_angle(cozmo.util.degrees(0), in_parallel = True)
        robot.set_lift_height(0, in_parallel = True)

        event = await robot.world.wait_for(cozmo.camera.EvtNewRawCameraImage, timeout=30)

        #convert camera image to opencv format
        opencv_image = cv2.cvtColor(np.asarray(event.image), cv2.COLOR_RGB2GRAY)

        #find the ball
        ball = find_ball.find_ball(opencv_image)

        #set annotator ball
        BallAnnotator.ball = ball
       

        await robot.drive_wheels(vel * self.direction, -vel * self.direction, acc, acc)

        if ball is not None: #and abs(ball[0] - len(opencv_image[0]) / 2 < 7):
            distance = 600 / (ball[2] * 2)
            
            self.found = True
            #Have no idea why this works but stops overshot without stopping
            await robot.drive_wheels(30, 30, 0, 0)

    def next(self):

        next_param = []
        if self.found:
            self.found = False
            next = chase
        else:
            next = search
        return (next, next_param)




class Chase(State):

    def __init__(self):
        self.name = "Chase"
        self.distance = 9999
        self.search_misses = 0
        self.offSet = 0
        self.max_misses = 20
        self.min_distance = 10

    async def run(self, next_param, robot):
        base = 70
        mod = .30
        acc = 200

        robot.set_head_angle(cozmo.util.degrees(0), in_parallel = True)
        robot.set_lift_height(0, in_parallel = True)

        event = await robot.world.wait_for(cozmo.camera.EvtNewRawCameraImage, timeout=30)

        #convert camera image to opencv format
        opencv_image = cv2.cvtColor(np.asarray(event.image), cv2.COLOR_RGB2GRAY)
        

        #find the ball
        ball = find_ball.find_ball(opencv_image)

        #set annotator ball
        BallAnnotator.ball = ball
       

        if ball is not None:
            self.distance = 600 / (ball[2] * 2)
            self.offSet = ball[0] - len(opencv_image[0]) / 2
            await robot.drive_wheels(base + self.offSet * mod , base - self.offSet * mod, acc, acc)
            self.search_misses = 0
        else:
            self.search_misses += 1
            self.distance = 9999
            # if self.search_misses >= self.max_misses:
            #     await robot.drive_wheels(0, 0)

    def next(self):
        next_param = []
        if self.search_misses > self.max_misses:
            next_state = search
            next_param.append(-1 if self.offSet < 0 else 1)

        elif self.distance < self.min_distance:
            next_state = approach

        else:
            next_state = chase

        return (next_state, next_param)

class Approach(State):
    def __init__(self):
        self.name = "Approach"
        self.distance = 9999
        self.search_misses = 0
        self.offSet = 0
        self.max_misses = 30
        self.min_distance = 10
        self.strike_distance = 4

    async def run(self, next_param, robot):
        base = 60
        mod = .2
        acc = 100

        robot.set_head_angle(cozmo.util.degrees(-15), in_parallel = True)
        robot.set_lift_height(0, in_parallel = True)

        event = await robot.world.wait_for(cozmo.camera.EvtNewRawCameraImage, timeout=30)

        #convert camera image to opencv format
        opencv_image = cv2.cvtColor(np.asarray(event.image), cv2.COLOR_RGB2GRAY)
        

        #find the ball
        ball = find_ball.find_ball(opencv_image)

        #set annotator ball
        BallAnnotator.ball = ball
       

        if ball is not None:
            self.distance = 600 / (ball[2] * 2)
            self.offSet = ball[0] - len(opencv_image[0]) / 2
            await robot.drive_wheels(base + self.offSet * mod , base - self.offSet * mod, acc, acc)
            self.search_misses = 0

        else:
            self.search_misses += 1
            self.distance = 9999



    def next(self):
        next_param = []
        if self.search_misses > self.max_misses:
            next_state = search
            next_param.append(-1 if self.offSet < 0 else 1)


        elif self.distance < self.strike_distance:
            next_state = strike

        elif self.distance < 9999 and self.distance > self.min_distance:
            next_state = chase

        else:
            next_state = approach

        return (next_state, next_param)


class Strike(State):
    def __init__(self):
        self.name = "Strike"
        self.distance = 9999
        self.search_misses = 0
        self.offSet = 0
        self.max_misses = 20
        self.min_distance = 5

    async def run(self, next_param, robot):
        base = 40
        mod = .2
        acc = 100

        robot.set_head_angle(cozmo.util.degrees(-15), in_parallel = True)
        event = await robot.world.wait_for(cozmo.camera.EvtNewRawCameraImage, timeout=30)

        #convert camera image to opencv format
        opencv_image = cv2.cvtColor(np.asarray(event.image), cv2.COLOR_RGB2GRAY)
        

        #find the ball
        ball = find_ball.find_ball(opencv_image)

        #set annotator ball
        BallAnnotator.ball = ball
       
        robot.set_lift_height(1, in_parallel = True)

        if ball is not None:
            self.distance = 600 / (ball[2] * 2)
            self.offSet = ball[0] - len(opencv_image[0]) / 2
            await robot.drive_wheels(base + self.offSet * mod , base - self.offSet * mod, acc, acc)
            #print(self.distance)
            self.search_misses = 0
        else:
            self.search_misses += 1
            self.distance = 9999

        if self.distance < 2.5:
            robot.set_lift_height(0, in_parallel = True)

    def next(self):
        next_param = []
        if self.search_misses > self.max_misses:
            next_state = search
            next_param.append(-1 if self.offSet < 0 else 1)

        elif self.distance > self.min_distance and self.distance < 9999:
            next_state = approach

        else:
            next_state = strike
        return (next_state, next_param)

class Wait(State):

    def __init__(self):
        self.name = "Wait"

    async def run(self, next_param, robot):
         await robot.drive_wheels(0, 0)

    def next(self):
        next_param = []
        return (wait, next_param)





class StateMachine:

    async def run(robot: cozmo.robot.Robot):
        robot.world.image_annotator.add_annotator('battery', BatteryAnnotator)
        robot.world.image_annotator.add_annotator('ball', BallAnnotator)

        current_state = search
        next_param = []

        try:
            print(cozmo.oled_face.dimensions())
            robot.set_head_angle(cozmo.util.degrees(0)).wait_for_completed()
            while 1:
                if current_state is wait: break
                #execute the current states behavior and then set the next state
                await current_state.set_face_image(robot)
                prev_state = current_state
                await current_state.run(next_param, robot)
                current_state, next_param = current_state.next()
                if prev_state is not current_state:
                    # robot.say_text("Yo", in_parallel = True)
                    print("\a")
                    print (prev_state.getName() + " ----> " + current_state.getName())



        except KeyboardInterrupt:
            print("")
            print("Exit requested by user")
        except cozmo.RobotBusy as e:
            print(e)


approach = Approach()
chase = Chase()
wait = Wait()
search = Search()
strike = Strike()

if __name__ == '__main__':
    cozmo.run_program(StateMachine.run, use_viewer = True, force_viewer_on_top = True)


StateMachine().run()

import pygame
import math
import numpy as np

pygame.init()

# -------------- smoothing functions (no touchy)
def add_more_points2(path, segment_length):
    new_path = []

    for i in range(0, len(path) - 1):

        distance = np.sqrt((path[i + 1][0] - path[i][0]) ** 2 + (path[i + 1][1] - path[i][1]) ** 2)
        num_of_points = int(round(distance / segment_length))

        if num_of_points == 0:
            new_path.append(path[i])

        else:
            segment_x = (path[i + 1][0] - path[i][0]) / num_of_points
            segment_y = (path[i + 1][1] - path[i][1]) / num_of_points

            for j in range(0, num_of_points):
                new_point = [(path[i][0] + j * segment_x), (path[i][1] + j * segment_y)]
                new_path.append(new_point)
    try:
        new_path.append(path[-1])
    except:
        return new_path

    return new_path


def sgn(num):
    if num >= 0:
        return 1
    else:
        return -1


def findMinAngle(absTargetAngle, currentHeading):
    minAngle = absTargetAngle - currentHeading

    if minAngle > 180 or minAngle < -180:
        minAngle = -1 * sgn(minAngle) * (360 - abs(minAngle))

    return minAngle


def smoothing(path, weight_data, weight_smooth, tolerance):
    smoothed_path = path.copy()
    change = tolerance

    while change >= tolerance:
        change = 0.0

        for i in range(1, len(path) - 1):

            for j in range(0, len(path[i])):
                aux = smoothed_path[i][j]

                smoothed_path[i][j] += weight_data * (path[i][j] - smoothed_path[i][j]) + weight_smooth * (
                        smoothed_path[i - 1][j] + smoothed_path[i + 1][j] - (2.0 * smoothed_path[i][j]))
                change += np.abs(aux - smoothed_path[i][j])

    return smoothed_path


def autoSmooth(path, maxAngle):
    currentMax = 0
    param = 0.01
    new_path = path
    firstLoop = True

    while currentMax >= maxAngle or firstLoop == True:

        param += 0.01
        firstLoop = False

        new_path = smoothing(path, CURVING_FACTOR, param, CURVING_FACTOR)
        currentMax = 0

        for i in range(1, len(new_path) - 2):
            angle1 = math.atan2(new_path[i][1] - new_path[i - 1][1], new_path[i][0] - new_path[i - 1][0]) * 180 / np.pi
            if angle1 < 0: angle1 += 360
            angle2 = math.atan2(new_path[i + 1][1] - new_path[i][1], new_path[i + 1][0] - new_path[i][0]) * 180 / np.pi
            if angle2 < 0: angle2 += 360

            if abs(findMinAngle(angle2, angle1)) > currentMax:
                currentMax = abs(findMinAngle(angle2, angle1))

    return new_path


# ------------------


# helper func for detecting node clicks
def is_mouse_click():
    return pygame.mouse.get_pressed()[0]


# helper func for detecting node hovering
def point_in_circle(px, py, x, y, r):
    return r >= math.sqrt((px - x) ** 2 + (py - y) ** 2)


class App:
    def __init__(self, node_list, window):
        self.smoothed_path = []
        self.node_list = node_list
        self.coordinates = []
        self.window = window
        self.selected_node = None
        self.del_node_list = []

    def draw(self):
        # draw lines and nodes for curved & normal path
        for i in range(len(self.node_list) - 1):
            pygame.draw.line(self.window, black, (self.node_list[i].x, self.node_list[i].y),
                             (self.node_list[i + 1].x, self.node_list[i + 1].y), 3)

        for coord in self.smoothed_path:
            coordx = coord[0] * SCALING_FACTOR
            coordy = abs(coord[1] - SCREEN_HEIGHT) * SCALING_FACTOR
            pygame.draw.circle(self.window, orange, (coordx, coordy), RADIUS)

        # draw the nodes --> diff colour if mouse hovering over
        for node in self.node_list:
            if node.is_mouse_hovering_over():
                pygame.draw.circle(self.window, black, (node.x, node.y), RADIUS + 2)
                pygame.draw.circle(self.window, light_blue, (node.x, node.y), RADIUS)
            else:
                pygame.draw.circle(self.window, black, (node.x, node.y), RADIUS + 2)
                pygame.draw.circle(self.window, blue, (node.x, node.y), RADIUS)

        # gibberish math to convert the actual coordinates back to pixel x and y
        for i in range(len(self.smoothed_path) - 1):
            coordx1 = self.smoothed_path[i][0] * SCALING_FACTOR
            coordy1 = abs(self.smoothed_path[i][1] - SCREEN_HEIGHT) * SCALING_FACTOR

            coordx2 = self.smoothed_path[i + 1][0] * SCALING_FACTOR
            coordy2 = abs(self.smoothed_path[i + 1][1] - SCREEN_HEIGHT) * SCALING_FACTOR

            pygame.draw.line(self.window, orange, (coordx1, coordy1), (coordx2, coordy2), 3)

    def update(self):
        # shove the node in the correct direction if out of bounds (im lazy)
        for node in self.node_list:
            if node.is_out_of_bounds():
                while node.is_out_of_bounds_left():
                    node.x += 1
                while node.is_out_of_bounds_right():
                    node.x -= 1
                while node.is_out_of_bounds_top():
                    node.y += 1
                while node.is_out_of_bounds_bottom():
                    node.y -= 1

        # to prevent user from moving multiple nodes
        if self.selected_node is None:
            for node in self.node_list:
                if node.is_mouse_hovering_over() and is_mouse_click():
                    self.selected_node = node

        # if a node has been selected
        if self.selected_node is not None:
            mouse = pygame.mouse.get_pos()
            self.selected_node.x = mouse[0]
            self.selected_node.y = mouse[1]

        # let go of the selected node
        if not is_mouse_click():
            self.selected_node = None

        # list to keep track of what the point would actually represent on a Cartesian plane
        self.coordinates = [[0 for i in range(2)] for j in range(len(self.node_list))]

        # populate list with converted values
        for i in range(len(self.node_list)):
            self.coordinates[i][0] = self.node_list[i].x / SCALING_FACTOR
            self.coordinates[i][1] = abs((self.node_list[i].y - SCREEN_HEIGHT * SCALING_FACTOR)) / SCALING_FACTOR

        # use the actual points in a Cartesian grid to generate smooth points
        path = add_more_points2(self.coordinates, SEGMENT_LENGTH)
        path = autoSmooth(path, MAXANGLE)
        self.smoothed_path = path

    def add_node(self, x, y):
        self.node_list.append(Node(x, y))

    # change this function for your own syntax preference
    def print_coordinates(self):

        print("PLOTTED COORDINATES: ")

        print("{", end="")

        for coord in self.coordinates:
            if coord == self.coordinates[len(self.coordinates) - 1]:
                print("{" + str(coord[0]) + ", " + str(coord[1]) + "}", end="")
            else:
                print("{" + str(coord[0]) + ", " + str(coord[1]) + "}" + ",")

        print("}")

        print("-------------------------------------")

        print("SMOOTHED COORDINATES: ")

        print("int" + " path" + "[" + str(len(self.smoothed_path)) +"]" + "[2]" + "=")

        print("{", end="")

        for coord in self.smoothed_path:
            if coord == self.smoothed_path[len(self.smoothed_path) - 1]:
                print("{" + str(coord[0]) + ", " + str(coord[1]) + "}", end="")
            else:
                print("{" + str(coord[0]) + ", " + str(coord[1]) + "}" + ",")

        print("}")

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    # use help func to see if mouse if hovering over node
    def is_mouse_hovering_over(self):
        mouse = pygame.mouse.get_pos()
        return point_in_circle(mouse[0], mouse[1], self.x, self.y, RADIUS)

    # to keep node in bounds
    def is_out_of_bounds(self):
        return self.x < 1 or self.x > SCREEN_WIDTH * SCALING_FACTOR or self.y < 1 or self.y > SCREEN_WIDTH * SCALING_FACTOR

    def is_out_of_bounds_left(self):
        return self.x < 0

    def is_out_of_bounds_right(self):
        return self.x > SCREEN_WIDTH * SCALING_FACTOR

    def is_out_of_bounds_top(self):
        return self.y < 0

    def is_out_of_bounds_bottom(self):
        return self.y > SCREEN_WIDTH * SCALING_FACTOR


# DO NOT CHANGE - field is 144 inches by 144 inches
SCREEN_WIDTH = 144
SCREEN_HEIGHT = 144

# change scaling factor to get more precise coordinates
# must resize image if scaling factor is changed
SCALING_FACTOR = 4

# radius of all nodes
RADIUS = 7

# change to fine-tune the curve
CURVING_FACTOR = 5
SEGMENT_LENGTH = 10
MAXANGLE = 80

# colours
light_blue = (68, 144, 242)
blue = (5, 110, 245)
black = (0, 0, 0)
orange = (245, 143, 10)

image = pygame.image.load('board.png')
board = pygame.transform.scale(image, (SCALING_FACTOR * SCREEN_WIDTH, SCREEN_HEIGHT * SCALING_FACTOR))

window = pygame.display.set_mode((SCREEN_WIDTH * SCALING_FACTOR, SCREEN_HEIGHT * SCALING_FACTOR))
clock = pygame.time.Clock()

node_list = [Node(150, 525)]
app = App(node_list, window)

pygame.display.set_caption("Way Point Generator")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            app.print_coordinates()
            pygame.quit()
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                app.print_coordinates()
                pygame.quit()
                quit()
            if event.key == pygame.K_SPACE:
                mouse = pygame.mouse.get_pos()
                app.add_node(mouse[0], mouse[1])
            if event.key == pygame.K_BACKSPACE:
                if len(app.node_list) > 0:
                    app.del_node_list.append(app.node_list.pop(len(app.node_list) - 1))
            if event.key == pygame.K_z:
                if len(app.del_node_list) > 0:
                    app.node_list.append(app.del_node_list.pop(len(app.del_node_list) - 1))

    app.window.fill((0, 0, 0))
    app.window.blit(board, (0, 0))
    app.update()
    app.draw()
    pygame.display.flip()

    clock.tick(60)

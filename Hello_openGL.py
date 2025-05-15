from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

point_x = 150
point_y = 150

ball_size = 5
ball_speed = 0.5

def draw_points(x, y):
    glPointSize(5) #pixel size. by default 1 thake
    glBegin(GL_POINTS)
    glVertex2f(x,y) #jekhane show korbe pixel
    glEnd()


def iterate():
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    glMatrixMode (GL_MODELVIEW)
    glLoadIdentity()

def animate():
    global point_x, point_y, ball_size, ball_speed
    point_x += ball_speed
    if point_x > 500:
        point_x = 150
    glutPostRedisplay()

def keyboard_listener(key, x, y):
    global point_x, ball_size, ball_speed
    if key == b'd':
        point_x += ball_speed 
        ball_size += 1
        ball_speed += 0.5
        glutPostRedisplay()
    if key == b'a':
        point_x -= ball_speed 
        ball_size -= 1
        ball_speed -= 0.5
        glutPostRedisplay()

def showScreen():
    global point_x, point_y, ball_size
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    iterate()
    glColor3f(1.0, 1.0, 0.0) #konokichur color set (RGB)
    #call the draw methods here
    glColor3f(1, 0, 0)
    glPointSize(ball_size)
    glBegin(GL_POINTS)
    glVertex2f(point_x, point_y) #coordinate
    glEnd()
    glutSwapBuffers()





glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(500, 500) #window size
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"Lab 423") #window name
glutDisplayFunc(showScreen)
glutIdleFunc(animate)
glutKeyboardFunc(keyboard_listener)

glutMainLoop()
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Game state variables
game_state = "PLAYING"  
player_health = 100
score = 0
level = 1
level_duration = 60 
level_start_time = time.time()
game_start_time = time.time()  
cheat_mode = False 
boss_active = False  
boss_spawned_this_level = False  
final_play_time = 0  
base_player_speed = 0.1  
speed_increase_rate = 0.00005 
base_virus_spawn_rate = 0.001  
game_paused = False 
game_speed_factor = 0.75 
game_speed_increase_rate = 0.0001  
max_game_speed = 1.5  

# Camera-related variables
player_pos = [0, 0, -100]  
player_velocity = [0, 0, -0.5] 
camera_offset = [0, 20, 30] 
camera_pos = [player_pos[0] + camera_offset[0],
              player_pos[1] + camera_offset[1],
              player_pos[2] + camera_offset[2]]

# Movement control variables
move_left = False
move_right = False
move_up = False
move_down = False
move_speed = 0.25
max_lateral_pos = 40  
max_vertical_pos = 40  

fovY = 70  
last_time = 0
GRID_LENGTH = 600

# Tunnel parameters
TUNNEL_RADIUS = 50
TUNNEL_SEGMENT_LENGTH = 100
TUNNEL_SEGMENTS = 35  
PULSE_AMPLITUDE = 3  
PULSE_SPEED = 0.0015  

# Virus and bullet parameters
viruses = []  
bullets = []  
shoot_cooldown = 0
boss_bullets = []  
boss_shoot_timer = 0

# Power-up parameters
powerups = []  
active_powerups = {
    "speed": {"active": False, "end_time": 0},
    "magnet": {"active": False, "end_time": 0},
    "laser": {"active": False, "end_time": 0},
    "invincibility": {"active": False, "end_time": 0}  
}
oxygen_collectibles = []  
virus_kill_tint_timer = 0  

fpp_view = False  

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draw text on screen."""
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_health_bar():
    """Draw the player's health bar."""
    bar_width = 200
    bar_height = 20
    x = 10
    y = 770
    
    # Draw border
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(x-2, y-2)
    glVertex2f(x+bar_width+2, y-2)
    glVertex2f(x+bar_width+2, y+bar_height+2)
    glVertex2f(x-2, y+bar_height+2)
    glEnd()
    
    # Draw health bar
    health_percentage = max(0, player_health) / 100.0
    health_width = bar_width * health_percentage
    
    if player_health > 60:
        glColor3f(0, 1, 0)  # Green for good health
    elif player_health > 30:
        glColor3f(1, 1, 0)  # Yellow for medium health
    else:
        glColor3f(1, 0, 0)  # Red for low health
    
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x+health_width, y)
    glVertex2f(x+health_width, y+bar_height)
    glVertex2f(x, y+bar_height)
    glEnd()
    
    # Draw health text
    glColor3f(1, 1, 1)
    draw_text(x+5, y+5, f"Health: {player_health}%")

def draw_hud():
    """Draw the game HUD."""
    draw_health_bar()
    
    # Draw score
    draw_text(800, 770, f"Score: {score}")
    
    # Draw level
    draw_text(10, 730, f"Level: {level}")
    
    # Draw item description panel on the left
    panel_x = 10
    panel_y = 600
    line_height = 25
    preview_offset_x = 10
    preview_offset_y = 8
    preview_size = 18
    text_offset_x = 40
    
    # Draw panel background
    glColor4f(0.0, 0.0, 0.0, 0.7)  # Semi-transparent black
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glVertex2f(panel_x - 5, panel_y - 5)
    glVertex2f(panel_x + 300, panel_y - 5)
    glVertex2f(panel_x + 300, panel_y + 200)
    glVertex2f(panel_x - 5, panel_y + 200)
    glEnd()
    glDisable(GL_BLEND)
    
    # Draw panel title
    glColor3f(1.0, 1.0, 1.0)
    draw_text(panel_x, panel_y, "Collectible Items", GLUT_BITMAP_HELVETICA_18)
    
    # Function to draw item preview in 2D overlay
    def draw_item_preview_2d(x, y, item_type):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(x, y, 0)
        glScalef(preview_size, preview_size, 1)
        if item_type == "speed":
            glColor3f(0.0, 0.6, 1.0)  # Blue
            glutSolidCube(0.5)
            glColor3f(1.0, 1.0, 1.0)
            sphere = gluNewQuadric()
            gluSphere(sphere, 0.18, 12, 12)
            gluDeleteQuadric(sphere)
        elif item_type == "magnet":
            glColor3f(0.8, 0.2, 1.0)  # Purple
            glutSolidCube(0.5)
            glColor3f(1.0, 1.0, 1.0)
            sphere = gluNewQuadric()
            gluSphere(sphere, 0.18, 12, 12)
            gluDeleteQuadric(sphere)
        elif item_type == "laser":
            glColor3f(1.0, 0.2, 0.2)  # Red
            glutSolidCube(0.5)
            glColor3f(1.0, 1.0, 1.0)
            sphere = gluNewQuadric()
            gluSphere(sphere, 0.18, 12, 12)
            gluDeleteQuadric(sphere)
        elif item_type == "health":
            glColor3f(0.2, 1.0, 0.2)  # Green
            glutSolidCube(0.5)
            glColor3f(1.0, 1.0, 1.0)
            sphere = gluNewQuadric()
            gluSphere(sphere, 0.18, 12, 12)
            gluDeleteQuadric(sphere)
        elif item_type == "invincibility":
            glColor3f(1.0, 0.2, 0.8)  # Pink
            glutSolidCube(0.5)
            glColor3f(1.0, 1.0, 1.0)
            sphere = gluNewQuadric()
            gluSphere(sphere, 0.18, 12, 12)
            gluDeleteQuadric(sphere)
        elif item_type == "oxygen":
            glColor3f(1.0, 1.0, 1.0)  # White
            sphere = gluNewQuadric()
            gluSphere(sphere, 0.25, 8, 8)
            gluDeleteQuadric(sphere)
            # Add sparkle effect
            glColor3f(1.0, 1.0, 1.0)  # White sparkle
            glPointSize(3.0)
            glBegin(GL_POINTS)
            glVertex3f(0, 0, 0)
            glEnd()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    # Draw power-ups with previews in 2D overlay
    current_y = panel_y - line_height
    draw_item_preview_2d(panel_x + preview_offset_x, current_y + preview_offset_y, "speed")
    glColor3f(0.0, 0.6, 1.0)  # Blue
    draw_text(panel_x + text_offset_x, current_y, "Speed (Blue)", GLUT_BITMAP_HELVETICA_12)
    glColor3f(1.0, 1.0, 1.0)
    draw_text(panel_x + text_offset_x, current_y - line_height, "- Increases speed (10s)", GLUT_BITMAP_HELVETICA_12)
    
    current_y -= line_height * 2
    draw_item_preview_2d(panel_x + preview_offset_x, current_y + preview_offset_y, "magnet")
    glColor3f(0.8, 0.2, 1.0)  # Purple
    draw_text(panel_x + text_offset_x, current_y, "Magnet (Purple)", GLUT_BITMAP_HELVETICA_12)
    glColor3f(1.0, 1.0, 1.0)
    draw_text(panel_x + text_offset_x, current_y - line_height, "- Attracts collectibles (15s)", GLUT_BITMAP_HELVETICA_12)
    
    current_y -= line_height * 2
    draw_item_preview_2d(panel_x + preview_offset_x, current_y + preview_offset_y, "laser")
    glColor3f(1.0, 0.2, 0.2)  # Red
    draw_text(panel_x + text_offset_x, current_y, "Laser (Red)", GLUT_BITMAP_HELVETICA_12)
    glColor3f(1.0, 1.0, 1.0)
    draw_text(panel_x + text_offset_x, current_y - line_height, "- Laser beams (10s)", GLUT_BITMAP_HELVETICA_12)
    
    current_y -= line_height * 2
    draw_item_preview_2d(panel_x + preview_offset_x, current_y + preview_offset_y, "health")
    glColor3f(0.2, 1.0, 0.2)  # Green
    draw_text(panel_x + text_offset_x, current_y, "Health (Green)", GLUT_BITMAP_HELVETICA_12)
    glColor3f(1.0, 1.0, 1.0)
    draw_text(panel_x + text_offset_x, current_y - line_height, "- Heals 25 HP", GLUT_BITMAP_HELVETICA_12)
    
    current_y -= line_height * 2
    draw_item_preview_2d(panel_x + preview_offset_x, current_y + preview_offset_y, "invincibility")
    glColor3f(1.0, 0.2, 0.8)  # Pink
    draw_text(panel_x + text_offset_x, current_y, "Invincibility (Pink)", GLUT_BITMAP_HELVETICA_12)
    glColor3f(1.0, 1.0, 1.0)
    draw_text(panel_x + text_offset_x, current_y - line_height, "- Full heal + 10s invincible", GLUT_BITMAP_HELVETICA_12)
    
    current_y -= line_height * 2
    draw_item_preview_2d(panel_x + preview_offset_x, current_y + preview_offset_y, "oxygen")
    glColor3f(1.0, 1.0, 1.0)  # White
    draw_text(panel_x + text_offset_x, current_y, "Oxygen (White)", GLUT_BITMAP_HELVETICA_12)
    glColor3f(1.0, 1.0, 1.0)
    draw_text(panel_x + text_offset_x, current_y - line_height, "- Worth 5 points, +1 HP", GLUT_BITMAP_HELVETICA_12)
    
    # Show active powerups
    y_pos = 690
    if active_powerups["speed"]["active"]:
        draw_text(10, y_pos, "Speed Boost Active!", GLUT_BITMAP_HELVETICA_12)
        y_pos -= 20
    if active_powerups["magnet"]["active"]:
        draw_text(10, y_pos, "Magnet Mode Active!", GLUT_BITMAP_HELVETICA_12)
        y_pos -= 20
    if active_powerups["laser"]["active"]:
        draw_text(10, y_pos, "Laser Mode Active!", GLUT_BITMAP_HELVETICA_12)
        y_pos -= 20
    if active_powerups.get("invincibility", {}).get("active", False):
        draw_text(10, y_pos, "INVINCIBLE!", GLUT_BITMAP_HELVETICA_12)
        y_pos -= 20
    
    # Show cheat mode status
    if cheat_mode:
        draw_text(800, 730, "CHEAT MODE: ON", GLUT_BITMAP_HELVETICA_12)

def draw_tunnel():
    """Draw a smooth continuous horizontal tunnel with pulsing cylinders and lighting."""
    glPushMatrix()
    time_val = glutGet(GLUT_ELAPSED_TIME) * PULSE_SPEED
    pulse = math.sin(time_val) * PULSE_AMPLITUDE
    radius = TUNNEL_RADIUS + pulse


    glColor3f(0.8, 0.2, 0.2)  # Consistent tunnel color
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
    glMaterialfv(GL_FRONT, GL_SHININESS, [50.0])

    start_segment = int(player_pos[2] / TUNNEL_SEGMENT_LENGTH) - 5  
    
    # Draw multiple connected segments to create a continuous tunnel
    for i in range(start_segment, start_segment + TUNNEL_SEGMENTS):
        z_start = i * TUNNEL_SEGMENT_LENGTH
        
        segment_dist = abs(player_pos[2] - z_start)
        if segment_dist > TUNNEL_SEGMENTS * TUNNEL_SEGMENT_LENGTH * 0.75:
            continue
        
        glPushMatrix()
        glTranslatef(0, 0, z_start)

        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE)
        

        segment_pulse = math.sin(time_val + i * 0.3) * PULSE_AMPLITUDE * 0.5
        segment_radius = radius + segment_pulse
        

        gluCylinder(quad, segment_radius, segment_radius * 0.98, TUNNEL_SEGMENT_LENGTH, 32, 8)
        
        # Add inner details to make it look more like a blood vessel
        glColor3f(0.9, 0.2, 0.2)  # Slightly lighter red for inner details
        glPushMatrix()
        glRotatef(i * 30, 0, 0, 1)  # Rotate each segment for variety
        
        # Add subtle texture with rings at the start of each segment
        for j in range(3):
            ring_pos = j * TUNNEL_SEGMENT_LENGTH / 4
            glPushMatrix()
            glTranslatef(0, 0, ring_pos)
            glutSolidTorus(0.8, segment_radius * 0.95, 8, 32)
            glPopMatrix()
        
        glPopMatrix()
        
        gluDeleteQuadric(quad)
        glPopMatrix()
    
    glPopMatrix()

def draw_player():
    """Draw the player's nanobot."""
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    
    # Apply color based on health/state
    if cheat_mode:
        # Rainbow effect for cheat mode
        time_val = glutGet(GLUT_ELAPSED_TIME) * 0.001
        r = 0.5 + 0.5 * math.sin(time_val)
        g = 0.5 + 0.5 * math.sin(time_val + 2.0)
        b = 0.5 + 0.5 * math.sin(time_val + 4.0)
        glColor3f(r, g, b)
    else:
        # Normal blue color
        glColor3f(0.2, 0.4, 1.0)
    
    # Draw the main body
    sphere = gluNewQuadric()
    gluSphere(sphere, 5, 16, 16)
    gluDeleteQuadric(sphere)
    
    # Draw small protrusions for a more machine-like look
    glPushMatrix()
    glTranslatef(0, 0, 6)
    glColor3f(0.3, 0.6, 1.0)
    cylinder = gluNewQuadric()
    gluCylinder(cylinder, 2, 1, 4, 8, 1)
    gluDeleteQuadric(cylinder)
    glPopMatrix()
    
    # Draw small wings
    glPushMatrix()
    glColor3f(0.3, 0.5, 0.9)
    glTranslatef(0, 0, -2)
    glRotatef(90, 0, 1, 0)
    
    glBegin(GL_TRIANGLES)
    # Right wing
    glVertex3f(0, 0, 0)
    glVertex3f(7, 3, 0)
    glVertex3f(5, -2, 0)
    # Left wing
    glVertex3f(0, 0, 0)
    glVertex3f(-7, 3, 0)
    glVertex3f(-5, -2, 0)
    glEnd()
    
    glPopMatrix()
    
    glPopMatrix()

def draw_viruses():
    """Draw all active viruses."""
    for virus in viruses:
        x, y, z, size, health, v_type = virus
        
        glPushMatrix()
        glTranslatef(x, y, z)
        

        if v_type == "boss":

            glColor3f(0.5, 0.2, 0.8)  # Purple-blue for boss
        else:
            glColor3f(0.2, 0.7, 0.3)  # Green for regular viruses
        
        # Draw the virus body
        sphere = gluNewQuadric()
        gluSphere(sphere, size, 16, 16)
        gluDeleteQuadric(sphere)
        
        # Draw spikes for viruses
        if v_type == "boss":
            spike_count = 16  # More spikes for boss virus
            spike_length = size * 0.6  # Longer spikes
            
            # Draw inner core for boss virus
            glColor3f(0.3, 0.1, 0.5)  # Darker purple core
            inner_sphere = gluNewQuadric()
            gluSphere(inner_sphere, size * 0.7, 16, 16)
            gluDeleteQuadric(inner_sphere)
            
            # Draw boss spikes with gradient coloring
            for i in range(spike_count):
                angle = (i / spike_count) * 2 * math.pi
                spike_x = math.cos(angle) * size
                spike_y = math.sin(angle) * size
                
                glPushMatrix()
                glTranslatef(spike_x, spike_y, 0)
                glRotatef(90, -math.sin(angle), math.cos(angle), 0)
                
                cone = gluNewQuadric()
                
                # Darker color for spikes
                glColor3f(0.4, 0.1, 0.6)
                gluCylinder(cone, size * 0.15, 0, spike_length, 8, 1)
                gluDeleteQuadric(cone)
                
                glPopMatrix()
        else:
            spike_count = 8
            spike_length = size * 0.4
                
            for i in range(spike_count):
                angle = (i / spike_count) * 2 * math.pi
                spike_x = math.cos(angle) * size
                spike_y = math.sin(angle) * size
                
                glPushMatrix()
                glTranslatef(spike_x, spike_y, 0)
                glRotatef(90, -math.sin(angle), math.cos(angle), 0)
                
                cone = gluNewQuadric()
                gluCylinder(cone, size * 0.15, 0, spike_length, 8, 1)
                gluDeleteQuadric(cone)
                
                glPopMatrix()
        
        glPopMatrix()

def draw_bullets():
    """Draw all active bullets."""
    for bullet in bullets:
        x, y, z, direction = bullet
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Change bullet appearance based on laser power-up
        if active_powerups["laser"]["active"]:
            # Get elapsed time for animated effects
            time_val = glutGet(GLUT_ELAPSED_TIME) * 0.001
            

            glColor3f(1.0, 0.5, 0.0)  
            
 
            beam_length = 50 + 10 * math.sin(time_val * 8)
            
            # Draw the main beam as a thin cylinder
            cylinder = gluNewQuadric()
            gluCylinder(cylinder, 0.8, 0.3, -beam_length, 12, 1)  # Tapered beam
            gluDeleteQuadric(cylinder)
            
            # Add core beam - brighter center
            glColor3f(1.0, 0.8, 0.2)  # Brighter yellow-orange core
            inner_cylinder = gluNewQuadric()
            gluCylinder(inner_cylinder, 0.4, 0.1, -beam_length, 8, 1)
            gluDeleteQuadric(inner_cylinder)
            
            # Add energy rings along the beam
            ring_count = 5
            for i in range(ring_count):
                ring_pos = -i * (beam_length/ring_count) - 5  
                ring_scale = 1.0 - (i / ring_count) * 0.5
                
                glPushMatrix()
                glTranslatef(0, 0, ring_pos)
                
                # Animated rotation for energy rings
                ring_angle = time_val * 180 + i * 30
                glRotatef(ring_angle, 0, 0, 1)
                
                glColor3f(1.0, 0.7, 0.1)  # Orange-gold for rings
                glutSolidTorus(0.3 * ring_scale, 1.5 * ring_scale, 8, 16)
                glPopMatrix()
            
            # Add a bright glow effect at the origin
            glColor3f(1.0, 1.0, 0.5)  # Bright yellow glow
            sphere = gluNewQuadric()
            gluSphere(sphere, 1.2, 12, 12)
            gluDeleteQuadric(sphere)
            
            # Add particle effect at the base
            glPointSize(5.0)
            glBegin(GL_POINTS)
            particle_count = 8
            for i in range(particle_count):
                angle = (i / particle_count) * 2 * math.pi
                dist = 1.5 + 0.5 * math.sin(time_val * 10 + i)
                px = math.cos(angle) * dist
                py = math.sin(angle) * dist
                # Color gradient from yellow to red
                glColor3f(1.0, 0.3 + 0.7 * (i/particle_count), 0.0)
                glVertex3f(px, py, 0)
            glEnd()
            
        else:
      
            glColor3f(1.0, 0.8, 0.0)  # Yellow for bullets
            sphere = gluNewQuadric()
            gluSphere(sphere, 1.8, 10, 10)  
            gluDeleteQuadric(sphere)
        
        glPopMatrix()

def draw_powerups():
    """Draw all active power-ups."""
    for powerup in powerups:
        x, y, z, p_type = powerup
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Rotate powerups for visual effect
        time_val = glutGet(GLUT_ELAPSED_TIME) * 0.001
        glRotatef(time_val * 60, 0, 1, 0)
        
        # Different colors for different power-ups
        if p_type == "speed":
            glColor3f(0.0, 0.6, 1.0)  # Blue for speed
        elif p_type == "magnet":
            glColor3f(0.8, 0.2, 1.0)  # Purple for magnet
        elif p_type == "laser":
            glColor3f(1.0, 0.2, 0.2)  # Red for laser
        elif p_type == "health":
            glColor3f(0.2, 1.0, 0.2)  # Green for health
        elif p_type == "invincibility":
            glColor3f(1.0, 0.2, 0.8)  # Pink for invincibility
        
        # Draw the power-up as a cube with a sphere inside
        glutSolidCube(4)
        
        # Inner sphere with different color
        glColor3f(1.0, 1.0, 1.0)  # White inner sphere
        sphere = gluNewQuadric()
        gluSphere(sphere, 1.5, 12, 12)
        gluDeleteQuadric(sphere)
        
        glPopMatrix()

def draw_oxygen_collectibles():
    """Draw oxygen collectibles."""
    for oxygen in oxygen_collectibles:
        x, y, z = oxygen
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Sparkle effect
        time_val = glutGet(GLUT_ELAPSED_TIME) * 0.003
        scale = 0.8 + 0.2 * math.sin(time_val * 5)
        glScalef(scale, scale, scale)
        
        # White oxygen particle (changed from Red)
        glColor3f(1.0, 1.0, 1.0)
        sphere = gluNewQuadric()
        gluSphere(sphere, 2.0, 8, 8)
        gluDeleteQuadric(sphere)
        
        # Add glow effect
        glColor3f(1.0, 1.0, 1.0)  # White glow (changed from Red)
        glPointSize(4.0)
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()
        
        glPopMatrix()

def draw_damage_tint():
    """Draw a red tint when player takes damage."""
    global player_health
    
    if player_health < 100 and not cheat_mode:
        # Calculate tint intensity based on health
        tint_alpha = max(0, (100 - player_health) / 100.0) * 0.5
        
        # Draw a red overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glColor4f(1.0, 0.0, 0.0, tint_alpha)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(1000, 0)
        glVertex2f(1000, 800)
        glVertex2f(0, 800)
        glEnd()
        
        glDisable(GL_BLEND)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

def draw_game_over_screen():
    """Draw the game over screen."""
    # Use frozen play time
    total_time = final_play_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)

    # Switch to 2D mode for overlay
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Disable depth test and lighting for overlay/text
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    # Draw semi-transparent black overlay
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.7)  # Black with 70% opacity
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    glDisable(GL_BLEND)

    # Game over text
    glColor3f(1.0, 0.0, 0.0)
    draw_text(500, 500, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)

    # Score and stats
    glColor3f(1.0, 1.0, 1.0)
    draw_text(500, 450, f"Final Score: {score}")
    draw_text(500, 400, f"Level Reached: {level}")
    draw_text(500, 350, f"Time Played: {minutes:02d}:{seconds:02d}")

    # Restart instructions
    glColor3f(0.8, 0.8, 0.8)
    draw_text(500, 300, "Press 'R' to restart")

    # Restore OpenGL state
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_blood_cells():
    """Draw floating blood cells as background particles inside the tunnel."""
    # Use a deterministic approach based on player position
    seed_z = int(player_pos[2] / 50)
    random.seed(seed_z)
    
    # Draw a set of blood cells in the current region
    for i in range(30):
 
        max_cell_distance = TUNNEL_RADIUS * 0.85  # Keep cells well inside tunnel
        

        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, max_cell_distance)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        z = player_pos[2] - 50 + random.uniform(0, 100)
        
        # Only draw cells that are ahead of the player
        if z < player_pos[2] + 150:
            glPushMatrix()
            glTranslatef(x, y, z)
            glRotatef(random.uniform(0, 360), random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
            
            # Red blood cells are flattened spheres
            glColor3f(0.7, 0.1, 0.1)
            glPushMatrix()
            glScalef(1.0, 0.3, 1.0)
            glutSolidSphere(2.5, 12, 8)
            glPopMatrix()
            
            # Draw depression in the middle
            glColor3f(0.6, 0.1, 0.1)
            glPushMatrix()
            glTranslatef(0, 0, 0)
            glScalef(0.5, 0.5, 0.5)
            glutSolidTorus(0.5, 1.5, 8, 12)
            glPopMatrix()
            
            glPopMatrix()
    

    random.seed()

def spawn_virus(is_boss=False):
    """Spawn a new virus in the tunnel ahead of the player."""
    # Calculate spawn distance from center to ensure virus stays inside tunnel
    max_spawn_distance = TUNNEL_RADIUS * 0.6  # Reduced from 0.7 to keep viruses well inside
    
    # Random position in the tunnel - use polar coordinates for better distribution
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(0, max_spawn_distance)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    z = player_pos[2] - 400 if is_boss else player_pos[2] - 200  # Boss spawns further away

    if is_boss:
        size = 12.0
        # Significantly increase boss health based on level - much more challenging
        health = level * 2  # Double the previous value for more challenge
        v_type = "boss"
    else:
        size = 3.5
        # Scale regular virus health with level - viruses get stronger in later levels
        if level >= 4:
            health = 2  # Higher levels have tougher viruses
        elif level >= 2:
            health = random.choice([1, 2])  # Mix of normal and tough viruses
        else:
            health = 1  # Normal health in level 1
        v_type = "regular"

    viruses.append([x, y, z, size, health, v_type])

def spawn_powerup():
    """Spawn a random power-up in the tunnel ahead of the player."""
    # Calculate spawn distance from center to ensure powerup stays inside tunnel
    max_spawn_distance = TUNNEL_RADIUS * 0.6  # Reduced from 0.7
    
    # Random position in the tunnel - use polar coordinates for better distribution
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(0, max_spawn_distance)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    z = player_pos[2] - 200  # Spawn ahead of the player

    # Power-up types and their spawn chances
    # Regular power-ups: 97% (speed, magnet, laser, health)
    # Rare invincibility: 3%
    if random.random() < 0.03:
        p_type = "invincibility"  # Pink, very rare
    else:
        p_type = random.choice(["speed", "magnet", "laser", "health"])  # Green health included

    powerups.append([x, y, z, p_type])

def spawn_oxygen():
    """Spawn oxygen collectibles in the tunnel ahead of the player."""
    # Calculate spawn distance from center to ensure oxygen stays inside tunnel
    max_spawn_distance = TUNNEL_RADIUS * 0.6  # Reduced from 0.7
    
    # Random position in the tunnel - use polar coordinates for better distribution
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(0, max_spawn_distance)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    
    z = player_pos[2] - 200  # Spawn ahead of the player
    
    oxygen_collectibles.append([x, y, z])

def fire_bullet():
    """Fire a bullet from the player's position."""
    global shoot_cooldown
    
    # Check cooldown
    current_time = time.time()
    if current_time - shoot_cooldown < 0.2:  # 0.2 seconds between shots
        return
    
    # Reset cooldown
    shoot_cooldown = current_time
    
    # Create bullet
    bullets.append([player_pos[0], player_pos[1], player_pos[2], [0, 0, -1]])

def update_player():
    """Update player position based on controls."""
    global player_pos, player_health, game_state, final_play_time, base_player_speed, game_speed_factor
    
    # Update player position based on keyboard controls
    current_move_speed = move_speed * game_speed_factor  # Scale movement speed with game speed
    
    if move_left and player_pos[0] > -max_lateral_pos:
        player_pos[0] -= current_move_speed
    if move_right and player_pos[0] < max_lateral_pos:
        player_pos[0] += current_move_speed
    if move_up and player_pos[1] < max_vertical_pos:
        player_pos[1] += current_move_speed
    if move_down and player_pos[1] > -max_vertical_pos:
        player_pos[1] -= current_move_speed
    
    # Additional constraint: Make sure player stays inside tunnel radius
    distance_from_center = math.sqrt(player_pos[0]**2 + player_pos[1]**2)
    max_allowed_distance = TUNNEL_RADIUS * 0.85  # Leave some margin from the wall
    
    if distance_from_center > max_allowed_distance:
        # Scale the position to keep the player inside
        scale_factor = max_allowed_distance / distance_from_center
        player_pos[0] *= scale_factor
        player_pos[1] *= scale_factor
    
    # Gradually increase base speed over time (up to a maximum) - faster acceleration
    if base_player_speed < 0.25:
        base_player_speed += speed_increase_rate * game_speed_factor
    
    # Gradually increase global game speed (affects everything) - faster acceleration
    if game_speed_factor < max_game_speed and not boss_active:
        game_speed_factor += game_speed_increase_rate
    
    # Stop forward movement if boss is active
    if boss_active:
        current_speed = 0  # No forward movement during boss fight
    else:
        # Increase speed based on level for faster progression
        level_speed_bonus = (level - 1) * 0.05  # 5% speed increase per level
        
        if cheat_mode:
            current_speed = base_player_speed * 3.0 * game_speed_factor
        elif active_powerups["speed"]["active"]:
            current_speed = (base_player_speed * 2.0 + level_speed_bonus) * game_speed_factor
        else:
            current_speed = (base_player_speed + level_speed_bonus) * game_speed_factor
    
    player_pos[2] -= current_speed
    
    # Check if player health is zero (only if not in cheat mode)
    if player_health <= 0 and not cheat_mode:
        if game_state != "GAME_OVER":
            final_play_time = time.time() - game_start_time
        game_state = "GAME_OVER"

def update_viruses():
    """Update virus positions and check for collisions."""
    global viruses, score, player_health
    
    viruses_to_remove = []
    
    for i, virus in enumerate(viruses):
        x, y, z, size, health, v_type = virus
        
        # Move virus toward player
        # Reduce chase speed for both regular and boss viruses
        base_speed = 0.08 if v_type == "regular" else 0.04  # Reduced from 0.15 and 0.075
        speed = base_speed * game_speed_factor  # Apply game speed factor
        
        direction_x = player_pos[0] - x
        direction_y = player_pos[1] - y
        direction_z = player_pos[2] - z
        
        # Normalize direction vector
        length = math.sqrt(direction_x**2 + direction_y**2 + direction_z**2)
        if length > 0:
            direction_x /= length
            direction_y /= length
            direction_z /= length
        
        # Update virus position
        virus[0] += direction_x * speed
        virus[1] += direction_y * speed
        virus[2] += direction_z * speed
        
        # Check for collision with player
        distance = math.sqrt((player_pos[0] - x)**2 + (player_pos[1] - y)**2 + (player_pos[2] - z)**2)
        if distance < (5 + size):  # Player radius (5) + virus size
            if not cheat_mode and not active_powerups.get("invincibility", {}).get("active", False):
                # Damage player
                damage = 10 if v_type == "regular" else 25
                player_health -= damage
            
            # Remove virus
            viruses_to_remove.append(i)
        
        # Remove viruses that are behind the player by a certain distance
        # This allows player to dodge viruses if they move quickly enough
        if z > player_pos[2] + 25:  # Reduced from 50 to 25 to give more dodging opportunity
            # Only remove virus if it's sufficiently far from player in lateral position
            # This ensures the virus doesn't just disappear when near the player
            lateral_distance = math.sqrt((player_pos[0] - x)**2 + (player_pos[1] - y)**2)
            if lateral_distance > 15:  # If virus is not close laterally, remove it
                viruses_to_remove.append(i)
            # If virus is very far behind player, remove regardless of lateral distance
            elif z > player_pos[2] + 50:
                viruses_to_remove.append(i)
    
    # Remove viruses (in reverse order to avoid index issues)
    for i in sorted(viruses_to_remove, reverse=True):
        if i < len(viruses):  # Safety check
            viruses.pop(i)

def update_bullets():
    """Update bullet positions and check for collisions with viruses."""
    global bullets, viruses, score, virus_kill_tint_timer
    
    bullets_to_remove = []
    
    for i, bullet in enumerate(bullets):
        x, y, z, direction = bullet
        
        # Move bullet forward - apply game speed factor
        base_speed = 2.0
        speed = base_speed * game_speed_factor
        bullet[2] += direction[2] * speed
        
        # Calculate bullet range based on visible tunnel length
        # TUNNEL_SEGMENT_LENGTH * TUNNEL_SEGMENTS gives approximate tunnel length
        visible_tunnel_length = TUNNEL_SEGMENT_LENGTH * TUNNEL_SEGMENTS
        bullet_visible_length = visible_tunnel_length * 0.3  # Bullets visible for 60% of tunnel length
        
        # Remove bullets when they're beyond 60% of the visible tunnel length
        if abs(bullet[2] - player_pos[2]) > bullet_visible_length:
            bullets_to_remove.append(i)
            continue
        
        # Check for collision with viruses
        viruses_hit = []
        for j, virus in enumerate(viruses):
            vx, vy, vz, size, health, v_type = virus
            
            # For laser, check if virus is directly in front of player
            if active_powerups["laser"]["active"]:
                # Improved laser collision: wider detection beam
                if abs(vx - player_pos[0]) < 8 and abs(vy - player_pos[1]) < 8 and vz < player_pos[2]:
                    viruses_hit.append(j)
            else:
                # Normal bullet collision
                distance = math.sqrt((x - vx)**2 + (y - vy)**2 + (z - vz)**2)
                if distance < (1.8 + size):  # Updated bullet radius (1.8) + virus size
                    viruses_hit.append(j)
                    bullets_to_remove.append(i)
                    break
        
        # Process virus hits
        for j in sorted(viruses_hit, reverse=True):
            if j < len(viruses):
                # Apply damage based on weapon type
                if cheat_mode:
                    damage = 3  # Cheat mode damage remains unchanged
                elif active_powerups["laser"]["active"]:
                    damage = 2  # Laser does exactly double normal damage (2 instead of 1)
                else:
                    damage = 1  # Normal bullet damage
                
                viruses[j][4] -= damage
                if viruses[j][4] <= 0:
                    if viruses[j][5] == "boss":
                        score += 100
                    else:
                        score += 10
                    viruses.pop(j)
                    virus_kill_tint_timer = 0.3  # Show tint for 0.3 seconds
    
    # Remove bullets (in reverse order to avoid index issues)
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(bullets):  # Safety check
            bullets.pop(i)

def update_powerups():
    """Update power-up positions and check for collisions with player."""
    global powerups, active_powerups, player_health
    powerups_to_remove = []
    current_time = time.time()
    # Check for expired power-ups
    for p_type, data in active_powerups.items():
        if data["active"] and current_time > data["end_time"]:
            data["active"] = False
    # Process active power-ups
    for i, powerup in enumerate(powerups):
        x, y, z, p_type = powerup
        # Check for collision with player
        distance = math.sqrt((player_pos[0] - x)**2 + (player_pos[1] - y)**2 + (player_pos[2] - z)**2)
        if distance < 10:  # Player radius (5) + power-up size
            if p_type == "speed":
                active_powerups["speed"]["active"] = True
                active_powerups["speed"]["end_time"] = current_time + 10
            elif p_type == "magnet":
                active_powerups["magnet"]["active"] = True
                active_powerups["magnet"]["end_time"] = current_time + 15
            elif p_type == "laser":
                active_powerups["laser"]["active"] = True
                active_powerups["laser"]["end_time"] = current_time + 10
            elif p_type == "health":
                player_health = min(100, player_health + 25)  # Green: heal 25, max 100
            elif p_type == "invincibility":
                player_health = 100  # Pink: full heal
                active_powerups["invincibility"]["active"] = True
                active_powerups["invincibility"]["end_time"] = current_time + 10
            powerups_to_remove.append(i)
        if z > player_pos[2] + 50:
            powerups_to_remove.append(i)
    for i in sorted(powerups_to_remove, reverse=True):
        if i < len(powerups):
            powerups.pop(i)

def update_oxygen():
    """Update oxygen collectible positions and check for collisions with player."""
    global oxygen_collectibles, score, player_health
    
    oxygen_to_remove = []
    
    # Calculate magnet range
    magnet_range = 30 if active_powerups["magnet"]["active"] else 0
    
    for i, oxygen in enumerate(oxygen_collectibles):
        x, y, z = oxygen
        
        # Apply magnet effect if active
        if active_powerups["magnet"]["active"]:
            # Calculate direction to player
            direction_x = player_pos[0] - x
            direction_y = player_pos[1] - y
            direction_z = player_pos[2] - z
            
            # Calculate distance to player
            distance = math.sqrt(direction_x**2 + direction_y**2 + direction_z**2)
            
            # If within magnet range, move toward player
            if distance < magnet_range:
                # Normalize direction vector
                if distance > 0:
                    direction_x /= distance
                    direction_y /= distance
                    direction_z /= distance
                
                # Move oxygen toward player
                magnet_speed = 1.0
                oxygen[0] += direction_x * magnet_speed
                oxygen[1] += direction_y * magnet_speed
                oxygen[2] += direction_z * magnet_speed
        
        # Check for collision with player
        distance = math.sqrt((player_pos[0] - x)**2 + (player_pos[1] - y)**2 + (player_pos[2] - z)**2)
        if distance < 7:  # Player radius (5) + oxygen radius (2)
            # Add score
            score += 5  # Oxygen worth 5 points
            
            # Increase player health by 1 (new feature)
            player_health = min(100, player_health + 1)  # Cap at 100 HP
            
            # Remove oxygen
            oxygen_to_remove.append(i)
        
        # Remove oxygen collectibles that are behind the player
        if z > player_pos[2] + 50:
            oxygen_to_remove.append(i)
    
    # Remove oxygen collectibles (in reverse order to avoid index issues)
    for i in sorted(oxygen_to_remove, reverse=True):
        if i < len(oxygen_collectibles):  # Safety check
            oxygen_collectibles.pop(i)

def check_level_progress():
    """Check if it's time to advance to the next level based on score thresholds."""
    global level, level_start_time, boss_active, boss_spawned_this_level

    # Define score thresholds for each level
    score_thresholds = {1: 200, 2: 800, 3: 1000, 4: 1500, 5: 2000}

    # Check if the current score meets the threshold for the next level
    if level < 5 and score >= score_thresholds[level]:
        level += 1
        level_start_time = time.time()
        boss_spawned_this_level = False  # Reset boss spawn flag for new level
        # Spawn bosses at the start of every level - number increases with level
        boss_active = True
        
        # Spawn multiple bosses in higher levels
        boss_count = min(level, 3)  # Cap at 3 bosses maximum
        for _ in range(boss_count):
            spawn_virus(is_boss=True)
        
        boss_spawned_this_level = True

def spawn_game_objects():
    global boss_active, boss_spawned_this_level, level, level_start_time, base_virus_spawn_rate, base_player_speed
    """Spawn game objects (viruses, powerups, collectibles) based on game rules."""
    
    # Calculate dynamic virus spawn rate based on player speed
    # Map from base_player_speed (0.05 to 0.25) to spawn rates
    # At minimum speed (0.05): very low spawn rate
    # At maximum speed (0.25): higher spawn rate based on level
    speed_factor = (base_player_speed - 0.05) / 0.2  # 0.0 to 1.0 based on current speed
    
    # Adjust spawn probability based on level, boss status, and current speed
    if boss_active:
        virus_spawn_chance = 0.01 * speed_factor + 0.005  # Very low, slight increase with speed
    elif level <= 2:
        virus_spawn_chance = 0.004 * speed_factor + 0.001  # 0.1% to 0.5% based on speed
    elif level <= 4:
        virus_spawn_chance = 0.008 * speed_factor + 0.002  # 0.2% to 1% based on speed
    else:
        virus_spawn_chance = 0.015 * speed_factor + 0.005  # 0.5% to 2% based on speed

    # Only spawn regular viruses if not in boss mode
    if not boss_active:
        # Spawn viruses randomly - higher chance in higher levels
        virus_spawn_chance *= (1 + (level - 1) * 0.2)  # 20% increase per level
        if random.random() < virus_spawn_chance:
            spawn_virus()

    # Check if boss is defeated (only relevant if boss_active)
    if boss_active and not any(v[5] == "boss" for v in viruses):
        # Boss defeated, allow level up in check_level_progress
        boss_active = False
        boss_spawned_this_level = False

    # Spawn powerups rarely - decreased from 0.01 (1%) to 0.003 (0.3%)
    if random.random() < 0.003:  # 0.3% chance each frame
        spawn_powerup()
    
    # Spawn oxygen collectibles - decreased from 0.02 (2%) to 0.015 (1.5%)
    if random.random() < 0.015:  # 1.5% chance each frame, reduced from 2%
        spawn_oxygen()

def restart_game():
    """Reset the game to initial state."""
    global game_state, player_health, score, level
    global player_pos, player_velocity, viruses, bullets
    global powerups, oxygen_collectibles, active_powerups
    global level_start_time, game_start_time, boss_active, boss_spawned_this_level, cheat_mode, final_play_time
    global base_player_speed, base_virus_spawn_rate, game_paused, game_speed_factor
    
    # Reset game state
    game_state = "PLAYING"
    player_health = 100
    score = 0
    level = 1
    level_start_time = time.time()
    game_start_time = time.time()  # Reset game start time
    boss_active = False
    boss_spawned_this_level = False
    cheat_mode = False
    final_play_time = 0
    base_player_speed = 0.1  # Updated from 0.08 to 0.1
    base_virus_spawn_rate = 0.001  # Reset to starting spawn rate
    game_paused = False  # Ensure game is not paused when restarting
    game_speed_factor = 0.75  # Updated from 0.7 to 0.75 (50% faster than 0.5)
    
    # Reset player position
    player_pos = [0, 0, -100]
    player_velocity = [0, 0, -0.5]
    
    # Clear game objects
    viruses = []
    bullets = []
    powerups = []
    oxygen_collectibles = []
    boss_bullets = []  # Also clear boss bullets
    
    # Reset powerups
    for p_type in active_powerups:
        active_powerups[p_type]["active"] = False
        active_powerups[p_type]["end_time"] = 0

def draw_boss_bullets():
    """Draw all active boss bullets."""
    for bullet in boss_bullets:
        x, y, z, direction = bullet
        
        # Skip drawing if bullet is outside of visible tunnel length
        if z > player_pos[2] + 100 or z < player_pos[2] - (TUNNEL_SEGMENT_LENGTH * TUNNEL_SEGMENTS):
            continue
            
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Use boss virus colors (purple-blue) for boss bullets
        glColor3f(0.5, 0.2, 0.8)  # Match boss color
        
        # Draw the main bullet
        sphere = gluNewQuadric()
        gluSphere(sphere, 1.5, 10, 10)
        gluDeleteQuadric(sphere)
        
        # Add trailing effect for boss bullets
        glColor3f(0.4, 0.1, 0.6)  # Darker purple for trail
        
        # Draw 3 smaller spheres behind the bullet for trail effect
        for i in range(1, 4):
            trail_x = x - direction[0] * i * 0.8
            trail_y = y - direction[1] * i * 0.8
            trail_z = z - direction[2] * i * 0.8
            
            glPushMatrix()
            glTranslatef(trail_x - x, trail_y - y, trail_z - z)  # Relative position
            sphere = gluNewQuadric()
            gluSphere(sphere, 1.5 * (1.0 - i * 0.2), 8, 8)  # Each trail sphere gets smaller
            gluDeleteQuadric(sphere)
            glPopMatrix()
        
        glPopMatrix()

def draw_virus_kill_tint():
    global virus_kill_tint_timer
    if virus_kill_tint_timer > 0:
        alpha = min(virus_kill_tint_timer / 0.3, 1.0) * 0.4  # Fade out
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 0.0, 0.0, alpha)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(1000, 0)
        glVertex2f(1000, 800)
        glVertex2f(0, 800)
        glEnd()
        glDisable(GL_BLEND)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

def draw_shapes():
    """Draw all game objects."""
    # Draw tunnel and environment
    draw_tunnel()
    draw_blood_cells()
    # Draw game objects
    draw_viruses()
    draw_bullets()
    draw_powerups()
    draw_oxygen_collectibles()
    draw_boss_bullets()
    # Draw player last so it's on top of everything (but not in FPP)
    if not fpp_view:
        draw_player()
    # Draw HUD and effects
    draw_hud()
    draw_damage_tint()
    draw_virus_kill_tint()

def keyboardListener(key, x, y):
    """Handle keyboard input."""
    global move_left, move_right, move_up, move_down, cheat_mode, game_state, fpp_view, game_paused
    
    key = key.decode('utf-8') if isinstance(key, bytes) else key
    
    if key == 'a' or key == 'A':
        move_left = True
    elif key == 'd' or key == 'D':
        move_right = True
    elif key == 'w' or key == 'W':
        move_up = True
    elif key == 's' or key == 'S':
        move_down = True
    elif key == ' ':  # Spacebar
        fire_bullet()
    elif key == 'c' or key == 'C':  # Toggle cheat mode
        cheat_mode = not cheat_mode
        if cheat_mode:
            print("Cheat Mode: ON - Increased damage, invincibility, and speed!")
        else:
            print("Cheat Mode: OFF")
    elif key == 'v' or key == 'V':  # Toggle FPP view
        fpp_view = not fpp_view
        if fpp_view:
            print("First-person view activated!")
        else:
            print("Third-person view activated!")
    elif key == 'p' or key == 'P':  # Toggle pause
        if game_state == "PLAYING":  # Only allow pause during active gameplay
            game_paused = not game_paused
            if game_paused:
                print("Game Paused")
            else:
                print("Game Resumed")
    elif key == 'r' or key == 'R':  # Restart game
        if game_state == "GAME_OVER":
            restart_game()
    elif key == 'q' or key == 'Q' or key == chr(27):  # Quit (ESC or Q)
        sys.exit(0)

def keyboardUpListener(key, x, y):
    """Handle keyboard key release."""
    global move_left, move_right, move_up, move_down
    
    key = key.decode('utf-8') if isinstance(key, bytes) else key
    
    if key == 'a' or key == 'A':
        move_left = False
    elif key == 'd' or key == 'D':
        move_right = False
    elif key == 'w' or key == 'W':
        move_up = False
    elif key == 's' or key == 'S':
        move_down = False

def specialKeyListener(key, x, y):
    """Handle special keyboard input."""
    global move_left, move_right, move_up, move_down
    if key == GLUT_KEY_LEFT:
        move_left = True
    elif key == GLUT_KEY_RIGHT:
        move_right = True
    elif key == GLUT_KEY_UP:
        move_up = True
    elif key == GLUT_KEY_DOWN:
        move_down = True

def specialKeyUpListener(key, x, y):
    """Handle special keyboard key release."""
    global move_left, move_right, move_up, move_down
    if key == GLUT_KEY_LEFT:
        move_left = False
    elif key == GLUT_KEY_RIGHT:
        move_right = False
    elif key == GLUT_KEY_UP:
        move_up = False
    elif key == GLUT_KEY_DOWN:
        move_down = False

def mouseListener(button, state, x, y):
    """Handle mouse input."""
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet()

def update_game():
    """Update game state based on time and player actions."""
    global virus_kill_tint_timer
    
    # Skip updates if game is paused
    if game_paused:
        return
        
    if game_state == "PLAYING":
        update_player()
        update_viruses()
        update_bullets()
        update_powerups()
        update_oxygen()
        update_boss_bullets()
        if boss_active:
            boss_attack()
        check_level_progress()
        spawn_game_objects()
        # Decrease virus kill tint timer
        if virus_kill_tint_timer > 0:
            virus_kill_tint_timer -= 1.0 / 60.0  # Assuming ~60 FPS
        if virus_kill_tint_timer < 0:
            virus_kill_tint_timer = 0

def setupCamera():
    """Set up the camera view."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if fpp_view:
        # First-person: camera further in front of player, looking forward
        cam_x = player_pos[0]
        cam_y = player_pos[1]
        cam_z = player_pos[2] - 8  # Move camera 8 units in front of player
        look_x = player_pos[0]
        look_y = player_pos[1]
        look_z = player_pos[2] - 50
        gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 1, 0)
    else:
        # Third-person: camera behind and above player
        camera_pos[0] = player_pos[0] + camera_offset[0]
        camera_pos[1] = player_pos[1] + camera_offset[1]
        camera_pos[2] = player_pos[2] + camera_offset[2]
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  player_pos[0], player_pos[1], player_pos[2] - 50,
                  0, 1, 0)

def idle():
    """Update game state when idle."""
    update_game()
    glutPostRedisplay()

def showScreen():
    """Render the game screen."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    if game_state == "PLAYING":
        setupCamera()
        draw_shapes()
        if game_paused:
            draw_pause_screen()
    elif game_state == "GAME_OVER":
        setupCamera()
        # Only draw tunnel and blood cells as background
        draw_tunnel()
        draw_blood_cells()
        # Draw game over screen on top
        draw_game_over_screen()

    glutSwapBuffers()

def init_lighting():
    """Set up basic lighting for the tunnel."""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    # Position light at camera to always illuminate forward
    glLightfv(GL_LIGHT0, GL_POSITION, [camera_pos[0], camera_pos[1], camera_pos[2], 1])
    
    # Light properties
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    
    # Enable materials
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)

def boss_attack():
    """Boss shoots bullets at the player with various patterns based on level."""
    global boss_shoot_timer, boss_bullets
    
    # Find all bosses
    bosses = [v for v in viruses if v[5] == "boss"]
    if not bosses:
        return
        
    current_time = time.time()
    
    # Faster shooting rate based on level - more challenging
    shoot_interval = max(0.8, 1.5 - (level * 0.15))  # Starts at 1.5s, decreases by 0.15s per level (min 0.8s)
    
    if current_time - boss_shoot_timer > shoot_interval:
        boss_shoot_timer = current_time
        
        # Each boss gets a chance to attack
        for boss in bosses:
            bx, by, bz, size, health, v_type = boss
            
            # Attack pattern based on level
            if level >= 4:
                # Level 4+: Spread shot (5 bullets in a fan pattern)
                spread_count = 5
                spread_angle = 30  # 30 degrees total spread
                
                for i in range(spread_count):
                    # Calculate spread direction
                    angle_offset = (i / (spread_count - 1) - 0.5) * spread_angle
                    
                    # Direction to player with prediction
                    predicted_x = player_pos[0] + (move_right - move_left) * 10
                    predicted_y = player_pos[1] + (move_up - move_down) * 10
                    predicted_z = player_pos[2]
                    
                    dx = predicted_x - bx
                    dy = predicted_y - by
                    dz = predicted_z - bz
                    
                    # Apply angle offset to direction (rotate around Y axis)
                    angle_rad = math.radians(angle_offset)
                    dx_new = dx * math.cos(angle_rad) - dz * math.sin(angle_rad)
                    dz_new = dx * math.sin(angle_rad) + dz * math.cos(angle_rad)
                    dx = dx_new
                    dz = dz_new
                    
                    # Normalize
                    length = math.sqrt(dx**2 + dy**2 + dz**2)
                    if length > 0:
                        direction = [dx/length, dy/length, dz/length]
                    else:
                        direction = [0, 0, 1]
                        
                    boss_bullets.append([bx, by, bz, direction])
                    
            elif level >= 2:
                # Level 2-3: Triple shot
                # Main bullet aimed at player
                predicted_x = player_pos[0] + (move_right - move_left) * 10
                predicted_y = player_pos[1] + (move_up - move_down) * 10
                predicted_z = player_pos[2]
                
                dx = predicted_x - bx
                dy = predicted_y - by
                dz = predicted_z - bz
                
                length = math.sqrt(dx**2 + dy**2 + dz**2)
                if length > 0:
                    direction = [dx/length, dy/length, dz/length]
                else:
                    direction = [0, 0, 1]
                    
                # Main bullet
                boss_bullets.append([bx, by, bz, direction])
                
                # Two side bullets with slight spread
                for angle_offset in [-15, 15]:  # 15 degrees left and right
                    angle_rad = math.radians(angle_offset)
                    dx_new = dx * math.cos(angle_rad) - dz * math.sin(angle_rad)
                    dz_new = dx * math.sin(angle_rad) + dz * math.cos(angle_rad)
                    
                    # Normalize
                    length = math.sqrt(dx_new**2 + dy**2 + dz_new**2)
                    if length > 0:
                        side_direction = [dx_new/length, dy/length, dz_new/length]
                    else:
                        side_direction = [0, 0, 1]
                        
                    boss_bullets.append([bx, by, bz, side_direction])
            else:
                # Level 1: Single shot (original behavior)
                # Direction from boss to player with slight prediction of player movement
                predicted_x = player_pos[0] + (move_right - move_left) * 10
                predicted_y = player_pos[1] + (move_up - move_down) * 10
                predicted_z = player_pos[2]
                
                dx = predicted_x - bx
                dy = predicted_y - by
                dz = predicted_z - bz
                
                length = math.sqrt(dx**2 + dy**2 + dz**2)
                if length == 0:
                    direction = [0, 0, 1]
                else:
                    direction = [dx/length, dy/length, dz/length]
                    
                boss_bullets.append([bx, by, bz, direction])

def update_boss_bullets():
    """Update boss bullet positions and check for collisions with player."""
    global boss_bullets, player_health
    bullets_to_remove = []
    
    # Boss bullet speed increases with level
    bullet_speed = 0.6 + (level * 0.1)  # Starts at 0.6, increases by 0.1 per level
    
    for i, bullet in enumerate(boss_bullets):
        x, y, z, direction = bullet
        # Move bullet toward player with increased speed
        bullet[0] += direction[0] * bullet_speed
        bullet[1] += direction[1] * bullet_speed
        bullet[2] += direction[2] * bullet_speed
        
        # Keep bullets within tunnel boundaries
        distance_from_center = math.sqrt(bullet[0]**2 + bullet[1]**2)
        max_distance = TUNNEL_RADIUS * 0.85  # Keep bullets well inside tunnel
        
        if distance_from_center > max_distance:
            # Scale the position to keep the bullet inside the tunnel
            scale_factor = max_distance / distance_from_center
            bullet[0] *= scale_factor
            bullet[1] *= scale_factor
        
        # Check for collision with player
        distance = math.sqrt((player_pos[0] - bullet[0])**2 + (player_pos[1] - bullet[1])**2 + (player_pos[2] - bullet[2])**2)
        if distance < 6:  # Player radius (5) + bullet radius (1)
            if not cheat_mode and not active_powerups.get("invincibility", {}).get("active", False):
                # Increase boss bullet damage based on level
                damage = 15 + (level * 3)  # Starts at 15, increases by 3 per level
                player_health -= damage
            bullets_to_remove.append(i)
        
        # Remove bullets that are far behind the player
        if bullet[2] > player_pos[2] + 100:
            bullets_to_remove.append(i)
    
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(boss_bullets):
            boss_bullets.pop(i)

def draw_pause_screen():
    """Draw the pause screen overlay."""
    # Switch to 2D mode for overlay
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Disable depth test and lighting for overlay/text
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    # Draw semi-transparent black overlay
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.5)  # Black with 50% opacity
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    glDisable(GL_BLEND)

    # Pause text
    glColor3f(1.0, 1.0, 1.0)
    draw_text(500, 500, "GAME PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
    
    # Instructions
    glColor3f(0.8, 0.8, 0.8)
    draw_text(500, 450, "Press 'P' to resume")
    
    # Controls reminder
    draw_text(500, 350, "Controls:", GLUT_BITMAP_HELVETICA_18)
    draw_text(500, 320, "WASD or Arrow Keys - Move")
    draw_text(500, 290, "Space or Left Mouse - Shoot")
    draw_text(500, 260, "V - Toggle First/Third Person View")

    # Restore OpenGL state
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def main():
    """Initialize and start the game."""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Nanobot Bloodstream Game")
    
    # Enable depth testing for 3D rendering
    glEnable(GL_DEPTH_TEST)
    
    # Enable lighting
    init_lighting()
    
    # Set clear color to dark red (bloodstream background)
    glClearColor(0.1, 0.0, 0.0, 1.0)
    
    # Register callbacks
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(specialKeyUpListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    # Start the game
    restart_game()
    
    # Start the main loop
    glutMainLoop()

if __name__ == "__main__":
    main()
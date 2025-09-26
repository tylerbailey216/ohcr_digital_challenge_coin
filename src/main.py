"""
Digital Challenge Coin App - Interactive 3D Coin
Photorealistic metal, holographic gloss, touch/trackpad controls only
"""
import sys
import os
import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image

# Constants
COIN_RADIUS = 90  # Shrink face radius to remove white edge
COIN_THICKNESS = 10
FPS = 60

FRONT_IMAGE = os.path.join(os.path.dirname(__file__), '../darkcoin4.png')
BACK_IMAGE = os.path.join(os.path.dirname(__file__), '../ohcrlogoGREENBACK.png')

class Coin3D:
    def __init__(self):
        self.angle_x = 0
        self.angle_y = 0
        self.flipped = False
        self.last_pos = None
        self.front_texture = self.load_texture(FRONT_IMAGE)
        self.back_texture = self.load_texture(BACK_IMAGE)
        self.flip_anim = 0
        self.flip_target = 0
        # Load signature image for overlay
        self.signature_img = None
        self.signature_surface = None
        self.load_signature()
        # Load watermark image for overlay
        self.watermark_surface = None
        self.load_watermark()

    def load_watermark(self):
        wm_path = os.path.join(os.path.dirname(__file__), '../gbailey_watermark.png')
        try:
            img = pygame.image.load(wm_path).convert_alpha()
            # Enlarge watermark to match coin diameter (COIN_RADIUS*2)
            img = pygame.transform.smoothscale(img, (COIN_RADIUS*2, COIN_RADIUS*2//3))
            self.watermark_surface = img
        except Exception as e:
            print(f"Warning: Could not load watermark image: {e}")
            self.watermark_surface = None

    def load_signature(self):
        sig_path = os.path.join(os.path.dirname(__file__), '../gbaileysignature.png')
        try:
            img = pygame.image.load(sig_path).convert_alpha()
            # Scale to fit bottom of window
            img = pygame.transform.smoothscale(img, (220, 48))
            self.signature_surface = img
        except Exception as e:
            print(f"Warning: Could not load signature image: {e}")
            self.signature_surface = None

    def load_texture(self, image_path):
        try:
            img = Image.open(image_path).convert('RGBA')
            img_data = img.tobytes()
            width, height = img.size
        except Exception as e:
            print(f"Warning: Could not load image '{image_path}': {e}")
            # Create a fallback solid color image
            width, height = 256, 256
            img = Image.new('RGBA', (width, height), (60, 180, 60, 255))
            img_data = img.tobytes()
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return tex_id

    def update(self):
        # Endless moderate-speed rotation
        self.angle_y += 0.8  # Adjust for desired speed
        if self.angle_y > 360:
            self.angle_y -= 360
        if self.flip_anim < self.flip_target:
            self.flip_anim += min(12, self.flip_target - self.flip_anim)
        elif self.flip_anim > self.flip_target:
            self.flip_anim -= min(12, self.flip_anim - self.flip_target)

    def draw(self):
        glPushMatrix()
        glRotatef(self.angle_x, 1, 0, 0)
        glRotatef(self.angle_y, 0, 1, 0)
        if self.flip_anim > 0:
            glRotatef(self.flip_anim, 0, 1, 0)
        self.draw_coin()
        glPopMatrix()

    def draw_coin(self):
        # Draw edge with metallic specular highlights
        glEnable(GL_LIGHTING)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.9, 0.9, 1.0, 1.0])
        glMaterialfv(GL_FRONT, GL_SHININESS, 128)
        glColor3f(0.85, 0.85, 0.95)
        self.draw_edge()
        glDisable(GL_LIGHTING)

        # Draw faces with holographic/metallic overlay
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.front_texture if not self.flipped else self.back_texture)
        self.draw_face(True)
        glBindTexture(GL_TEXTURE_2D, self.back_texture if not self.flipped else self.front_texture)
        self.draw_face(False)
        glDisable(GL_TEXTURE_2D)

        # Holographic shine overlay (animated gradient)
        self.draw_holo_shine()

    def draw_holo_shine(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_LIGHTING)
        for face in [True, False]:
            glBegin(GL_TRIANGLE_FAN)
            glColor4f(1.0, 1.0, 1.0, 0.10)
            glVertex3f(0, 0, COIN_THICKNESS/2 if face else -COIN_THICKNESS/2)
            for i in range(0, 361, 5):
                theta = math.radians(i)
                x = COIN_RADIUS * math.cos(theta)
                y = COIN_RADIUS * math.sin(theta)
                holo = 0.5 + 0.5 * math.sin(self.angle_x/25 + theta*3 + self.angle_y/25)
                r = 0.85 + 0.15 * holo
                g = 0.85 + 0.15 * (1-holo)
                b = 1.0
                alpha = 0.08 + 0.07 * abs(math.cos(theta + self.angle_y/40))
                glColor4f(r, g, b, alpha)
                glVertex3f(x, y, COIN_THICKNESS/2 if face else -COIN_THICKNESS/2)
            glEnd()
        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND)

    def draw_edge(self):
        # Chrome/metallic polished gradient edge
        glBegin(GL_QUAD_STRIP)
        for i in range(0, 361, 5):
            theta = math.radians(i)
            x = COIN_RADIUS * math.cos(theta)
            y = COIN_RADIUS * math.sin(theta)
            # Chrome base: cool steel, high contrast
            base = 0.7 + 0.25 * math.sin(theta + self.angle_y/10)
            # Specular highlight band (moving)
            spec = pow(abs(math.cos(theta - self.angle_y * math.pi / 180)), 32)
            # Subtle blue/gold color shift
            blue = 0.08 * math.sin(theta*2 + self.angle_x/12)
            gold = 0.06 * math.cos(theta*3 + self.angle_y/15)
            r = min(max(0.85 * base + 1.1 * spec + gold, 0.10), 1.0)
            g = min(max(0.88 * base + 1.0 * spec + gold*0.8, 0.10), 1.0)
            b = min(max(0.95 * base + 1.2 * spec + blue, 0.12), 1.0)
            glColor3f(r, g, b)
            glVertex3f(x, y, -COIN_THICKNESS/2)
            # Much darker for the back edge, with color shift
            glColor3f(r*0.25+0.1, g*0.25+0.1, b*0.25+0.1)
            glVertex3f(x, y, COIN_THICKNESS/2)
        glEnd()

    def draw_face(self, front=True):
        glBegin(GL_TRIANGLE_FAN)
        glColor3f(1.15, 1.15, 1.12)
        glTexCoord2f(0.5, 0.5)
        glVertex3f(0, 0, COIN_THICKNESS/2 if front else -COIN_THICKNESS/2)
        for i in range(0, 361, 5):
            theta = math.radians(i)
            outer_r = COIN_RADIUS * (1 + 0.04 * abs(math.cos(theta)))
            x = outer_r * math.cos(theta)
            y = outer_r * math.sin(theta)
            rim = 0.55 + 0.35 * ((math.sin(theta*2 + self.angle_y/8) + math.cos(theta*3 + self.angle_x/12)) * 0.5 + 0.5)
            shadow = 0.03 + 0.07 * abs(math.sin(theta + self.angle_x/20))
            bevel_color = (rim-shadow, rim-shadow, rim-shadow)
            glColor3f(*bevel_color)
            if front:
                glTexCoord2f(0.5 + 0.5 * math.cos(theta), 0.5 - 0.5 * math.sin(theta))
            else:
                glTexCoord2f(0.5 - 0.5 * math.cos(theta), 0.5 - 0.5 * math.sin(theta))
            glVertex3f(x, y, COIN_THICKNESS/2 if front else -COIN_THICKNESS/2)
        glEnd()

    def handle_gesture(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.last_pos = event.pos
            elif event.button == 3:
                self.flip_target += 180
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            dx, dy = event.rel
            self.angle_y += dx * 0.5
            self.angle_x += dy * 0.5
        elif event.type == pygame.FINGERDOWN:
            if event.touch_id == 2:
                self.flip_target += 180
        elif event.type == pygame.FINGERMOTION:
            self.angle_y += event.dx * 180
            self.angle_x += event.dy * 180

def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((600, 600), DOUBLEBUF | OPENGL)
    pygame.display.set_caption('Digital Challenge Coin')
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 1, 0.1, 1000)
    glMatrixMode(GL_MODELVIEW)
    glTranslatef(0, 0, -350)
    clock = pygame.time.Clock()
    coin = Coin3D()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.FINGERDOWN, pygame.FINGERMOTION):
                coin.handle_gesture(event)
        glClearColor(0.1, 0.1, 0.15, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLightfv(GL_LIGHT0, GL_POSITION, [math.sin(coin.angle_y/60)*300, math.cos(coin.angle_x/60)*300, 300, 1])
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        coin.update()
        coin.draw()
        glDisable(GL_LIGHTING)

        # Draw enlarged watermark image at coin position
        if coin.watermark_surface:
            wm_rect = coin.watermark_surface.get_rect()
            wm_rect.centerx = 300
            wm_rect.centery = 300  # Centered on coin
            pygame.display.get_surface().blit(coin.watermark_surface, wm_rect)

        # Draw signature image below the coin, above the bottom edge
        if coin.signature_surface:
            surface = pygame.display.get_surface()
            sig_rect = coin.signature_surface.get_rect()
            # Place signature about 60px above the bottom, centered horizontally
            sig_rect.centerx = 300
            sig_rect.y = 520  # Adjust as needed for your layout
            # Draw a semi-transparent black background for visibility
            bg = pygame.Surface((sig_rect.width+16, sig_rect.height+8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            surface.blit(bg, (sig_rect.x-8, sig_rect.y-4))
            surface.blit(coin.signature_surface, sig_rect)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == '__main__':
    main()

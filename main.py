import time
import sys
import pygame as pg
import random
from button import Button
from pygame.locals import *
from pygame.sprite import Sprite
from vector import Vector

#Original source code: https://github.com/yashabnarang/pacman-portal-pygame
# -------------------------------------------------------------------------------------
#Class that creates pepples around the maze, they will disappear as pacman 'eats' them once
class Circle(Sprite):

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.screen = self.game.surface

        self.image = pg.image.load('images/circle.png')
        self.rect = self.image.get_rect()

        self.rect.left = self.rect.width
        self.rect.top = self.rect.height
        self.x = float(self.rect.x)

    def width(self): return self.rect.width

    def height(self): return self.rect.height

    def check_edges(self):
        r = self.rect
        s_r = self.screen.get_rect()
        return r.right >= s_r.right or r.left <= 0

    def draw(self): self.screen.blit(self.image, self.rect)

    def update(self):
        self.draw()

# -------------------------------------------------------------------------------------
class Grid:

    def __init__(self, game):
        self.dir = 0
        self.circles = pg.sprite.Group()
        self.powerCircles = pg.sprite.Group()
        self.screen = game.surface
        self.game = game

    def create_circle(self, n, row):
        circle = Circle(game=self.game)
        r = circle.rect
        w, h = r.size
        circle.x = w + 2 * n * (w / 4)
        r.x = circle.x
        r.y = r.height + 2 * (h / 4) * row
        self.circles.add(circle)

    #Creating the 4 bigger circles in the 4 corners of the maze
    #as pac-man consumes this circles, ghosts will turn to scary mode and run away from him
    def create_powerCircle(self, n, row):
        superCircle = Circle(game=self.game)
        superCircle.image = pg.image.load('images/largeCircle.png')
        r = superCircle.rect
        w, h = r.size
        superCircle.x = w + 2 * n * (w / 4)
        r.x = superCircle.x
        r.y = r.height + 2 * (h / 4) * row
        self.powerCircles.add(superCircle)

    def check_hit(self):
        for i in range(len(self.game.bricks)):
            pg.sprite.spritecollide(self.game.bricks[i], self.circles, True)
        if pg.sprite.spritecollide(self.game.player, self.circles, True):
            if self.game.mainClock.get_time() % 2 == 0:
                self.game.audio.play_sound(0)
            self.game.score += 10
        if pg.sprite.spritecollide(self.game.player, self.powerCircles, True):
            #when pacman eats the larger circles, set scaredmode to 1
            self.game.scaredmode = 1
            self.game.blinky.startF, self.game.blinky.endF = 0, 1
            self.game.pinky.startF, self.game.pinky.endF = 0, 1
            self.game.inky.startF, self.game.inky.endF = 0, 1
            self.game.clyde.startF, self.game.clyde.endF = 0, 1
            self.game.blinky.currentFrame, self.game.pinky.currentFrame, self.game.inky.currentFrame,
            self.game.clyde.currentFrame = 0, 0, 0, 0
            self.game.score += 50
        if len(self.circles) == 0:
            self.game.level += 1
            Enemy.SPEED += 1
            self.reset_grid()

    def reset_grid(self):
        for row in range(14, 121, 3):
            for col in range(6, 50 * 2, 3):
                self.create_circle(n=col, row=row)
        self.create_powerCircle(n=5, row=19)
        self.create_powerCircle(n=98, row=19)
        self.create_powerCircle(n=5, row=94)
        self.create_powerCircle(n=98, row=94)

    def update(self):
        self.check_hit()
        self.circles.update()
        self.powerCircles.update()


# -------------------------------------------------------------------------------------
class Player:
    SPEED = 6

    def __init__(self, rect, speed=Vector()):
        self.pacAnimation = ['images/pacman0.png', 'images/pacman1.png', 'images/pacman2.png']
        self.currentFrame, self.currentAngle, self.animationDirection = 0, 0, 0
        self.rect = rect
        self.speed = speed
        self.player = pg.Rect(300, 100, 25, 25)
        self.lives = 3
        self.death = 0
        self.image = pg.transform.rotozoom(pg.image.load(self.pacAnimation[self.currentFrame]),
                                           self.currentAngle, 0.06)

    def __repr__(self):
        return "Player(rect={},speed={})".format(self.rect, self.speed)

    def pixel_(self):
        if self.speed == Vector():
            return
        if self.animationDirection == 0:
            if self.currentFrame < len(self.pacAnimation) - 1:
                self.currentFrame += 1
            else:
                self.animationDirection = 1
        else:
            if self.currentFrame > 0:
                self.currentFrame -= 1
            else:
                self.animationDirection = 0

    def limit_to_screen(self, game):
        self.rect.top = max(73, min(game.WINDOW_HEIGHT - self.rect.height - 80, self.rect.top))
        if 0 <= self.rect.left > game.WINDOW_HEIGHT:
            self.rect.left = max(-28, min(game.WINDOW_WIDTH - self.rect.width + 48, self.rect.left))
        elif self.rect.left < -30:
            self.rect.left = game.WINDOW_WIDTH
        elif self.rect.left > game.WINDOW_WIDTH:
            self.rect.left = -30

    def move_ip(self, game):
        if self.speed == Vector():
            return
        self.rect.move_ip(self.speed.x, self.speed.y)
        self.limit_to_screen(game)

    def move(self, game):
        if self.speed == Vector():
            return

        tempX = self.speed.x
        tempY = self.speed.y

        if self.death == 0:
            if not self.check_collisions(game):
                self.rect.left += self.speed.x
                self.rect.top += self.speed.y
            if self.check_collisions(game):
                self.rect.left -= self.speed.x
                self.rect.top -= self.speed.y

        if tempX != 0 or tempY != 0:
            self.pixel_()
        if self.speed.x > 0:
            self.currentAngle = 0
        elif self.speed.x < 0:
            self.currentAngle = 180
        elif self.speed.y > 0:
            self.currentAngle = -90
        else:
            self.currentAngle = 90

        self.limit_to_screen(game)

    #check collision against ghost, if pacman collide with ghost, he loses 1 life.
    def check_collisions_ghost(self, game):
        if self.death == 0:
            if self.rect.colliderect(game.blinky.rect) or self.rect.colliderect(game.pinky.rect) or \
                    self.rect.colliderect(game.inky.rect) or self.rect.colliderect(game.clyde.rect):
                if game.scaredmode == 0:
                    self.pacAnimation = ['images/death0.png', 'images/death1.png', 'images/death2.png',
                                         'images/death3.png', 'images/death4.png']
                    self.currentFrame, self.death = 0, 1
                else:
                    game.score += 200
                    if self.rect.colliderect(game.blinky.rect):
                        game.blinky.rect.left = 259
                        game.blinky.rect.top = 250
                    if self.rect.colliderect(game.pinky.rect):
                        game.pinky.rect.left = 259
                        game.pinky.rect.top = 305
                    if self.rect.colliderect(game.inky.rect):
                        game.inky.rect.left = 230
                        game.inky.rect.top = 305
                    if self.rect.colliderect(game.clyde.rect):
                        game.clyde.rect.left = 259
                        game.clyde.rect.top = 305
                    game.scaredmode = 0

        if self.currentFrame == 4:
            pg.mixer.music.load(game.death_src)
            pg.mixer.music.play(1, 0.0)
            # can't move until intro music stops
            while pg.mixer.music.get_busy():
                time.sleep(0.02)

            self.rect.left, self.rect.top = 259, 363
            game.blinky.rect.left, game.blinky.rect.top = 259, 250
            game.pinky.rect.left, game.pinky.rect.top = 259, 305
            game.inky.rect.left, game.inky.rect.top = 230, 305
            game.clyde.rect.left, game.clyde.rect.top = 285, 305
            self.lives -= 1
            if self.lives == 0:
                game.surface.blit(game.gOver0, game.gOver0Rect)
            self.pacAnimation = ['images/pacman0.png', 'images/pacman1.png', 'images/pacman2.png']
            self.currentFrame, self.death, self.speed = 0, 0, Vector()
            game.update()

            if self.lives > 0:
                pg.mixer.music.load(game.intro_src)
                pg.mixer.music.play(1, 0.0)
                # can't move until intro music stops
                while pg.mixer.music.get_busy():
                    time.sleep(0.02)
            time.sleep(0.02)

    def draw(self, game):
        self.image = pg.transform.rotozoom(pg.image.load(self.pacAnimation[self.currentFrame]),
                                           self.currentAngle, 0.06)
        game.surface.blit(self.image, self.rect)

    #check collisions against the walls of the maze
    def check_collisions(self, game):
        for j in range(len(game.walls)):
            if self.rect.colliderect(game.walls[j]):
                return True
        return False

    def update(self, game):
        self.check_collisions_ghost(game=game)
        self.check_collisions(game=game)
        self.move(game=game)
        self.draw(game=game)


# -------------------------------------------------------------------------------------
class Enemy:
    SPEED = 6

    def __init__(self, rect, speed=Vector()):
        self.enemyAnimation = ['images/blinky0.png', 'images/blinky1.png', 'images/blinky2.png', 'images/blinky3.png',
                               'images/blinky4.png', 'images/blinky5.png', 'images/blinky6.png', 'images/blinky7.png',
                               'images/run0.png', 'images/run1.png']
        self.currentFrame, self.animationDirection = 0, 0
        self.startF, self.endF = 0, 1  # len(self.enemyAnimation) - 1
        self.rect = rect
        self.speed = speed
        self.enemy = pg.Rect(300, 100, 50, 50)
        self.image = pg.transform.rotozoom(pg.image.load(self.enemyAnimation[self.currentFrame]), 0, 0.06)

    def __repr__(self):
        return "Enemy(rect={},speed={})".format(self.rect, self.speed)

    def pixel_(self):
        if self.speed == Vector():
            return
        if self.startF <= self.currentFrame < self.endF:
            self.currentFrame += 1
        else:
            self.currentFrame = self.startF

    def change_menu_frame(self):
        if self.startF <= self.currentFrame < self.endF:
            self.currentFrame += 1
        else:
            self.currentFrame = self.startF

    def limit_to_screen(self, game):
        self.rect.top = max(73, min(game.WINDOW_HEIGHT - self.rect.height - 55, self.rect.top))
        if game.m == 0:
            self.rect.left = max(-28, min(game.WINDOW_WIDTH - self.rect.width + 48, self.rect.left))
        else:
            self.rect.left = max(-300, min(game.WINDOW_WIDTH - self.rect.width + 48, self.rect.left))

    def move(self, game):
        if self.speed == Vector():
            return
        if game.m == 1:
            self.rect.left += self.speed.x
            self.rect.top += self.speed.y
            tempX = self.speed.x
            tempY = self.speed.y
            if tempX != 0 or tempY != 0:
                self.pixel_()
        else:
            self.pixel_()
            if not self.check_collisions(game):
                self.rect.left += self.speed.x
                self.rect.top += self.speed.y
            if self.check_collisions(game):
                self.rect.left -= self.speed.x
                self.rect.top -= self.speed.y
            if game.scaredmode == 0:
                if self.speed.x > 0:
                    self.startF, self.endF = 2, 3
                elif self.speed.x < 0:
                    self.startF, self.endF = 0, 1
                elif self.speed.y > 0:
                    self.startF, self.endF = 4, 5
                else:
                    self.startF, self.endF = 6, 7
            else:
                self.startF, self.endF = 8, 9
        self.limit_to_screen(game)

        for j in range(len(game.gWalls)):
            if self.rect.colliderect(game.gWalls[j]):
                return True
        return False

    def draw(self, game):
        self.image = pg.transform.rotozoom(pg.image.load(self.enemyAnimation[self.currentFrame]), 0, 0.06)
        game.surface.blit(self.image, self.rect)

    def check_collisions(self, game):
        for j in range(len(game.gWalls)):
            if self.rect.colliderect(game.gWalls[j]):
                return True
        return False

    def update(self, game):
        self.check_collisions(game=game)
        self.move(game=game)
        self.draw(game=game)

# -------------------------------------------------------------------------------------
class Audio:  # sound(s) and background music
    def __init__(self, sounds, playing):
        self.sounds = {}
        for sound in sounds:
            for k, v in sound.items():
                self.sounds[k] = pg.mixer.Sound(v)
        self.playing = playing

    def play_sound(self, sound):
        if self.playing and sound in self.sounds.keys():
            self.sounds[sound].play()

    def toggle(self):
        self.playing = not self.playing
        pg.mixer.music.play(-1, 0.0) if self.playing else pg.mixer.music.stop()

    def game_over(self, game):
        pg.playing = False
        pg.mixer.music.stop()
        self.play_sound(game.GAME_OVER)


# -------------------------------------------------------------------------------------
class Game:
    def __init__(self, title):
        pg.init()
        logo = pg.image.load('images/pacman2.png')
        pg.display.set_icon(logo)
        self.WINDOW_WIDTH, self.WINDOW_HEIGHT = 550, 700
        self.bitFont = pg.font.Font('fonts/font.ttf', 28)

        self.m, self.h, self.scaredmode, self.gameOver = 0, 0, 0, 0
        self.animated = Enemy(pg.Rect(self.WINDOW_WIDTH, 363, 50, 50), Vector())
        self.animated.enemyAnimation = ['images/menu0.png', 'images/menu1.png', 'images/menu2.png', 'images/menu3.png',
                                        'images/menu4.png', 'images/menu5.png', 'images/menu6.png']

        # Pac-Man and Ghosts
        self.player = Player(pg.Rect(259, 363, 25, 25), Vector())
        self.blinky = Enemy(pg.Rect(259, 250, 25, 25), Vector())
        self.pinky = Enemy(pg.Rect(259, 305, 25, 25), Vector())
        self.inky = Enemy(pg.Rect(230, 305, 25, 25), Vector())
        self.clyde = Enemy(pg.Rect(285, 305, 25, 25), Vector())
        self.bCount, self.iCount, self.pCount, self.cCount = 0, 0, 0, 0
        self.pinky.enemyAnimation = ['images/pinky0.png', 'images/pinky1.png', 'images/pinky2.png', 'images/pinky3.png',
                                     'images/pinky4.png', 'images/pinky5.png', 'images/pinky6.png', 'images/pinky7.png',
                                     'images/run0.png', 'images/run1.png']
        self.inky.enemyAnimation = ['images/inky0.png', 'images/inky1.png', 'images/inky2.png', 'images/inky3.png',
                                    'images/inky4.png', 'images/inky5.png', 'images/inky6.png', 'images/inky7.png',
                                    'images/run0.png', 'images/run1.png']
        self.clyde.enemyAnimation = ['images/clyde0.png', 'images/clyde1.png', 'images/clyde2.png', 'images/clyde3.png',
                                     'images/clyde4.png', 'images/clyde5.png', 'images/clyde6.png', 'images/clyde7.png',
                                     'images/run0.png', 'images/run1.png']

        # Loading Audio from file sounds
        self.intro_src = 'sounds/bg_music.mp3'
        self.death_src = 'sounds/gameOver.ogg'

        self.EAT_SOUND, self.GHOST, self.GAME_OVER = 0, 1, 2
        sounds = [{self.EAT_SOUND: 'sounds/eat.ogg',
                   self.GHOST: 'sounds/ghost.ogg',
                   self.GAME_OVER: 'sounds/gameOver.ogg'}]
        self.audio = Audio(sounds=sounds, playing=True)

        # Creating Bricks in the Maze
        brick1 = Player(pg.Rect(0, 40, 29, 260))
        brick2 = Player(pg.Rect(0, 341, 29, 319))
        brick3 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 40, 29, 260))
        brick4 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 341, 29, 319))
        brick5 = Player(pg.Rect(58, 100, 60, 40))
        brick6 = Player(pg.Rect(140, 100, 100, 40))
        brick7 = Player(pg.Rect(self.WINDOW_WIDTH - 240, 100, 100, 40))
        brick8 = Player(pg.Rect(self.WINDOW_WIDTH - 118, 100, 60, 40))
        brick9 = Player(pg.Rect(58, 155, 60, 40))
        brick10 = Player(pg.Rect(self.WINDOW_WIDTH - 118, 155, 60, 40))
        brick11 = Player(pg.Rect(58, self.WINDOW_HEIGHT - 140, 180, 40))
        brick12 = Player(pg.Rect(self.WINDOW_WIDTH - 240, self.WINDOW_HEIGHT - 140, 190, 40))
        brick13 = Player(pg.Rect(140, 155, 40, 160))
        brick14 = Player(pg.Rect(self.WINDOW_WIDTH - 180, 155, 40, 160))
        brick15 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 12, 80, 30, 60))
        brick16 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 70, 155, 140, 40))
        brick17 = Player(pg.Rect(0, 222, 120, 85))
        brick18 = Player(pg.Rect(150, 220, 90, 30))
        brick19 = Player(pg.Rect(270, 200, 20, 50))
        brick20 = Player(pg.Rect(310, 220, 90, 30))
        brick21 = Player(pg.Rect(430, 222, 120, 85))
        brick22 = Player(pg.Rect(200, 280, 150, 85))
        brick23 = Player(pg.Rect(0, 330, 120, 85))
        brick24 = Player(pg.Rect(150, 330, 30, 85))
        brick25 = Player(pg.Rect(370, 330, 40, 85))
        brick26 = Player(pg.Rect(430, 330, 120, 85))
        brick27 = Player(pg.Rect(210, 390, 140, 30))
        brick28 = Player(pg.Rect(60, 440, 60, 40))
        brick29 = Player(pg.Rect(430, 440, 70, 40))
        brick30 = Player(pg.Rect(150, 440, 90, 40))
        brick31 = Player(pg.Rect(315, 445, 90, 40))
        brick32 = Player(pg.Rect(260, 430, 30, 50))
        brick33 = Player(pg.Rect(90, 470, 30, 70))
        brick34 = Player(pg.Rect(430, 470, 40, 70))
        brick35 = Player(pg.Rect(30, 500, 30, 40))
        brick36 = Player(pg.Rect(490, 500, 30, 40))
        brick37 = Player(pg.Rect(140, 500, 40, 50))
        brick38 = Player(pg.Rect(370, 500, 40, 50))
        brick39 = Player(pg.Rect(210, 500, 140, 40))
        brick40 = Player(pg.Rect(260, 530, 30, 70))
        self.bricks = [brick1, brick2, brick3, brick4, brick5, brick6, brick7, brick8, brick9, brick10, brick11,
                       brick12, brick13, brick14, brick15, brick16, brick17, brick18, brick19, brick20, brick21,
                       brick22, brick23, brick24, brick25, brick26, brick27, brick28, brick29, brick30, brick31,
                       brick32, brick33, brick34, brick35, brick36, brick37, brick38, brick39, brick40]

        # Creating Walls in the maze
        wall1 = Player(pg.Rect(-30, 40, 50, 260))
        wall2 = Player(pg.Rect(-30, 341, 50, 319))
        wall3 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 40, 60, 260))
        wall4 = Player(pg.Rect(self.WINDOW_WIDTH - 29, 341, 60, 319))
        wall5 = Player(pg.Rect(58, 100, 50, 25))
        wall6 = Player(pg.Rect(140, 100, 80, 25))
        wall7 = Player(pg.Rect(self.WINDOW_WIDTH - 230, 100, 80, 25))
        wall8 = Player(pg.Rect(self.WINDOW_WIDTH - 110, 100, 40, 25))
        wall9 = Player(pg.Rect(60, 165, 50, 20))
        wall10 = Player(pg.Rect(self.WINDOW_WIDTH - 110, 165, 40, 20))
        wall11 = Player(pg.Rect(60, self.WINDOW_HEIGHT - 130, 165, 25))
        wall12 = Player(pg.Rect(self.WINDOW_WIDTH - 230, self.WINDOW_HEIGHT - 140, 165, 25))
        wall13 = Player(pg.Rect(145, 165, 25, 130))
        wall14 = Player(pg.Rect(self.WINDOW_WIDTH - 170, 165, 20, 130))
        wall15 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 12, 80, 20, 40))
        wall16 = Player(pg.Rect(self.WINDOW_WIDTH / 2 - 70, 165, 130, 20))
        wall17 = Player(pg.Rect(0, 222, 105, 80))
        wall18 = Player(pg.Rect(150, 220, 70, 20))
        wall19 = Player(pg.Rect(270, 200, 10, 40))
        wall20 = Player(pg.Rect(320, 220, 60, 20))
        wall21 = Player(pg.Rect(430, 222, 120, 76))
        wall22 = Player(pg.Rect(200, 280, 140, 75))
        wall23 = Player(pg.Rect(0, 341, 105, 75))
        wall24 = Player(pg.Rect(150, 335, 20, 75))
        wall25 = Player(pg.Rect(380, 335, 20, 75))
        wall26 = Player(pg.Rect(440, 341, 120, 70))
        wall27 = Player(pg.Rect(210, 390, 130, 25))
        wall28 = Player(pg.Rect(60, 450, 50, 25))
        wall29 = Player(pg.Rect(435, 450, 50, 25))
        wall30 = Player(pg.Rect(150, 450, 70, 25))
        wall31 = Player(pg.Rect(315, 450, 70, 25))
        wall32 = Player(pg.Rect(260, 430, 20, 40))
        wall33 = Player(pg.Rect(90, 470, 20, 60))
        wall34 = Player(pg.Rect(435, 470, 20, 60))
        wall35 = Player(pg.Rect(30, 510, 20, 25))
        wall36 = Player(pg.Rect(495, 510, 20, 25))
        wall37 = Player(pg.Rect(150, 510, 15, 50))
        wall38 = Player(pg.Rect(380, 510, 15, 50))
        wall39 = Player(pg.Rect(210, 510, 130, 20))
        wall40 = Player(pg.Rect(260, 530, 20, 50))
        self.walls = [wall1, wall2, wall3, wall4, wall5, wall6, wall7, wall8, wall9, wall10, wall11, wall12, wall13,
                      wall14, wall15, wall16, wall17, wall18, wall19, wall20, wall21,
                      wall22, wall23, wall24, wall25, wall26, wall27, wall28, wall29, wall30, wall31, wall32, wall33,
                      wall34, wall35, wall36, wall37, wall38, wall39, wall40]

        # Static Walls (Ghosts/Walls)
        self.gWalls = self.walls
        self.gWalls[21] = Player(pg.Rect(320, 280, 20, 75))
        self.gWalls.append(Player(pg.Rect(200, 280 + 55, 140, 20)))
        self.gWalls.append(Player(pg.Rect(200, 280, 20, 75)))


        self.score, self.level, self.highestScores = 0, 0, []
        # Fill highestScores with values loaded from saved files
        f = open('highscores.txt', 'r')
        f1 = f.readlines()
        for s in f1:
            self.highestScores.append(int(s))
        f.close()
        self.highestScores.sort(reverse=True)

        self.finished = False
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BACKGROUND_COLOR = self.BLACK
        self.WALL_COLOR = (255, 0, 0)
        self.FPS = 60

        self.gOver0 = self.bitFont.render('Game Over', True, self.WHITE, self.BLACK)
        self.gOver0Rect = self.gOver0.get_rect()
        self.gOver0Rect.center = (275, 325)

        pg.display.set_caption(title)
        self.surface = pg.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), 0, 32)
        self.grid = Grid(self)

        self.bImage = pg.image.load('images/pacGrid.png')
        self.mImage = pg.image.load('images/menu.png')
        self.mainClock = pg.time.Clock()

    @staticmethod
    def check_key_pressed():
        check_key = False
        while not check_key:
            for e in pg.event.get():
                if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
                    Game.terminate()
                elif e.type == KEYDOWN:
                    check_key = True

    def process_event_loop(self, event):
        # speed = Player.SPEED
        e_type = event.type
        movement = {K_a: Vector(-1, 0), K_d: Vector(1, 0), K_w: Vector(0, -1), K_s: Vector(0, 1)}
        translate = {K_LEFT: K_a, K_RIGHT: K_d, K_UP: K_w, K_DOWN: K_s}
        left_right_up_down = (K_LEFT, K_a, K_RIGHT, K_d, K_UP, K_w, K_DOWN, K_s)
        x_z = (K_x, K_z)

        if e_type == KEYDOWN or e_type == KEYUP:
            k = event.key
            if k == K_m and e_type == KEYUP:
                pg.mixer.music.stop()
            elif k in x_z:
                if e_type == KEYDOWN:
                    pass
                elif e_type == KEYUP:
                    pass
            elif k in left_right_up_down:
                if k in translate.keys():
                    k = translate[k]
                self.player.speed = Player.SPEED * movement[k]

        elif e_type == QUIT or (e_type == KEYUP and event.key == K_ESCAPE):
            self.finished = True

    def update(self):
        self.surface.fill(self.BACKGROUND_COLOR)
        self.surface.blit(self.bImage, (0, 46))

        text = self.bitFont.render(f'Score: {self.score}', True, self.WHITE, self.BLACK)
        textRect = text.get_rect()
        textRect.center = (70, 25)
        self.surface.blit(text, textRect)

        text2 = self.bitFont.render(f'Level: {self.level}', True, self.WHITE, self.BLACK)
        textRect2 = text2.get_rect()
        textRect2.center = (500, 25)
        self.surface.blit(text2, textRect2)

        text3 = self.bitFont.render(f'Lives: {self.player.lives}', True, self.WHITE, self.BLACK)
        textRect3 = text3.get_rect()
        textRect3.center = (70, 675)
        self.surface.blit(text3, textRect3)

        self.grid.update()

        self.player.update(game=self)
        if self.player.lives == 0:
            self.gameOver = 1
            self.player.lives = 3
            self.highestScores.append(self.score)

            # update score to the highscore.txt on file, this will always keep scores
            f = open('highscores.txt', 'a')
            f.write(f'\n{self.score}')
            f.close()

            self.highestScores.sort(reverse=True)
            self.score, self.level = 0, 1
            self.grid.reset_grid()
            # Placing the location of pacman and all ghost back to starting position
            self.player.rect.left, self.player.rect.top = 259, 363
            self.blinky.rect.left, self.blinky.rect.top = 259, 250
            self.pinky.rect.left, self.pinky.rect.top = 259, 305
            self.inky.rect.left, self.inky.rect.top = 230, 305
            self.clyde.rect.left, self.clyde.rect.top = 285, 305
            self.surface.fill(self.BACKGROUND_COLOR)
            self.surface.blit(self.bImage, (0, 46))
            self.surface.blit(self.gOver0, self.gOver0Rect)
            self.menu()

        else:

            # Randomizing the movement of the ghosts
            if self.mainClock.get_time() % random.randint(1, 40) == 0:
                self.bCount = random.randint(1, 4)
                if self.bCount == 1:
                    self.blinky.speed = Enemy.SPEED * Vector(1, 0)
                elif self.bCount == 2:
                    self.blinky.speed = Enemy.SPEED * Vector(0, 1)
                elif self.bCount == 3:
                    self.blinky.speed = Enemy.SPEED * Vector(-1, 0)
                else:  # 4
                    self.blinky.speed = Enemy.SPEED * Vector(0, -1)
            self.blinky.update(game=self)
            if self.mainClock.get_time() % random.randint(1, 40) == 0:
                self.pCount = random.randint(1, 4)
                if self.pCount == 1:
                    self.pinky.speed = Enemy.SPEED * Vector(1, 0)
                elif self.pCount == 2:
                    self.pinky.speed = Enemy.SPEED * Vector(0, 1)
                elif self.pCount == 3:
                    self.pinky.speed = Enemy.SPEED * Vector(-1, 0)
                else:  # 4
                    self.pinky.speed = Enemy.SPEED * Vector(0, -1)
            self.pinky.update(game=self)
            if self.mainClock.get_time() % random.randint(1, 40) == 0:
                self.iCount = random.randint(1, 4)
                if self.iCount == 1:
                    self.inky.speed = Enemy.SPEED * Vector(1, 0)
                elif self.iCount == 2:
                    self.inky.speed = Enemy.SPEED * Vector(0, 1)
                elif self.iCount == 3:
                    self.inky.speed = Enemy.SPEED * Vector(-1, 0)
                else:  # 4
                    self.inky.speed = Enemy.SPEED * Vector(0, -1)
            self.inky.update(game=self)
            # Making Clyde move randomly
            # if the current time mod 3,7 == 0 then it will move otherwise it won't
            # assigning random number from 1-4 to cCount
            # left, up, right, down = 1 2 3 4
            if self.mainClock.get_time() % random.randint(1, 40) == 0:
                self.cCount = random.randint(1, 4)
                if self.cCount == 1:
                    self.clyde.speed = Enemy.SPEED * Vector(1, 0)
                elif self.cCount == 2:
                    self.clyde.speed = Enemy.SPEED * Vector(0, 1)
                elif self.cCount == 3:
                    self.clyde.speed = Enemy.SPEED * Vector(-1, 0)
                else:  # 4
                    self.clyde.speed = Enemy.SPEED * Vector(0, -1)
            self.clyde.update(game=self)
            pg.display.update()

    def menu(self):
        self.m = 1  # menu is on
        # loading up background music from here
        if not pg.mixer.music.get_busy():
            pg.mixer.music.load('sounds/Arsenic1987_PacmanRemix.mp3')
            pg.mixer.music.play()
        self.surface.blit(self.mImage, (0, 0))
        self.animated.update(game=self)

        # Make the Play button.
        play_button = Button(self.surface, "Play")
        play_button.rect.top += 200
        play_button.prep_msg("Play")

        # Make the HighScore button.
        highScore_button = Button(self.surface, "Highscores")
        highScore_button.rect.top += 250
        highScore_button.prep_msg("Highscores")

        pg.display.update()
        play_button.draw_button()
        highScore_button.draw_button()

        blink_intro, pink_intro, inky_intro, clyde_intro = (249, 0, 0), (249, 141, 224), (5, 249, 249), (249, 138, 13)
        text0 = self.bitFont.render('Blinky', True, blink_intro, (0, 0, 0))
        text1 = self.bitFont.render('Pinky', True, pink_intro, (0, 0, 0))
        text2 = self.bitFont.render('Inky', True, inky_intro, (0, 0, 0))
        text3 = self.bitFont.render('Clyde', True, clyde_intro, (0, 0, 0))
        text4 = self.bitFont.render('Can you escape from ghosts?', True, (249, 241, 0), (0, 0, 0))
        textRect0, textRect1, textRect2, textRect3, textRect4 \
            = text0.get_rect(), text1.get_rect(), text2.get_rect(), text3.get_rect(), text4.get_rect()
        textRect0.center, textRect1.center, textRect2.center, textRect3.center, textRect4.center \
            = (275, 450), (275, 450), (275, 450), (275, 450), (275, 450)

        # Wait for Keypress To Move To Next State
        check_key = False
        count = 0
        temp = -1
        temp_ = 0

        blinky = self.blinky
        pinky = self.pinky
        inky = self.inky
        clyde = self.clyde

        blinky.rect.left, blinky.rect.top = 260, 410
        pinky.rect.left, pinky.rect.top = 260, 410
        inky.rect.left, inky.rect.top = 260, 410
        clyde.rect.left, clyde.rect.top = 260, 410

        while not check_key:
            temp_ += 1
            if count == 150:
                temp *= -1
                count = 0
            count += 1

            self.animated.speed = Enemy.SPEED * Vector(1 * temp, 0)
            self.surface.blit(self.mImage, (0, 0))
            if temp_ < 300:
                if count < 50 and self.gameOver == 1:
                    self.surface.blit(self.gOver0, self.gOver0Rect)
                elif self.gameOver == 1:
                    self.gameOver = 0
                if self.animated.speed == Enemy.SPEED * Vector(-1, 0):
                    self.animated.rect.left = self.animated.rect.left
                    self.animated.startF, self.animated.endF = 0, 2
                else:
                    self.animated.startF, self.animated.endF = 3, len(self.animated.enemyAnimation) - 1
                    self.surface.blit(text4, textRect4)

                self.animated.update(game=self)

            # Individually Introduce
            if 300 <= temp_ <= 337:
                self.surface.blit(text0, textRect0)
                blinky.change_menu_frame()
                blinky.update(self)
            elif 337 <= temp_ <= 375:
                self.surface.blit(text1, textRect1)
                pinky.change_menu_frame()
                pinky.update(self)
            elif 375 <= temp_ <= 412:
                self.surface.blit(text2, textRect2)
                inky.change_menu_frame()
                inky.update(self)
            elif 412 <= temp_ <= 450:
                self.surface.blit(text3, textRect3)
                clyde.change_menu_frame()
                clyde.update(self)
            elif temp_ >= 450:
                temp_ = 0
                temp *= -1

            play_button.draw_button()
            highScore_button.draw_button()
            pg.display.update()
            for e in pg.event.get():
                if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
                    Game.terminate()
                elif e.type == pg.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pg.mouse.get_pos()
                    play_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)
                    score_clicked = highScore_button.rect.collidepoint(mouse_x, mouse_y)
                    if play_clicked:
                        check_key = True
                    if score_clicked:
                        self.highScores()
                else:
                    mouse_x, mouse_y = pg.mouse.get_pos()
                    play_hover = play_button.rect.collidepoint(mouse_x, mouse_y)
                    score_hover = highScore_button.rect.collidepoint(mouse_x, mouse_y)
                    if play_hover:
                        play_button.text_color = (255, 255, 255)
                        play_button.prep_msg("Play")
                        play_button.draw_button()
                    else:
                        play_button.text_color = play_button.temp_color
                        play_button.prep_msg("Play")
                        play_button.draw_button()
                    if score_hover:
                        highScore_button.text_color = (255, 255, 255)
                        highScore_button.prep_msg("Highscores")
                        highScore_button.draw_button()
                    else:
                        highScore_button.text_color = highScore_button.temp_color
                        highScore_button.prep_msg("Highscores")
                        highScore_button.draw_button()
            time.sleep(0.02)
        self.m = 0  # menu is off
        # reset ghosts
        self.blinky.rect.left, self.blinky.rect.top = 259, 250
        self.pinky.rect.left, self.pinky.rect.top = 259, 305
        self.inky.rect.left, self.inky.rect.top = 230, 305
        self.clyde.rect.left, self.clyde.rect.top = 285, 305
        self.play()

    def highScores(self):
        self.h = 1  # highscores is on
        #the current hisghest score is set to 10000, if there is a higher score, it will automatically be updated

        self.surface.fill(self.BACKGROUND_COLOR)
        text = self.bitFont.render('High Scores:', True, (249, 241, 0), (0, 0, 0))
        text0 = self.bitFont.render(f'#1: {self.highestScores[0]}', True, (249, 0, 0), (0, 0, 0))
        text1 = self.bitFont.render(f'#2: {self.highestScores[1]}', True, (249, 141, 224), (0, 0, 0))
        text2 = self.bitFont.render(f'#3: {self.highestScores[2]}', True, (5, 249, 249), (0, 0, 0))
        text3 = self.bitFont.render(f'#4: {self.highestScores[3]}', True, (249, 138, 13), (0, 0, 0))
        text4 = self.bitFont.render(f'#5: {self.highestScores[4]}', True, (249, 241, 0), (0, 0, 0))
        text5 = self.bitFont.render('BackSpace = Main Menu', True, (255, 255, 255), (0, 0, 0))
        textRect, textRect0, textRect1, textRect2, textRect3, textRect4, textRect5 = \
            text.get_rect(), text0.get_rect(), text1.get_rect(), text2.get_rect(), \
            text3.get_rect(), text4.get_rect(), text5.get_rect()
        textRect.center, textRect0.center, textRect1.center, textRect2.center, textRect3.center, textRect4.center, \
        textRect5.center = (285, 150), (285, 200), (285, 250), (285, 300), (285, 350), (285, 400), (285, 500)

        # Wait for Keypress To Move To Next State
        check_key = False
        while not check_key:
            self.surface.blit(text, textRect)
            self.surface.blit(text0, textRect0)
            self.surface.blit(text1, textRect1)
            self.surface.blit(text2, textRect2)
            self.surface.blit(text3, textRect3)
            self.surface.blit(text4, textRect4)
            self.surface.blit(text5, textRect5)
            pg.display.update()

            for e in pg.event.get():
                if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
                    Game.terminate()
                elif e.type == KEYDOWN and e.key == K_BACKSPACE:
                    check_key = True

        self.h = 0  # highscores is off
        self.menu()

    def play(self):
        pg.mixer.music.load(self.intro_src)
        pg.mixer.music.play(1, 0.0)
        while not self.finished:
            for event in pg.event.get():
                self.process_event_loop(event)

            self.update()
            # can't move until intro music stops
            while pg.mixer.music.get_busy():
                time.sleep(0.02)
            time.sleep(0.02)
            self.mainClock.tick(self.FPS)
        Game.terminate()

    @staticmethod
    def terminate():
        pg.quit()
        sys.exit()


# -------------------------------------------------------------------------------------
def main():
    game = Game(title='Pac-Man')
    game.menu()


# -------------------------------------------------------------------------------------
if __name__ == '__main__':
    main()

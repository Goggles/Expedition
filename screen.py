import libtcodpy as libtcod

#Global, set variables
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45

colour_dark_wall = libtcod.Color(0, 0, 100)
colour_dark_ground = libtcod.Color(50, 50, 150)


#defines the state of a tile - is it able to be walked on and is it sight-blocking?
class Tile:
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked

		if block_sight is None:
			block_sight = blocked
		self.block_sight = block_sight

class Rect:
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h

class Object:
	#A generic object. Anything that has a position on the screen uses this - walls, npcs, the player.
	def __init__(self, x, y, char, colour):
		self.x = x
		self.y = y
		self.char = char
		self.colour = colour

	def move(self, dx, dy):
		if not map[self.x + dx][self.y + dy].blocked:
			self.x += dx
			self.y += dy

	def draw(self):
		#set the character and the colour
		libtcod.console_set_default_foreground(con, self.colour)
		libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

	def clear(self):
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

def make_map():
	global map

	map = [[Tile(False)
		for y in range(MAP_HEIGHT) ]
			for x in range(MAP_WIDTH) ]
	
	map[30][22].blocked = True
	map[30][22].block_sight = True
	map[50][22].blocked = True
	map[50][22].block_sight = True

def render_all():
	global colour_light_wall
	global colour_light_ground

	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			wall = map[x][y].block_sight
			if wall:
				libtcod.console_set_char_background(con, x, y, colour_dark_wall, libtcod.BKGND_SET)
			else:
				libtcod.console_set_char_background(con, x, y, colour_dark_ground, libtcod.BKGND_SET)
	
	for object in objects:
		object.draw()

	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

def handle_keys():
		
	key = libtcod.console_wait_for_keypress(True)
	
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+enter toggles fullscreen mode
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	elif key.vk == libtcod.KEY_ESCAPE:
		return True #exit the game
	#movement keys
	if libtcod.console_is_key_pressed(libtcod.KEY_UP):
		player.move(0, -1)
	elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
		player.move(0, 1)
	elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
		player.move(-1, 0)
	elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
		player.move(1, 0)

#console initialization and main game loop
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Expedition', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

#initialise the on-screen objects
player = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.white)
npc = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.yellow)
objects = [npc, player]

#initialise the map
make_map()

while not libtcod.console_is_window_closed():
	
	render_all()
	libtcod.console_flush()

	for object in objects:
		object.clear()	

	exit = handle_keys()
	if exit:
		break


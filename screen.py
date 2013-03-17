import libtcodpy as libtcod
import math

#Global, set variables

#Window setup variables
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

#Map size
MAP_WIDTH = 80
MAP_HEIGHT = 45

#dungeon generator parameters
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

#Field of View parameters
FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

#Room contents variables
MAX_ROOM_MONSTERS = 3


#Dungeon Colours
colour_dark_wall = libtcod.Color(0, 0, 100)
colour_light_wall = libtcod.Color(130, 110, 50)
colour_dark_ground = libtcod.Color(50, 50, 150)
colour_light_ground = libtcod.Color(200, 180, 50)


#defines the state of a tile - is it able to be walked on and is it sight-blocking?
class Tile:
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked

		self.explored = False

		if block_sight is None:
			block_sight = blocked
		self.block_sight = block_sight

#defines a rectangle
class Rect:
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h
	
	def center(self):
		center_x = (self.x1 + self.x2) / 2
		center_y = (self.y1 + self.y2) / 2
		return (center_x, center_y)

	def intersect(self, other):
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and 
			self.y1 <= other.y2 and self.y2 >= other.y1)


#A generic object. Anything that has a position on the screen uses this - walls, npcs, the player.
class Object:
	def __init__(self, x, y, char, name, colour, blocks=False, fighter=None, ai=None):
		self.x = x
		self.y = y
		self.char = char
		self.name = name
		self.colour = colour
		self.blocks = blocks
		self.fighter = fighter
		if self.fighter:
			self.fighter.owner = self

		self.ai = ai
		if self.ai:
			self.ai.owner = self

	def move(self, dx, dy):
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy

	def move_towards(self, target_x, target_y):
		dx = target_x - self.x
		dy = target_y - self.y

		distance = math.sqrt(dx ** 2 + dy ** 2)

		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		self.move(dx, dy)
	
	def distance_to(self, other):
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)
	
	def draw(self):
		#sets the character and the colour
		libtcod.console_set_default_foreground(con, self.colour)
		libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
	
	def send_to_back(self):
		global objects
		objects.remove(self)
		objects.insert(0, self)
	
	def clear(self):
		#clears the character from the old position
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

#class defining combat properties
class Fighter:
	def __init__(self, hp, defence, power, death_function=None):
		self.max_hp = hp
		self.hp = hp
		self.defence = defence
		self.power = power
		self.death_function = death_function

	def take_damage(self, damage):
		if damage > 0:
			self.hp -= damage
			
			if self.hp <= 0:
				function = self.death_function
				if function is not None:
					function(self.owner)
	
	def attack(self, target):
		damage = self.power - target.fighter.defence

		if damage > 0:
			print self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.'
			target.fighter.take_damage(damage)
		else:
			print self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!'


#class defining monsters
class BasicMonster:
	def take_turn(self):
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)
			elif player.fighter.hp > 0:
				monster.fighter.attack(player)

#changes the game state to dead, alerts the player that they are dead
def player_death(player):
	global game_state
	print 'You died!'
	game_state = 'dead'

	player.char = '%'
	player.colour = libtcod.dark_red

#turns dead monsters into corpses
def monster_death(monster):
	print monster.name.capitalize() + ' is dead!'
	monster.char = '%'
	monster.colour = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()

#checks if a tile is taken up by something that can block movement(player, npc, monster) or is a wall
def is_blocked(x, y):
	if map[x][y].blocked:
		return True
	
	for object in objects:
		if object.blocks and object.x == x and object.y == y:
			return True

	return False

#creates a room
def create_room(room):
	global map
	
	for x in range(room.x1 + 1, room.x2):
		for y in range(room.y1 + 1, room.y2):
			map[x][y].blocked = False
			map[x][y].block_sight = False

#creates a horizontal corridor
def create_h_tunnel(x1, x2, y):
	global map
	
	for x in range(min(x1, x2), max(x1, x2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False

#creates a vertical corridor
def create_v_tunnel(y1, y2, x):
	global map

	for y in range(min(y1, y2), max(y1, y2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False

#makes the map in full
def make_map():
	global map, player

	map = [[Tile(True)
		for y in range(MAP_HEIGHT) ]
			for x in range(MAP_WIDTH) ]
	rooms = []
	num_rooms = 0

	for r in range(MAX_ROOMS): 
		w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

		new_room = Rect(x, y, w, h)

		failed = False
		for other_room in rooms:
			if new_room.intersect(other_room):
				failed = True
				break

		if not failed:
			
			create_room(new_room)
			
			(new_x, new_y) = new_room.center()

			if num_rooms == 0:
				player.x = new_x
				player.y = new_y
			else:
				(prev_x, prev_y) = rooms[num_rooms - 1].center()
				if libtcod.random_get_int(0, 0, 1) == 1:
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
				else:
					create_v_tunnel(prev_y, new_y, prev_x)
					create_h_tunnel(prev_x, new_x, new_y)

			rooms.append(new_room)
			place_objects(new_room)
			num_rooms += 1

#populates a given room with objects
def place_objects(room):
	num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)
	
	
	for i in range(num_monsters):
		x = libtcod.random_get_int(0, room.x1, room.x2)
		y = libtcod.random_get_int(0, room.y1, room.y2)
		#this if is a bit limited, when more mobs are thought up, a more complex replacement will be made.
		if not is_blocked(x, y):
			if libtcod.random_get_int(0, 0, 100) < 80:
				fighter_component = Fighter(hp=5, defence=0, power=2, death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x, y, 'p', 'parasite', libtcod.desaturated_green, blocks=True, fighter=fighter_component,
						ai=ai_component)
			else:
				fighter_component = Fighter(hp=10, defence=1, power=3, death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x, y, 'k', 'kree', libtcod.darker_green, blocks=True, fighter=fighter_component,
						ai=ai_component)
		
			objects.append(monster)

#assigns colours to the map areas and calculates the field of view
def render_all():
	global fov_map, colour_dark_wall, colour_light_wall
	global colour_light_ground, colour_dark_ground
	global fov_recompute

	if fov_recompute:
		fov_recompute = False
		libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				visible = libtcod.map_is_in_fov(fov_map, x, y)
				wall = map[x][y].block_sight
				if not visible:
					if map[x][y].explored:
						if wall:
							libtcod.console_set_char_background(con, x, y, colour_dark_wall, libtcod.BKGND_SET)
						else:
							libtcod.console_set_char_background(con, x, y, colour_dark_ground, libtcod.BKGND_SET)
				else:
					if wall:
						libtcod.console_set_char_background(con, x, y, colour_light_wall, libtcod.BKGND_SET)
					else:
						libtcod.console_set_char_background(con, x, y, colour_light_ground, libtcod.BKGND_SET)
					map[x][y].explored = True
	for object in objects:
		if object != player:
			object.draw()

	player.draw()

	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
	
	libtcod.console_set_default_foreground(con, libtcod.white)
	libtcod.console_print_ex(0, 1, SCREEN_HEIGHT - 2, libtcod.BKGND_NONE, libtcod.LEFT, 'HP: ' + str(player.fighter.hp) + str(player.fighter.max_hp))

#determines whether the player moves or attacks(fancy that) - it checks whether there is something targetable, else, movement occurs.
def player_move_or_attack(dx, dy):
	global fov_recompute

	x = player.x + dx
	y = player.y + dy

	target = None
	for object in objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break
	
	if target is not None:
		player.fighter.attack(target)
	else:
		player.move(dx, dy)
		fov_recompute = True

#Handles all events relating to relevant key-presses
def handle_keys():
		
	key = libtcod.console_wait_for_keypress(True)
	
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+enter toggles fullscreen mode
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	elif key.vk == libtcod.KEY_ESCAPE:
		return True #exit the game
	if game_state == 'playing':
		#movement keys - WASD
		if key.vk == libtcod.KEY_CHAR:
			if key.c == ord('w'):
				player_move_or_attack(0, -1)
			elif key.c == ord('s'):
				player_move_or_attack(0, 1)
			elif key.c == ord('a'):
				player_move_or_attack(-1, 0)
			elif key.c == ord('d'):
				player_move_or_attack(1, 0)
			else:
				return 'didnt-take-turn'

#console initialization and main game loop
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Expedition', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

#initialise the player and components of them
fighter_component = Fighter(hp=30, defence=2, power=5, death_function=player_death)
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)
objects = [player]

#initialise the map
make_map()

#sets up the field of view
fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
	for x in range(MAP_WIDTH):
		libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

fov_recompute = True
game_state = 'playing'
player_action = None

while not libtcod.console_is_window_closed():
	
	render_all()
	libtcod.console_flush()
	
	for object in objects:
		object.clear()	
	
	#player's turn
	player_action = handle_keys()
	if player_action == 'exit':
		break
	
	#monster's turn
	if game_state == 'playing' and player_action != 'didnt-take-turn':
		for object in objects:
			if object.ai:
				object.ai.take_turn()

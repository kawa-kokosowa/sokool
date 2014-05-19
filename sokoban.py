import curses
import math
import sys


# CONFIG CONSTANTS ############################################################


BACKGROUND_CHARACTER = '/'
BACKGROUND_COLOR = curses.COLOR_WHITE
FOREGROUND_COLOR = curses.COLOR_BLACK
PLAYER_CHARACTER = '@'


# A* ALGORITHM/PATH GENERATION ################################################


def distance(plot_a, plot_b):
    """The Distance formula."""

    a_x, a_y = plot_a
    b_x, b_y = plot_b
    x = a_x - b_x
    y = a_y - b_y

    return math.sqrt(x * x + y * y)


def heuristic_cost_estimate(start, goal):
    diff_x = math.fabs(start[0] - goal[0])
    diff_y = math.fabs(start[1] - goal[1])

    return 10 * (diff_x + diff_y)


def reconstruct_path(came_from, current_node):

    if current_node in came_from:
        p = reconstruct_path(came_from, came_from[current_node])

        return p + (current_node,)  # p + current_node

    else:

        return (current_node,)


def astar(start, goal, strict=False):
    coordinates = room.coordinates
    closedset = set()  # set of nodes already evaluated
    openset = set([start])  # set of tentative nodes to be evaluated
    came_from = {}  # map of navigated nodes
    g_score = {start: 0}  # cost from start along best known path

    # estimated total cost from start to goal through y
    f_score = {start: heuristic_cost_estimate(start, goal)}

    while openset:
        # the node in openset having the lowest f_score[] value.
        openset_f_scores = {}

        for plot in openset:
            score = f_score.get(plot, None)

            if score is None:
                continue

            openset_f_scores[plot] = score

        current = min(openset_f_scores, key=openset_f_scores.get)

        if current == goal:

            return reconstruct_path(came_from, goal)

        openset.remove(current)
        closedset.add(current)

        # generate "adjacent" tiles of movement
        current_x, current_y = current
        up = (current_x - 1, current_y)
        left = (current_x, current_y - 1)
        down = (current_x, current_y + 1)
        right = (current_x + 1, current_y)
        adjacent = (up, left, down, right)

        for neighbor in adjacent:
            tentative_g_score = g_score[current] + distance(current, neighbor)

            # needs to reference tile_type's impassable value
            tile_type = room[neighbor]

            if tile_type in ('#', '%', '$'):
                closedset.add(neighbor)

                continue

            if (neighbor in closedset
                and tentative_g_score >= g_score[neighbor]):

                continue

            if (neighbor not in openset
                or tentative_g_score < g_score[neighbor]):

                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = (tentative_g_score
                                     + heuristic_cost_estimate(neighbor, goal))

                if neighbor not in openset:
                    openset.add(neighbor)

    if strict:

        raise Exception('AStar: Impossible!')

    else:

        return None


# Game Objects ################################################################


class Player(object):

    def __init__(self):
        self.y = room.player_start_y
        self.x = room.player_start_x
        self.char = PLAYER_CHARACTER
        self.moves = 0
        self.in_menu = False

        # stats
        self.hp = 3
        self.max_hp = 3

        self.blocks = 0
        self.max_blocks = 2

        self.xp = 0

    def set_block(self, direction):

        if not self.blocks:

            return False

        x = self.x
        y = self.y
        current_plot = (x, y)

        if room[current_plot] == '&':
            self.hp -= 1
            del room.entities[current_plot]
            room[current_plot] = '@'

        if direction == 'left':
            x -= 1
        elif direction == 'right':
            x += 1
        elif direction == 'up':
            y -= 1
        elif direction == 'down':
            y += 1

        coord = (x, y)

        if self.blocks and not room[coord] in ['%', '#', '$']:
            room[coord] = '%'
            self.blocks -= 1
            self.add_moves(1)

            return True

        else:

            return False

    def add_moves(self, x):
        """Subtract by adding negative."""

        self.moves += x
        room.win.addstr(room.y - 1, 1, str(self.moves) + ' MOVES')

        # should target specific range
        room.win.refresh()
        screen.refresh()

    def update(self):
        key = screen.getch()
        x = self.x
        y = self.y

        # get out of existing menu if possible... else lock input.
        if self.in_menu:

            if key == ord('c'):
                room.win.touchwin()
                room.win.refresh()
                self.in_menu = False

                return False

            elif key == ord('q'):
                # end
                curses.nocbreak()
                screen.keypad(0)
                curses.echo()
                curses.endwin()
                sys.exit()

                return False

            else:

                return False

        if self.hp == 0:

            raise Exception('death!')

        # movement...
        moving_direction = None

        if key == curses.KEY_LEFT:
            x -= 1
            moving_direction = 'left'

        elif key == curses.KEY_UP:
            y -= 1
            moving_direction = 'up'

        elif key == curses.KEY_RIGHT:
            x += 1
            moving_direction = 'right'

        elif key == curses.KEY_DOWN:
            y += 1
            moving_direction = 'down'

        # now for setting blocks
        elif key == ord('a'):

            return self.set_block('left')

        elif key == ord('d'):

            return self.set_block('right')

        elif key == ord('w'):

            return self.set_block('up')

        elif key == ord('s'):

            return self.set_block('down')

        elif self.in_menu is False and key == ord('m'):
           stats =  curses.newwin(8, 18)
           stats.box()
           stats.addstr(1, 2, 'HP: %s/%s' % (self.hp, self.max_hp))
           stats.addstr(2, 2, 'BLOCKS: %s/%s' % (self.blocks, self.max_blocks))
           stats.addstr(3, 2, 'MOVES: ' + str(self.moves))
           stats.addstr(4, 2, 'XP: ' + str(self.xp))
           stats.addstr(6, 2, '(c)LOSE (q)UIT')
           stats.touchwin()
           stats.refresh()
           self.in_menu = True

           return False

        else:

            return False

        # entity/interaction checks
        if room[(x, y)] in ('#', '&'):

            return False

        if room[(x, y)] == '%':

            if not self.blocks == self.max_blocks:
                self.blocks += 1

            else:

                return False

        # pushing block?
        elif room[(x, y)] == '$':
            # we gotta check for block's boundaries when pushing
            check_x = x
            check_y = y

            # soon this will be a method
            if moving_direction == 'left':
                check_x -= 1
            elif moving_direction == 'up':
                check_y -= 1
            elif moving_direction == 'right':
                check_x += 1
            elif moving_direction == 'down':
                check_y += 1

            if room[(check_x, check_y)] in ['#', '%', '&', '$']:

                return False

            else:
                room[(check_x, check_y)] = '$'

        room[(self.x, self.y)] = ord(' ')
        self.x = x
        self.y = y
        room[(self.x, self.y)] = self.char
        self.add_moves(1)

        return True


class Enemy(object):

    def __init__(self, x, y):
        self.name = 'enemy'
        self.y = y
        self.x = x
        self.player_last_move_count = 0

    def update(self):
        """Handle rendering enemy's interaction with the world.

        """

        current_plot = (self.x, self.y)

        if room[current_plot] == '%':
            player.xp += 1
            del room.entities[current_plot]

            return None

        # determine direction to move via a*
        astar_path = astar(current_plot, (player.x, player.y))

        if astar_path is None:
            room[current_plot] = '*'

            return None

        first_step = astar_path[1]
        step_x, step_y = first_step

        if step_x > self.x:
            direction = 'right'
        elif step_x < self.x:
            direction = 'left'
        elif step_y > self.y:
            direction = 'down'
        elif step_y < self.y:
            direction = 'up'
        else:

            raise Exception((step_x, step_y))

        x = self.x
        y = self.y

        # movement...
        if direction == 'left':
            x -= 1
        elif direction == 'up':
            y -= 1
        elif direction == 'right':
            x += 1
        elif direction == 'down':
            y += 1

        if room[(x, y)] in ('#', '&'):

            return None

        if not room[current_plot] == '%':
            room[current_plot] = ord(' ')

        if room[(x, y)] == '@':
            player.hp -= 1
            del room.entities[current_plot]
            room[current_plot] = ' '

            return None

        del room.entities[current_plot]
        self.x = x
        self.y = y
        new_plot = (self.x, self.y)
        room[new_plot] = '&'
        room.entities[new_plot] = self


class CarryBlock(object):

    pass


class PushBlock(object):

    def __init__(self):
        """The typical sokoban push block."""

        pass


class Room(object):

    def __init__(self):
        """Need better way of storing objects at positions in the map?

        All objects can have __str__...

        room.entities[(x, y)] to store/get entities. Just use a hash
        table!

        """

        # generate model from file
        with open('rooms/test.txt') as f:
            file_contents = f.read()

        self.model = [list(row) for row in file_contents.split('\n')][:-1]
        self.player_position = None  # done in self.draw()

        self.y = len(self.model) + 1
        self.x = len(max(self.model))
        room = curses.newwin(self.y, self.x, 0, 0)
        self.win = room
        self.coordinates = []

        # store objects, e.g., enemies, blocks at positions
        self.entities = {}

    def __setitem__(self, key, value):
        x, y = key
        self.win.addch(y, x, value)
        self.model[y][x] = value
        self.win.refresh()

    def __getitem__(self, key):
        x, y = key

        return self.model[y][x]

    def draw(self):

        for y, row in enumerate(self.model):

            for x, col in enumerate(row):

                if col == '@':
                    self.player_start_x = x
                    self.player_start_y = y

                elif col == '&':
                    self.entities[(x, y)] = Enemy(x, y)

                self[(x, y)] = col
                self.coordinates.append((x, y))


# runtime/start UI
screen = curses.initscr()
curses.noecho()
curses.curs_set(0)
curses.start_color()
curses.use_default_colors()
curses.cbreak()
screen.keypad(1)
curses.init_pair(1, BACKGROUND_COLOR, FOREGROUND_COLOR)
screen.bkgd(BACKGROUND_CHARACTER, curses.color_pair(1))
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

screen.addstr(2, 2, 'PRESS M TO START')

room = Room()
room.draw()
room.win.addstr(room.y - 1, room.x - 7, '(m)ENU')
room.win.touchwin()

player = Player()

while 1:

    #screen.clear()
    if player.update() and room.entities:

        for entity in room.entities.values():

            if entity.name == 'enemy':
                entity.update()


"""Sokool: Sokoban Kool Edition
Lillian Lynn Mahoney

RPG elements!

Experience is a formula involving the # of moves to complete a level...

"""

import curses
import glob
import math
import sys


# CONFIG CONSTANTS ############################################################


BACKGROUND_CHARACTER = '/'
BACKGROUND_COLOR = curses.COLOR_WHITE
FOREGROUND_COLOR = curses.COLOR_BLACK
PLAYER_CHARACTER = '@'


# A* ALGORITHM/PATH GENERATION ################################################


def distance(plot_a, plot_b):
    """Cartesian coordinates distance."""

    a_x, a_y = plot_a
    b_x, b_y = plot_b
    x = a_x - b_x
    y = a_y - b_y

    return math.sqrt(x * x + y * y)


def heuristic_cost_estimate(start, goal):
    """Traversing cost estimator for the A* algorithm."""

    diff_x = math.fabs(start[0] - goal[0])
    diff_y = math.fabs(start[1] - goal[1])

    return 10 * (diff_x + diff_y)


def reconstruct_path(came_from, current_node):

    if current_node in came_from:
        p = reconstruct_path(came_from, came_from[current_node])

        return p + (current_node,)  # p + current_node

    else:

        return (current_node,)


def astar(start, goal):
    """Updated from some abandonded project of mine (SSHRPG).

    Args:
      start (tuple): (x, y) coord to start navigating from.
      goal (tuple): (x, y) coord to find a path to.

    Returns:
      list: list of coordinates to traverse to get to goal.

    """

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
        adjacent = [plot for plot in adjacent if plot in room.coordinates]

        for neighbor in adjacent:
            tentative_g_score = g_score[current] + distance(current, neighbor)

            # needs to reference tile_type's impassable value
            entity = room[neighbor]

            if entity.name in ('wall', 'place block', 'push block'):
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

    return None


class Menu(object):

    def __init__(self):
        self.rows = rows
        self.items = {}

    def item(self, item_title, callback=None):
        self.items[item_title] = callback

    def init(self):
        height = len(self.items)
        width = len(max(self.items.keys()))
        window =  curses.newwin(height, width)
        window.box()

        callback_index = {}

        for i, row in enumerate(self.items.keys()):
            y = i + 1
            window.addstr(y, 2, row)

            callback = self.items[row]

            if callback:
                callback_index[y] = self.items[row]

        close_pos_y = y + 2
        window.addstr(close_pos_y, 2, 'CLOSE')
        stats.touchwin()
        stats.refresh()

        # build the index of options
        cursor_positions = callback_index.keys()
        cursor_index = cursor_positions[0]
        window.putch(cursor_index, 0, '>')

        # time to navigate the menu with up and down
        while True:
            key = screen.getch()
            window.putch(cursor_index, 0, ' ')

            if key == curses.KEY_UP:
                cursor_index -= 1

            elif key == curses.KEY_DOWN:
                cursor_index += 1


# Game Objects ################################################################


class Player(object):

    def __init__(self):
        self.y = None
        self.x = None

        self.name = 'player'
        self.character = PLAYER_CHARACTER
        self.moves = 0
        self.in_menu = False
        self.solid = True
        self.underfoot = None

        # stats
        self.hp = 3
        self.max_hp = 3

        self.blocks = 0
        self.max_blocks = 2

        self.xp = 0

    def __str__(self):

        return self.char

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

        if self.blocks and not room[coord].name in ['place block', 'wall',
                                                    'push block']:

            room[coord] = PlaceBlock()
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
        conflict_entity = room[x, y]

        # if there is an entity conflict for this coordinate, we
        # should deal with the conflict based on opposing name
        if conflict_entity.name in ('wall', 'enemy'):

            return False

        elif conflict_entity.name == 'place block':

            if not self.blocks == self.max_blocks:
                self.blocks += 1

            else:

                return False

        # pushing block?
        elif conflict_entity.name == 'push block':
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

            if room[(check_x, check_y)].solid:

                # you can't push a block into a solid object!
                return False

            else:
                room.move((x, y), (check_x, check_y))

        old_coord = (self.x, self.y)
        self.x = x
        self.y = y
        new_coord = (x, y)

        room.move(old_coord, new_coord)
        self.add_moves(1)

        return True


class Enemy(object):

    def __init__(self):
        self.name = 'enemy'
        self.y = None
        self.x = None
        self.player_last_move_count = 0
        self.character = '&'
        self.solid = True
        self.underfoot = None

    def __str__(self):

        return self.char

    def update(self):
        """Handle rendering enemy's interaction with the world.

        """

        current_plot = (self.x, self.y)

        if room[current_plot] == '%':
            player.xp += 1
            del room[current_plot]

            return None

        # determine direction to move via a*
        astar_path = astar(current_plot, (player.x, player.y))

        if astar_path is None:
            self.character = '*'

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

        entity = room[x, y]

        if entity.name in ('wall', 'enemy', 'place block'):

            return None

        elif entity.name == 'player':
            player.hp -= 1
            del room[current_plot]

            return None

        new_plot = (x, y)
        room.move(current_plot, new_plot)


class PlaceBlock(object):

    def __init__(self):
        """You can actually pick these up and place elsewhere."""

        self.character = '%'
        self.name = 'place block'
        self.solid = True
        self.underfoot = None

        self.x = None
        self.y = None


class PushBlock(object):

    def __init__(self):
        """The typical sokoban push block."""

        self.character = '$'
        self.name = 'push block'
        self.solid = True
        self.underfoot = None

        self.x = None
        self.y = None


class Goal(object):

    def __init__(self):
        """Where push blocks belong!"""

        self.character = '.'
        self.name = 'goal'
        self.solid = False
        self.underfoot = None

        self.x = None
        self.y = None


class Wall(object):

    def __init__(self):
        self.character = '#'
        self.name = 'wall'
        self.solid = True
        self.underfoot = None

        self.x = None
        self.y = None


class EmptySpace(object):

    def __init__(self):
        self.character = ' '
        self.name = 'empty'
        self.solid = False
        self.underfoot = None

        self.x = None
        self.y = None


class Room(object):

    def __init__(self, room=1):
        """Need better way of storing objects at positions in the map?

        All objects can have __str__...

        room.entities[(x, y)] to store/get entities. Just use a hash
        table!

        """

        # generate model from file
        self.room = room
        self.filename = glob.glob('rooms/%s - *.txt' % self.room)[0]

        with open(self.filename) as f:
            file_contents = f.read()

        # static_map is for containing characters within cells [y][x]
        self.static_map = [list(row) for row in file_contents.split('\n')][:-1]

        # extrapolate room meta
        self.y = len(self.static_map) + 1
        self.x = max([len(s) for s in self.static_map])
        self.coordinates = []
        self.goals = []  # so we may quickly check goal status later...

        # for window/curses control
        self.win = curses.newwin(self.y, self.x, 0, 0)

        # good place for items that move about, rendered last (highest z index)
        self.overlay_cells = {}

    def next(self):
        self.__init__(room=self.room)
        self.draw()
        self.win.addstr(room.y - 1, room.x - 7, '(m)ENU')
        room.win.touchwin()
        player = room.player

    def goals_complete(self):
        goals_complete = 0

        for goal in self.goals:

            if self[goal].name == 'push block':
                goals_complete += 1

        if goals_complete == len(self.goals):

            return True

        else:

            return False

    def __iter__(self):
        """Iterate through the entity objects which are on the overlay
        map.

        """

        return iter(self.overlay_cells.values())

    def __setitem__(self, key, value):
        """Directly affect the map's overlay cells.

        """

        x, y = key

        entity = value
        entity.x = x
        entity.y = y

        self.overlay_cells[(x, y)] = entity

        self.win.addch(y, x, entity.character)
        self.win.refresh()

    def __getitem__(self, key):

        return self.overlay_cells[key]

    def __delitem__(self, key):

        empty_space = EmptySpace()
        self.overlay_cells[key] = empty_space

        x, y = key
        self.win.addch(y, x, empty_space.character)
        self.win.refresh()

    def move(self, move_from, move_to):
        """Move an overlay cell by coordinate/key."""

        source = self[move_from]
        target = self[move_to]

        if source.underfoot:
            self[move_from] = source.underfoot
            source.underfoot = None

        else:
            del self[move_from]

        if not target.solid:
            source.underfoot = target

        self[move_to] = source

    def draw(self):
        """Should be called compile... maybe a part of init?"""

        # collect data from "static map" and transform into entities
        for y, row in enumerate(self.static_map):

            for x, col in enumerate(row):

                if col == '@':
                    self.player = Player()
                    self[(x, y)] = self.player

                elif col == '&':
                    self[(x, y)] = Enemy()

                elif col == '#':
                    self[(x, y)] = Wall()

                elif col == '%':
                    self[(x, y)] = PlaceBlock()

                elif col == '$':
                    self[(x, y)] = PushBlock()

                elif col == ' ':
                    self[(x, y)] = EmptySpace()

                elif col == '.':
                    self[(x, y)] = Goal()
                    self.goals.append((x, y))

                elif col == ';':
                    comment = ''.join(row[x:])

                    try:
                        self.win.addstr(y, x, comment)
                    except:
                        raise Exception(([x, y], [self.x, self.y], len(comment)))

                    break

                self.coordinates.append((x, y))

        # now draw the overlay/entitites
        for coordinate, entity in self.overlay_cells.items():
            x, y = coordinate

            try:
                self.win.addch(y, x, entity.character)
            except:
                raise Exception(entity.character)


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
player = room.player

while 1:

    #screen.clear()
    if player.update():

        # check if all goals complete
        if room.goals_complete():
            room = Room(room.room + 1)
            room.draw()
            room.win.addstr(room.y - 1, room.x - 7, '(m)ENU')
            room.win.touchwin()
            player = room.player

            continue

        # all entities move after player!
        for entity in room:

            if entity.name == 'enemy':
                entity.update()


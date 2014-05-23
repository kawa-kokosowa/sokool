# -*- coding: utf-8 -*-
"""Sokool: Sokoban Kool Edition
Lillian Lynn Mahoney

RPG elements!

Experience is a formula involving the # of moves to complete a level...

Record # of moves, level/character

Work on color next, all entities should have a color...

"""

import curses, curses.panel
import itertools
import textwrap
import random
import glob
import math
import sys
import os


# CONFIG CONSTANTS ############################################################


BACKGROUND_CHARACTER = '.'
BACKGROUND_COLOR = curses.COLOR_WHITE
FOREGROUND_COLOR = curses.COLOR_BLACK
PLAYER_CHARACTER = '@'

STATUS_PANEL_WIDTH = 35

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


def make_panel(width, height, position, title=None):
    """I need to document this better..."""

    win = curses.newwin(height, width, *position)
    win.erase()

    if title:
        win.box()
        title = ' ' + title + ' '
        win.addstr(0, 2, title, curses.A_REVERSE)

    panel = curses.panel.new_panel(win)

    return win, panel


def menu(rows):
    """Mostly a placeholder. Should use make_panel..."""
    stats =  curses.newwin(6, 18)
    stats.box()
    callbacks = rows.values()
    rows = rows.keys()

    while True:

        for i, row in enumerate(rows):
            stats.addstr(i + 1, 2, row)

        stats.addstr(2, 2, 'BLOCKS: %s/%s' % (self.blocks, self.max_blocks))
        stats.addstr(3, 2, 'MOVES: ' + str(self.moves))
        stats.addstr(4, 2, 'XP: ' + str(self.xp))
        stats.touchwin()
        stats.refresh()
        self.in_menu = True


# Game Objects ################################################################


class Player(object):

    def __init__(self):
        self.y = None
        self.x = None

        self.name = 'player'
        self.character = PLAYER_CHARACTER
        self.in_menu = False
        self.solid = True
        self.underfoot = None
        self.color_pair = 1

        # stats
        self.hp = 3
        self.max_hp = 3

        self.blocks = 0
        self.max_blocks = 2

        self.steps = 0
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

        self.steps += 1
        status.update()
        #screen.refresh()

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

        elif self.in_menu is False and key == curses.KEY_PPAGE:
            menu = Menu(['derp', 'bad', 'fad', 'ogay'])
            self.in_menu = True

            return False

            stats =  curses.newwin(6, 18)
            stats.box()
            stats.addstr(1, 2, 'HP: %s/%s' % (self.hp, self.max_hp))
            stats.addstr(2, 2, 'BLOCKS: %s/%s' % (self.blocks, self.max_blocks))
            stats.addstr(4, 2, 'XP: ' + str(self.xp))
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
        self.color_pair = 2

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
        self.color_pair = 3

        self.x = None
        self.y = None


class PushBlock(object):

    def __init__(self):
        """The typical sokoban push block."""

        self.character = '$'
        self.name = 'push block'
        self.solid = True
        self.underfoot = None
        self.color_pair = 4

        self.x = None
        self.y = None


class Goal(object):

    def __init__(self):
        """Where push blocks belong!"""

        self.character = '.'
        self.name = 'goal'
        self.solid = False
        self.underfoot = None
        self.color_pair = 5

        self.x = None
        self.y = None


class Wall(object):

    def __init__(self):
        self.character = '#'
        self.name = 'wall'
        self.solid = True
        self.underfoot = None
        self.color_pair = 6

        self.x = None
        self.y = None


class EmptySpace(object):

    def __init__(self):
        self.character = ' '
        self.name = 'empty'
        self.solid = False
        self.underfoot = None
        self.color_pair = 7

        self.x = None
        self.y = None


class StatusPanel(object):

    def __init__(self):
        """Sits to the right of the game screen. Displays
        general level and player data.

        Right-aligned. IS a curses panel.

        Args:
          room (int): room # to fetch meta and dialog for.

        """

        self.title = room.title

        # screen
        screen_height, screen_width = screen.getmaxyx()
        position = (0, screen_width - STATUS_PANEL_WIDTH)
        width = STATUS_PANEL_WIDTH
        self.width = width

        # draw the status panel...
        self.window, self.curses_panel = make_panel(width, screen_height,
                                                    position, self.title)

        # draw the story for this room if possible
        if os.path.exists('story/%s.txt' % room.room):
            story_position = 0
            story = curses.newpad(20, width)
            story.box()
            story.addstr(0, 2, ' EVENT LOG ', curses.A_REVERSE)

            with open('story/%s.txt' % room.room) as f:
                story_contents = f.readlines()

            paragraphs = []

            for i, paragraph in enumerate(story_contents):

                if paragraph == '\n':
                    paragraphs.append(' ')

                    continue

                paragraph = textwrap.wrap(paragraph,
                                          STATUS_PANEL_WIDTH - 4)

                if i == 0:
                    paragraph[0] = paragraph[0].upper()

                paragraphs.extend(paragraph)

            for y, line in enumerate(paragraphs):
                story.addstr(y + 2, 2, line)

        self.screen_height = screen_height
        self.screen_width = screen_width
        self.story_position = 0
        self.story_pad = story
        self.update()

    def update(self):
        self.window.addstr(2, 2, 'STEPS: %s' % player.steps)
        self.window.addstr(3, 2, 'HP: %s/%s' % (player.hp, player.max_hp))
        self.window.addstr(4, 2, 'BLOCKS: %s/%s' % (player.blocks,
                                                    player.max_blocks))
        self.window.addstr(5, 2, 'XP: %s' % player.xp)

        # refresh the screen
        curses.panel.update_panels()
        y_position = self.screen_height - 20
        x_position = self.screen_width - self.width
        self.story_pad.refresh(self.story_position, 0, y_position, x_position,
                               y_position + y_position,
                               x_position + (self.width - 1))
        screen.refresh()


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
        self.title = self.filename.rsplit('.', 1)[0].replace('rooms/', '')

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
        #self.win = curses.newwin(self.y, self.x, 0, 0)
        self.height, self.width = screen.getmaxyx()
        self.width -= STATUS_PANEL_WIDTH
        self.win = curses.newwin(self.height, self.width, 0, 0)

        # need a get_background command...
        self.win.bkgd(' ', curses.color_pair(1))
        self.background_lines = []

        if os.path.exists('backgrounds/%s.txt' % self.room):

            with open('backgrounds/%s.txt' % self.room) as f:
                background_lines = f.readlines()

            width = len(background_lines[0])
            height = len(background_lines)
            self.background_x_repeat = int(math.ceil(float(self.width)
                                                     / float(width)))
            self.background_y_repeat = int(math.ceil(float(self.height)
                                           / float(height)))

            for i in xrange(self.background_y_repeat):

                for line in background_lines:
                    line = line * self.background_x_repeat
                    self.background_lines.append(line)

        # good place for items that move about, rendered last (highest z index)
        self.overlay_cells = {}

    def next(self):
        self.__init__(room=self.room)
        self.draw()
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

        self.win.addch(y, x, entity.character,
                       curses.color_pair(entity.color_pair))
        self.win.refresh()

    def __getitem__(self, key):

        return self.overlay_cells[key]

    def __delitem__(self, key):

        empty_space = EmptySpace()
        self.overlay_cells[key] = empty_space

        x, y = key
        self.win.addch(y, x, empty_space.character,
                       curses.color_pair(empty_space.color_pair))
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
                    # new panel here?
                    comment = ''.join(row[x:])
                    self.win.addstr(y, x, comment, curses.A_REVERSE
                                                   | curses.A_BOLD)

                    break

                self.coordinates.append((x, y))

        # background lines
        for y, line in enumerate(self.background_lines):
            line = line.strip().replace('\n', '')

            for x, char in enumerate(line):

                try:
                    self.win.addch(y, x, char)
                except:

                    break

        # now draw the overlay/entitites
        for coordinate, entity in self.overlay_cells.items():
            x, y = coordinate
            self.win.addch(y, x, entity.character,
                           curses.color_pair(entity.color_pair))


# runtime/start UI
screen = curses.initscr()
curses.noecho()
curses.curs_set(0)
curses.start_color()
curses.use_default_colors()
curses.cbreak()
screen.keypad(1)

# make the color combos here...
colors = [
           curses.COLOR_BLACK,
           curses.COLOR_RED,
           curses.COLOR_GREEN,
           curses.COLOR_YELLOW,
           curses.COLOR_BLUE,
           curses.COLOR_MAGENTA,
           curses.COLOR_CYAN,
           curses.COLOR_WHITE,
         ]
random.shuffle(colors)
all_color_combos = itertools.combinations(colors, 2)
max_color_pair = 0

for combo in all_color_combos:
    max_color_pair += 1
    curses.init_pair(max_color_pair, *combo)

screen.bkgd(' ', curses.color_pair(1))
screen.addstr(2, 2, 'PRESS M TO START', curses.color_pair(2))

room = Room()
room.draw()
room.win.touchwin()

player = room.player
status = StatusPanel()

while 1:

    #screen.clear()
    if player.update():

        # check if all goals complete
        if room.goals_complete():
            room = Room(room.room + 1)
            room.draw()
            room.win.touchwin()
            player = room.player

            continue

        # all entities move after player!
        for entity in room:

            if entity.name == 'enemy':
                entity.update()


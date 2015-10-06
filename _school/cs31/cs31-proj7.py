"""
Quick and dirty implementation of project 7 ("Snake Pit") for CS31. The
programs are not exactly the same, design-wise, but have the same basic
relationships (e.g. here Player and Snake do not affect the board; Pit
does all the calculations and is the only one that changes the board).
About ~220 lines; not bad compared to snakepit.cpp's 500-line program skeleton.
"""

import sys
import random

class Game(object):
    def __init__(self, rows, cols, nsnakes):
        self.pit = None
        self._new_game(rows, cols, nsnakes)

    def _new_game(self, rows, cols, nsnakes):
        """Create new pit with player and nsnakes snakes."""
        self.pit = Pit(rows, cols)

        loc = gen_random_loc(self.pit.rows, self.pit.cols)
        #loc = (3, 2)
        self.pit.create_player(loc[0], loc[1])

        for i in xrange(nsnakes):
            loc = gen_random_loc(self.pit.rows, self.pit.cols)
            self.pit.create_snake(loc[0], loc[1])
    def test():
        self.pit.create_snake(3, 1)
        self.pit.create_snake(2, 2)
        self.pit.create_snake(4, 2)
        self.pit.create_snake(3, 3)
        self.pit.create_snake(3, 4)
        self.pit.create_snake(5, 2)

    def play(self):
        while True:
            self.pit.draw()
            print "\nu/d/l/r//q:",
            
            opt = raw_input()
            
            direc = None
            if opt == "u":
                direc = 3
            elif opt == "d":
                direc = 2
            elif opt == "l":
                direc = 1
            elif opt == "r":
                direc = 0
            elif opt == "q":
                print "Play stopped"
                break
            elif opt == "":
                pass
            else:
                print "Invalid option"
                continue

            self.pit.move_player(direc)
            self.pit.move_snakes()

            if len(self.pit.snakes) == 0:
                print "Congratulations on winning!"
                return
            if self.pit.player.dead:
                self.pit.draw()
                return

class Pit(object):
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.player = None
        self.snakes = []
        self.board = []

        for r in xrange(self.rows):
            self.board.append([0] * self.cols)

    def create_player(self, row, col):
        self.player = Player(self, row, col, 0)
        self.board[self.player.row-1][self.player.col-1] -= 1
        # This method of setting the board is much more efficient than the
        # spec's method of looping through self.snakes each time to figure
        # out how many snakes are on each spot

    def create_snake(self, row, col):
        loc = (row, col)     # Assumes row/col are in range of self.board
        
        # Don't spawn on the player
        while loc == (self.player.row, self.player.col):
            loc = gen_random_loc(self.rows, self.cols)
        snk = Snake(self, loc[0], loc[1])
        
        self.snakes.append(snk)
        self.board[snk.row-1][snk.col-1] += 1

    def destroy_snake(self, row, col):
        """Destroy snake at location and decrement board[i][j]."""
        for i, snk in enumerate(self.snakes):
            if snk.row == row and snk.col == col:
                self.board[snk.row-1][snk.col-1] -= 1
                del self.snakes[i]
                break

    def draw(self):
        for row in self.board:
            for cell in row:
                if cell == 0:
                    sys.stdout.write(".")
                elif cell == -1:
                    sys.stdout.write("@")
                elif cell <= -2:
                    sys.stdout.write("*")
                else:
                    n = min(cell, 9)         # Up to number nine
                    sys.stdout.write(str(n))
            sys.stdout.write("\n")
        print "There are {0} snakes left".format(len(self.snakes))
        if self.player.dead:
            print "The player is dead"
        else:
            print "The player has lasted {0} turns".format(self.player.age)

    def move_player(self, direc):
        # Move the player in the given direction
        pl = self.player
        self._move_player(pl, direc)
        if direc is None:        # Don't continue
            return

        # Check if over snake
        if self.board[pl.row-1][pl.col-1] > -1:
            # Save location, and attempt to move again
            loc = (pl.row, pl.col)
            self._move_player(self.player, direc, False)
            if loc == (pl.row, pl.col):     # If hit a wall, revert
                reverse = {
                    0: 1, 1: 0,
                    2: 3, 3: 2
                }.get(direc)
                self._move_player(self.player, reverse, False)
            elif self.board[pl.row-1][pl.col-1] > -1:
                self.player.die("Tried to jump over 2 snakes")
                self.board[self.player.row-1][self.player.col-1] = -2
            else:            # Destroy snake
                self.destroy_snake(loc[0], loc[1])
                print "Snake destroyed:", loc[0], loc[1]

    def _move_player(self, pl, direc, do_age=True):
        """Calls move() on the player and sets self.board accordingly."""
        self.board[pl.row-1][pl.col-1] += 1
        pl.move(direc, do_age)
        self.board[pl.row-1][pl.col-1] -= 1

    def move_snakes(self):
        """Make all the snakes move and modify self.board accordingly."""
        for snk in self.snakes:
            self.board[snk.row-1][snk.col-1] -= 1
            snk.move()
            self.board[snk.row-1][snk.col-1] += 1

            # Check if killed player
            if self.board[snk.row-1][snk.col-1] == 0:
                self.player.die("Eaten by snake")
                self.board[self.player.row-1][self.player.col-1] = -2
                break

class Player(object):
    def __init__(self, pit, row, col, age):
        self.pit = pit       # Note that pit is only used to access its rows/cols
        self.row = row
        self.col = col
        self.age = age
        self.dead = False

    def die(self, text):
        self.dead = True
        print "The player has died!", text

    def move(self, direc, do_age=True):
        if direc is not None:
            self.row, self.col = row_col_move(direc, self.row, self.col,
                                              self.pit.rows, self.pit.cols)
        if do_age:
            self.age += 1
        print "Player moved to:", self.row, self.col

class Snake(object):
    def __init__(self, pit, row, col):
        self.pit = pit
        self.row = row       # Since attributes are public, no getRow()/etc.
        self.col = col

    def move(self):
        """Randomly moves in any direction unless it hits a wall."""
        n = int(random.random() * 4)
        
        self.row, self.col = row_col_move(n, self.row, self.col,
                                          self.pit.rows, self.pit.cols)
        print "Snake moved to:", self.row, self.col

def gen_random_loc(rows, cols):
    row = int(random.random() * rows + 1)
    col = int(random.random() * cols + 1)
    return (row, col)

def row_col_move(direc, row, col, max_row, max_col):
    """Returns a tuple (row, col) to be set to the new row/col."""
    # 0 = right, 1 = left, 2 = down, 3 = up
    if direc == 0:
        col = min(max_col, col + 1)
    elif direc == 1:
        col = max(1, col - 1)
    elif direc == 2:
        row = min(max_row, row + 1)
    else:
        row = max(1, row - 1)

    return (row, col)

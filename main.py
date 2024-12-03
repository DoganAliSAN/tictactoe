# todo
# get players into same room
# handle player moves 
# make game functional (winning,losing,tie)
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from functools import partial
import sqlite3
import socket
import ast
import random
import math
import time
# when switching to game screen append current player name to player list 
# new connection should be included to this 
# game database should have how many players is inside the game 
# but this can cause slow database interactions
# for now i'll do this

def get_info(query):
    with sqlite3.connect("rooms.db") as sqliteConnection:
        cursor = sqliteConnection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
    return result
def update_info(query):
    with sqlite3.connect("rooms.db") as sqliteConnection:
        cursor = sqliteConnection.cursor()
        cursor.execute(query)
        sqliteConnection.commit()
def send_data(data):
    HOST = "127.0.0.1"
    PORT = 65434
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))
        s.sendall(data)
        response = s.recv(1024)
    return response
class MainScreen(Screen):
    def __init__(self,**kwargs):
        super (MainScreen, self).__init__(**kwargs)
        self.player = ""

        layout = GridLayout(cols=2,spacing=10,padding=10)
        self.sub_layout_1 = BoxLayout(orientation="vertical")
        sub_layout_1 = self.sub_layout_1
        layout.add_widget(sub_layout_1)

        rooms = Label(text="Rooms",size_hint_y = None,height=100)
        sub_layout_1.add_widget(rooms)
        self.buttons= []

        self.get_rooms()
        empty_label = Label()
        sub_layout_1.add_widget(empty_label)
        self.sub_layout_2 = BoxLayout(orientation="vertical")
        sub_layout_2 = self.sub_layout_2
        layout.add_widget(sub_layout_2)

        player_name_input = TextInput(hint_text="Player Name",size_hint_y=None,height=100)
        player_name_input.bind(text=self.player_name_set)
        sub_layout_2.add_widget(player_name_input)

        self.create_room = Button(text="Create Room",size_hint_y = None,height = 100,disabled=1)
        
        sub_layout_2.add_widget(self.create_room)
        self.create_room.bind(on_release= self.changer)
        #adding an empty label at the end because boxlayout stars stacking from bottom
        empty_label = Label()
        sub_layout_2.add_widget(empty_label)
        self.add_widget(layout)
    def changer(self,*args):
        self.manager.current = "Create Room"

    def player_name_set(self,*args):

        if len(args[0].text) != 0:
            for i in self.buttons:
                i.disabled=0
            self.create_room.disabled = 0
            self.player = args[0].text

        else:
            for i in self.buttons:
                i.disabled = 1
            self.create_room.disabled = 1
    def get_rooms(self,*args):
        result = get_info("SELECT * from rooms")


        for room in result:
            if room[6] == 2:
                #Theoretically this should prevent showing rooms that are full
                continue
            btn = Button(text = f"{room[1]} - {room[4]}",disabled = 1,size_hint_y=None,height=100)
            btn.bind(on_release=partial(self.redirect_to_room,room[5]))
            self.sub_layout_1.add_widget(btn)
            self.buttons.append(btn)
    def redirect_to_room(self,*args):
        #UPDATE table_name SET column1 = value1, column2 = value2...., columnN = valueN WHERE [condition];

        room_link = args[0]
        data = send_data(f"GETGAME|{room_link}".encode("utf-8"))
   
        data = data.decode("utf-8")
        
        game_info = ast.literal_eval(data)

        #open game screen with game info
        self.manager.screens[2].room_name = game_info[1]
        self.manager.screens[2].room_password = game_info[2]
        self.manager.screens[2].player_name = self.player
        self.manager.screens[2].game_size = game_info[4]
        self.manager.screens[2].game_link = game_info[5]
        self.manager.screens[2].second_player = game_info[-1]

        update_info(f"""UPDATE rooms set second_connection = "{game_info[-1]}" WHERE game_link = '{game_info[5]}'""")
        update_info(f"UPDATE rooms set current_players = 2 WHERE game_link = '{game_info[5]}'")

        self.manager.current = "Game"
class CreateRoom(Screen):
    def __init__(self,**kwargs):

        super (CreateRoom, self).__init__(**kwargs)
        self.game_size = "3x3"
        self.game_link = ""
        self.player_name = ""

        # one grid layout 
        layout = GridLayout(cols=2,spacing=10,padding=10)
        # one grid and one box layout inside it 
        self.sub_layout_1 = GridLayout(cols=2)
        sub_layout_1 = self.sub_layout_1
        layout.add_widget(sub_layout_1)
        # first box layout:
        # back to home button
        back_to_home = Button(text="Home Page",size_hint=  (None,None),height=200,width=200)
        back_to_home.bind(on_release=self.changer)
        sub_layout_1.add_widget(back_to_home)
        # game size button (that changes when you press it)
        self.game_size_button = Button(text=self.game_size,size_hint=  (None,None),height=200,width=200)
        self.game_size_button.bind(on_release= self.change_game_size)
        sub_layout_1.add_widget(self.game_size_button)
        # preview space of game
        self.preview = GridLayout(cols=3,rows=3)
        preview = self.preview
        for i in range(9): #default game is 3x3
            btn = Button(text=" ")
            preview.add_widget(btn)


            #this actually doesn't require anything game size button will append buttons into it 
        # second box layout:
        sub_layout_2 = BoxLayout(orientation = "vertical")
        layout.add_widget(sub_layout_2)
        # room name input box
        self.room_name = TextInput(hint_text="Room Name")
        sub_layout_2.add_widget(self.room_name)
        # password input box
        self.password_input = TextInput(hint_text = "Room Password")
        sub_layout_2.add_widget(self.password_input)
        # create room button 
        create_room = Button(text="Create Room")
        create_room.bind(on_release= self.create_room)
        sub_layout_2.add_widget(create_room)
        layout.add_widget(preview)

        self.add_widget(layout)

    def changer(self,*args):
        self.manager.current = "Main Page"

    def get_player(self,*args):

        self.player_name = self.manager.screens[0].player

    def change_game_size(self,*args):
        game_sizes = ["3x3","4x4","5x5"]
        #find index of current game size and add 1 to get next game size
        local_next_index = game_sizes.index(self.game_size) + 1 
        if len(game_sizes) <= local_next_index:
            local_next_index = 0
        
        self.game_size = game_sizes[local_next_index] 
        self.game_size_button.text = self.game_size
        grid = [int(x) for x in self.game_size.split("x")]
        children = self.preview.children[:]
        for i in children:
            self.preview.remove_widget(i)
        self.preview.cols = grid[0]
        self.preview.rows = grid[1]
        for i in range(grid[0] * grid[1]):
            btn = Button(text= " ")
            self.preview.add_widget(btn)
        
    def generate_link(self,*args):

        #room_name+playername+firstpartofgamesize
        self.get_player()
        self.game_link = self.room_name.text.replace(" ","") + self.player_name + self.game_size[0] + str(random.randint(0,99))
        return self.game_link

    def create_room(self,*args):
        game_link = self.generate_link()
        data = send_data(f"CREATEGAME|['{self.room_name.text}','{self.password_input.text}','{self.player_name}','{self.game_size}','{game_link}']".encode("utf-8"))
        data = data.decode("utf-8")
        if  "Success" in data:

            self.manager.screens[2].room_name = self.room_name.text
            self.manager.screens[2].room_password = self.password_input.text
            self.manager.screens[2].player_name = self.player_name
            self.manager.screens[2].game_size = self.game_size
            self.manager.screens[2].game_link = game_link
            self.manager.screens[2].creator = data.split("|")[1]
            update_info(f"""UPDATE rooms set creator_connection = "{data.split("|")[1]}" WHERE game_link = '{game_link}'""")

            self.manager.current = "Game"

class Game(Screen):
    def __init__(self, **kwargs):
        
        super(Game, self).__init__(**kwargs)
        #'room_name','room_password','creator_name','game_size','game_link'
        self.room_name = ""
        self.room_password = ""
        self.player_name = ""
        self.game_size = ""
        self.game_link = ""
        self.second_player = ""
        self.creator = ""
        self.winner = ""
        self.current_player  = ""
        self.open_event = []
        self.layout_buttons = []
        self.layout = GridLayout(cols=3,rows=3,spacing = 10 )

        layout = self.layout

        self.add_widget(layout)
    def update_buttons(self, *args):
        current_player = self.current_player
        moves = get_info(f"SELECT moves FROM rooms WHERE game_link = '{self.game_link}' ")[0]
        if moves[0]:
            moves = ast.literal_eval(moves[0])
            for i in moves:
                row,col = self.get_row_and_col(i[0],int(self.game_size.split("x")[0]))
                self.update_button_text(row,col,i[1])
    def on_enter(self, *args):
        # This will be called when the screen is activated (entered)

        game_size_list = [int(x) for x in self.game_size.split("x")]
        game_size = math.prod(game_size_list)
        self.layout.cols = game_size_list[0]
        self.layout.rows = game_size_list[1]
        for i in range(game_size): #default game is 3x3
            
            
            btn = Button(text=" ")
            btn.place = i 
            btn.bind(on_release = self.move)
            self.layout_buttons.append(btn)
            self.layout.add_widget(btn)
    
        event_1 = Clock.schedule_interval(self.update_buttons, 1)
        self.open_event.append(event_1)
        if self.game_size:
            event_2 = Clock.schedule_interval(lambda dt: self.check_winner(int(self.game_size.split("x")[0])), 1)
            self.open_event.append(event_2)


    def changer(self,*args):
        self.manager.current = "Create Room"
        self.winner = ""
        self.layout.clear_widgets()

    def update_button_text(self, target_row, target_col, new_text):

        # Iterate through grid children (buttons) in reverse order
        for index, btn in enumerate(reversed(self.layout.children)):  # reverse children list
            # Calculate the button's row and column based on the grid layout
            row = index // self.layout.cols  # Row is calculated by dividing the index by number of columns
            col = index % self.layout.cols   # Column is the remainder of the index divided by number of columns

            # If we find the button at the target row and column, update its text
            if row == target_row and col == target_col:
                btn.text = new_text
                self.layout.spacing = 10
                return  # Exit once the button is found and updated
    def check_winner(self, game_size):
        """
        Checks for a winner in a Tic-Tac-Toe game where 3 consecutive symbols (horizontally, vertically, or diagonally) win.

        Parameters:
            game_size (int): Size of the Tic-Tac-Toe grid (e.g., 3 for a 3x3 grid).
        """
        moves = get_info(f"SELECT moves FROM rooms WHERE game_link = '{self.game_link}'")[-1]
        
        
        if moves[0]:
            moves = ast.literal_eval(moves[0])
        else:
            moves = []

        # Create an empty board
        board = [['' for _ in range(game_size)] for _ in range(game_size)]

        # Fill the board with moves
        for position, player in moves:
            row = position // game_size
            col = position % game_size
            board[row][col] = player

        # Function to check for a winning sequence of 3
        def is_winner(sequence):
            return sequence == ['X', 'X', 'X'] or sequence == ['O', 'O', 'O']

        # Check rows for a winning sequence of 3
        for row in range(game_size):
            for col in range(game_size - 2):  # Only check valid subsets
                if is_winner([board[row][col], board[row][col + 1], board[row][col + 2]]):
                    self.winner = board[row][col]
                    break

        # Check columns for a winning sequence of 3
        for col in range(game_size):
            for row in range(game_size - 2):  # Only check valid subsets
                if is_winner([board[row][col], board[row + 1][col], board[row + 2][col]]):
                    self.winner = board[row][col]
                    break

        # Check diagonals for a winning sequence of 3
        for row in range(game_size - 2):
            for col in range(game_size - 2):
                # Main diagonal
                if is_winner([board[row][col], board[row + 1][col + 1], board[row + 2][col + 2]]):
                    self.winner = board[row][col]
                    break
                # Anti-diagonal
                if is_winner([board[row][col + 2], board[row + 1][col + 1], board[row + 2][col]]):
                    self.winner = board[row][col + 2]
                    break
        if all(board[row][col] != '' for row in range(game_size) for col in range(game_size)):
            
            self.winner = "Tie"

        # If a winner is found
        if self.winner and self.winner != "Tie":
            self.layout.clear_widgets()

            # Unschedule all events
            for i in self.open_event:
                Clock.unschedule(i)

            # Add the winner label
            lbl = Label(text=f"Winner is {self.winner}", font_size=50)
            self.layout.add_widget(lbl)

            # Schedule the changer function to run after 3 seconds
            Clock.schedule_once(lambda dt: self.changer(), 3)
        elif self.winner == "Tie":
            self.layout.clear_widgets()

            # Unschedule all events
            for i in self.open_event:
                Clock.unschedule(i)

            # Add the winner label
            lbl = Label(text=f"Tie", font_size=50)
            self.layout.add_widget(lbl)

            # Schedule the changer function to run after 3 seconds
            Clock.schedule_once(lambda dt: self.changer(), 3)


    def get_row_and_col(self,button_number, grid_cols):
        # Calculate row and column based on button number and grid columns
        row = button_number // grid_cols  # Integer division gives the row
        col = button_number % grid_cols  # Modulus gives the column
        return row, col
    def move(self,*args):

        button_loc = args[0].place

        game_size = [int(x) for x in self.game_size.split("x")]
     
        result = get_info(f"SELECT creator_name from rooms WHERE game_link = '{self.game_link}'")
        
        
        
        current_player = None
        if self.player_name == result[0][0]:
            opposite_player = self.second_player
            current_player = "X"
            self.current_player = current_player
        else:
            opposite_player = self.creator
            current_player = "O"
            self.current_player = current_player


        row,col = self.get_row_and_col(button_loc,game_size[0])

        moves = get_info(f"SELECT moves FROM rooms WHERE game_link = '{self.game_link}'")[0][0]
        
        
        if not moves:
            new_moves = f"[[{button_loc},'{current_player}']]"
            self.update_button_text(row,col,current_player)
            
        else:
            new_moves = ast.literal_eval(moves)
            if new_moves[-1][1] != self.current_player:     
                move_indexes = [x[0] for x in new_moves]
                
                
                if button_loc in move_indexes:
                    pass
                else:
                    new_moves.append([button_loc,current_player])

                    self.update_button_text(row,col,current_player)

            
            new_moves = f"{new_moves}"
        query = f"""Update rooms set moves = "{new_moves}" WHERE game_link = '{self.game_link}'"""

        update_info(query)
        data = send_data(f"MOVE|['{self.game_link}','{col}','{row}',{opposite_player}]".encode("utf-8"))
class TicTacToe(App):
    #this is main page so other pages should be added to here

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="Main Page"))
        sm.add_widget(CreateRoom(name="Create Room"))
        sm.add_widget(Game(name="Game"))
        sm.current = "Main Page"
        return sm
    def switch_screen(self,instance):
        sm.current="Create Room"
        
if __name__=="__main__":
	TicTacToe().run()

import pygame
import io
from ChessEngine import GameState, Move
import ChessAI
import time
import os
# import PIL
# import pygame.freetype    

def get_square(coords: tuple[int, int]):
    '''Return chess board square based on screen coordinates'''

    return coords[1] // SQ_SIZE, coords[0] // SQ_SIZE

def update_move(move_played: Move, valid_move: Move) -> Move:
    '''Update move attributes from another move'''

    move_played.is_enpassant = valid_move.is_enpassant # updating registered move with en passant flag
    move_played.piece_captured = valid_move.piece_captured # updating registered piece captured to incorporate en passant flag
    move_played.is_promotion = valid_move.is_promotion # updating registered move with promotion flag
    move_played.is_castling = valid_move.is_castling # updating registered move with castling flag
    
def load_images_png():
    '''Loads .png piece images into memory (only do this once for efficiency)'''
    
    pieces = ['bR','bN','bB','bQ','bK','bP','wR','wN','wB','wQ','wK','wP']
    for piece in pieces:
        piece_image = pygame.image.load(f'./images/png/{piece}.png')
        IMAGES[piece] = pygame.transform.scale(piece_image, (SQ_SIZE, SQ_SIZE))
        # IMAGES[piece] = pygame.image.load(f'./images/{piece}.svg') # transform="scale(2.4)"
        piece_image.fill((255, 255, 255 , 128), None, pygame.BLEND_RGBA_MULT) # alpha = 128, change for transparency
        TRANSPARENT_IMAGES[piece] = pygame.transform.scale(piece_image, (SQ_SIZE, SQ_SIZE))

def load_images_svg():
    '''Loads .svg piece images into memory (only do this once for efficiency)'''
    
    pieces = ['bR','bN','bB','bQ','bK','bP','wR','wN','wB','wQ','wK','wP']
    for piece in pieces:
        # read each file
        svg_string = open(f'./images/svg/{piece}.svg', "rt").read()
        # looking for viewBox="0 0 50 50" in svg text to get image display size, get last number
        view_box_start = svg_string.find('viewBox="') + 9
        view_box_end = view_box_start + svg_string[view_box_start:].find('"')
        view_box = svg_string[view_box_start:view_box_end]
        dim = int(view_box.split(' ')[-1])
        # scale up to board square size, add back to svg string, load image
        scale = round(SQ_SIZE / dim, 2)
        svg_string = svg_string[:4] + f' transform="scale({scale})"' + svg_string[4:]
        piece_image = pygame.image.load(io.BytesIO(svg_string.encode())) 
        IMAGES[piece] = piece_image
        # get transparent copies for moving state
        piece_image_copy = piece_image.copy()
        piece_image_copy.fill((255, 255, 255 , 128), None, pygame.BLEND_RGBA_MULT) # alpha = 128, change for transparency
        TRANSPARENT_IMAGES[piece] = piece_image_copy

def load_sounds():
    '''Initial load for sound files'''
    
    folder = './sounds/'
    for file in os.listdir(folder):
        filename = file.split('.')[0]
        SOUNDS[filename]= pygame.mixer.Sound(os.path.join(folder, file))
    
def play_sound(move: Move):
    '''Play different sounds for capture and non-capture move'''
    
    if move.piece_captured != '--':
        SOUNDS['capture'].play()
    else:
        SOUNDS['move'].play()

def draw_board(screen: pygame.display):
    '''Displays chess board with row and column lables'''
       
    pygame.display.set_caption('Chess')
    label_font = pygame.font.SysFont('CaskaydiaCove NF', SQ_SIZE // 5)
    
    # draw colored squares
    for i in range(DIMENSIONS):
        for j in range(DIMENSIONS):
            screen.fill(COLORS[(i + j) % 2], (j * SQ_SIZE, i * SQ_SIZE, SQ_SIZE, SQ_SIZE))        

    # display row & column labels
    for i, ch in enumerate('abcdefgh'):
        number_color = COLORS[1-(i % 2)]    
        number_label = label_font.render(str(8-i), True, number_color)
        screen.blit(number_label, (2, 2 + i * SQ_SIZE))
        
        letter_color = COLORS[i % 2]
        letter_label = label_font.render(ch, True, letter_color)
        screen.blit(letter_label, ((i+1) * SQ_SIZE - letter_label.get_width() - 2, screen.get_height() - letter_label.get_height() - 2))

def draw_pieces(gs: GameState, screen: pygame.display):
    '''Displays chess pieces based on gamestate'''
    
    for i, row in enumerate(gs.board):
        for j, cell in enumerate(row):      
            if cell != '--':
                piece = IMAGES[cell]
                screen.blit(piece, (j * SQ_SIZE, i * SQ_SIZE))
      
def draw_moving_state(gs: GameState, screen: pygame.display, valid_moves: list[Move], square: tuple[int, int]):
    '''Displays the board with selected piece moving with the cursor and home square greyed out'''
    
    r, c = square
    piece = gs.get_piece(square)
    draw_board(screen)
    highlight_last_move(gs, screen)
    highlight_moves(gs, screen, valid_moves, square)
    draw_pieces(gs, screen)

    # shade the starting square 
    s = pygame.Surface((SQ_SIZE, SQ_SIZE))
    s.fill(COLORS[(r + c) % 2])
    screen.blit(s,(c * SQ_SIZE, r * SQ_SIZE))
    highlight_start_sq(screen, square)
    transp_img = TRANSPARENT_IMAGES[piece]
    screen.blit(transp_img, (c * SQ_SIZE, r * SQ_SIZE))

    # draw moving piece on top of mouse    
    piece_img = IMAGES[piece]
    screen.blit(piece_img, (pygame.mouse.get_pos()[0] - SQ_SIZE//2, pygame.mouse.get_pos()[1] - SQ_SIZE//2))
       
def get_promotion_squares(square: tuple[int, int]) -> dict:
    '''
    Return dictionary of promotion squares in the form "square: piece".
    E.g. {(0,1): 'wQ', (1,1): 'wN', (2,1): 'wR', (3,1): 'wB'}
    '''
    
    if square[0] == 0: # if white promotes go down the board, if black - go up the board
        direction = 1
        color = 'w'
    else:
        direction = -1
        color = 'b'
    
    promotion_pieces = ['Q', 'N', 'R', 'B']
    promotion_sqs = {(square[0] + direction * i, square[1]): color + promotion_pieces[i] for i in range(4)}
    return promotion_sqs   
 
def draw_promotion(gs: GameState, screen: pygame.display, square: tuple[int, int]):
    '''Displays special promotion screen when pawn reaches edge rank with options to promote to (Queen, Knight, Rook, Bishop) for user to click'''
    
    draw_board(screen)
    draw_pieces(gs, screen)
    # draw opaque square on top of the screen during promotion for highlighting
    s = pygame.Surface(SIZE)
    s.set_alpha(150)                # level of opacity
    s.fill((0,0,0))           # background color
    screen.blit(s, (0,0))    # (0,0) are the top-left coordinates

    promotion_sqs = get_promotion_squares(square) # get squares relevant for promotion based on file and color
    
    for sq in promotion_sqs:
        piece = promotion_sqs[sq]
        img = IMAGES[piece]
        x = sq[1] * SQ_SIZE
        y = sq[0] * SQ_SIZE
        screen.fill(COLORS[(sq[0] + sq[1]) % 2], (x, y, SQ_SIZE, SQ_SIZE))
        screen.blit(img, (x, y))

def highlight_start_sq(screen: pygame.display, square: tuple[int, int]):
    '''Highlight starting square'''
    
    color = (235, 100, 64) # orange
    r, c = square
    s = pygame.Surface((SQ_SIZE, SQ_SIZE))
    s.set_alpha(200)
    s.fill(color)
    screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

def highlight_moves(gs: GameState, screen: pygame.display, valid_moves: list[Move], square: tuple[int, int]):
    '''Highlights possible moves for piece on selected square'''

    # highlight target squares
    for move in valid_moves:
        if move.start_sq == square:
            r_e, c_e = move.end_sq
            highl_color = HIGHLIGHT_COLORS[(r_e + c_e) % 2]
            if gs.get_piece(move.end_sq) == '--':
                # draw circles for empty squares 
                pygame.draw.circle(screen, highl_color, (c_e * SQ_SIZE + SQ_SIZE/2, r_e * SQ_SIZE + SQ_SIZE/2), SQ_SIZE/8)
            else:
                # draw triangles in the corners for captures
                draw_triangles(screen, highl_color, move.end_sq, 0.2)
                
            # highlight valid square on mouse over
            mouse_sq = get_square(pygame.mouse.get_pos())
            if mouse_sq == move.end_sq:
                s_m = pygame.Surface((SQ_SIZE, SQ_SIZE))
                s_m.fill(HIGHLIGHT_COLORS[(mouse_sq[1] + mouse_sq[0]) % 2])
                screen.blit(s_m, (mouse_sq[1] * SQ_SIZE, mouse_sq[0] * SQ_SIZE))
    
def highlight_last_move(gs:GameState, screen: pygame.display):
    '''Highlights last played move'''
    
    # highlight last move
    if gs.move_log:
        last_move = gs.move_log[-1]
        for r, c in (last_move.start_sq, last_move.end_sq):
            # color = LAST_MOVE_COLORS[(r + c) % 2]
            color = LAST_MOVE_COLOR
            s_lm = pygame.Surface((SQ_SIZE, SQ_SIZE))
            s_lm.fill(color)
            s_lm.set_alpha(160)
            screen.blit(s_lm, (c * SQ_SIZE, r * SQ_SIZE))
    

def draw_triangles(screen: pygame.display, color: tuple[int, int, int], square: tuple[int, int], scale):
    '''Draws 4 inward right triangles in the corners of the square based on scale'''
    
    r, c = square
    triangles = [(0, 0, 1, 1), (SQ_SIZE - 1, 0, -1, 1), (SQ_SIZE - 1, SQ_SIZE - 1, -1, -1), (0, SQ_SIZE - 1, 1, -1)]
    for t in triangles:
        v1 = (c * SQ_SIZE + t[0], r * SQ_SIZE + t[1])
        v2 = (v1[0] + t[2] * SQ_SIZE * scale, v1[1])
        v3 = (v1[0], v1[1] + t[3] * SQ_SIZE * scale)
        pygame.draw.polygon(screen, color, (v1, v2, v3))

def draw_check(screen: pygame.display, square: tuple[int, int]):
    
    r, c = square
    s = pygame.Surface((SQ_SIZE, SQ_SIZE))
    s.set_alpha(100)
    s.fill(CHECK_COLOR)
    # pygame.draw.circle(s, CHECK_COLOR, (c * SQ_SIZE + SQ_SIZE/2, r * SQ_SIZE + SQ_SIZE/2), SQ_SIZE)
    screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

def animate_move(gs: GameState, screen: pygame.display, move: Move, clock: pygame.time.Clock):
    '''Animate the last played move'''
       
    dr = move.end_row - move.start_row
    dc = move.end_col - move.start_col
    frames_per_sq = 1 # how often to draw new state
    frames_count = (abs(dr) + abs(dc))*frames_per_sq # total frames per animation
    

    for frame in range(frames_count + 1):
        r, c = (move.start_row + dr * frame / frames_count, move.start_col + dc * frame / frames_count) # piece position each frame        
        
        # redraw board
        draw_board(screen)
        draw_pieces(gs, screen)
        
        # erase piece from starting and ending squares
        end_color = COLORS[(move.end_row + move.end_col) % 2]
        end_square = pygame.Surface((SQ_SIZE, SQ_SIZE))
        end_square.fill(end_color)
        screen.blit(end_square, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))
        
        start_color = COLORS[(move.start_row + move.start_col) % 2]
        start_square = pygame.Surface((SQ_SIZE, SQ_SIZE))
        start_square.fill(start_color)
        screen.blit(start_square, (move.start_col * SQ_SIZE, move.start_row * SQ_SIZE))
        
        # draw back captured piece
        if move.piece_captured != '--':
            screen.blit(IMAGES[move.piece_captured], (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))
            
        # draw moving piece
        screen.blit(IMAGES[move.piece_moved], (c * SQ_SIZE, r * SQ_SIZE))
        
        # update screen
        pygame.display.flip()
        clock.tick(FPS)

def draw_end_text(screen: pygame.display, text: str):
    '''Displays end text'''

    main_font = pygame.font.SysFont('Cambria Math', 55, True, False)
    main_text = main_font.render(text, True, pygame.Color('Black'))
    main_text_outl = add_outline_to_image(main_text, 2, (255,255,255))
    text_location = ((WIDTH - main_text_outl.get_width()) / 2, (HEIGHT - main_text_outl.get_height()) / 2)
    screen.blit(main_text_outl, text_location)
    
    second_font = pygame.font.SysFont('Cambria Math', 25, True, False)
    reset_text = second_font.render('R to reset', True, pygame.Color('Black'))
    reset_text_outl = add_outline_to_image(reset_text, 2, (255,255,255))
    text_location = ((WIDTH - reset_text_outl.get_width()) / 2, (HEIGHT - reset_text_outl.get_height() + main_text_outl.get_height()) / 2)
    screen.blit(reset_text_outl, text_location)    

def add_outline_to_image(image: pygame.Surface, thickness: int, color: tuple, color_key: tuple = (255, 0, 255)) -> pygame.Surface:
    '''Adds scuffed outline to image or text'''
    
    mask = pygame.mask.from_surface(image)
    mask_surf = mask.to_surface(setcolor=color, unsetcolor=None)
    mask_surf.set_colorkey(color_key)

    new_img = pygame.Surface((image.get_width() + thickness, image.get_height() + thickness))
    new_img.fill(color_key)
    new_img.set_colorkey(color_key)

    for i in -thickness, thickness:
        new_img.blit(mask_surf, (i + thickness, thickness))
        new_img.blit(mask_surf, (thickness, i + thickness))
    new_img.blit(image, (thickness, thickness))
    return new_img


def main():   
    
    clock = pygame.time.Clock()   
    screen = pygame.display.set_mode(SIZE)
    curr_state = GameState()
    valid_moves = curr_state.get_valid_moves()
    move_made = False
    promotion = False
    get_notation = False
    game_over = False
    run = True
    clicked_piece = '--'
    player_color = 'w'
    clicked_sqs = [] # keep track of initial and target squares
    is_lmb_pressed = False
    player_one = True # True if human is playing white, False if AI is playing white
    player_two = True # True if human is playing Black, False if AI is playing Black
    while run:
        human_turn = (curr_state.white_to_move and player_one) or (not curr_state.white_to_move and player_two)
        for event in pygame.event.get():
            if not promotion:
                # Base screen
                if event.type == pygame.QUIT:
                    # close the game
                    run = False             
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not game_over and human_turn:
                        # LMB pressed
                        lmb_down_pos = get_square(event.pos)
                        clicked_piece = curr_state.get_piece(lmb_down_pos)

                        if clicked_sqs:
                            # 2nd click, already 1 square registered for a move
                            if clicked_piece[0] == player_color: 
                                # clicked same color, replace first registered square
                                if clicked_sqs[0] == lmb_down_pos:
                                    # clicked the same square twice
                                    click_counter = 2 
                                clicked_sqs[0] = lmb_down_pos
                                
                                
                            else:
                                # clicked on empty space or opponent's piece, register 2nd square, try to make a move
                                clicked_sqs.append(lmb_down_pos)
                                move_played = Move(clicked_sqs[0], clicked_sqs[1], curr_state) # register the move
                                for i in range(len(valid_moves)):
                                    if move_played == valid_moves[i]: # testing if move is valid
                                        update_move(move_played, valid_moves[i])
                                        if move_played.is_promotion:
                                            promotion = True # move to promotion branch
                                            animate_move(curr_state, screen, move_played, clock)
                                            play_sound(move_played)
                                            promotion_sqs = get_promotion_squares(move_played.end_sq) # generate squares and pieces for promotion screen
                                            curr_state.remove_piece(move_played.start_sq) # remove pawn for promotion screen (for visual purposes)
                                        else:
                                            curr_state.make_move(move_played)
                                            animate_move(curr_state, screen, move_played, clock)
                                            play_sound(move_played)
                                            move_made = True
                                            get_notation = True # to display notation only on new moves, not undo/redo
                                        break
                                clicked_sqs.clear()
                                
                        else:
                            # 1st click, no squares registered for a move
                            if clicked_piece[0] != player_color:
                                # click on empty square or enemy piece - do nothing
                                pass
                            else:
                                # click on a piece, register as 1st square
                                clicked_sqs.append(lmb_down_pos)
                                click_counter = 1 # for deselection if clicked same square twice
                    else:
                        # game is over
                        
                        ...
            
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and clicked_sqs: # if LMB is released and piece is registered
                    lmb_up_pos = get_square(event.pos)
                    
                    if clicked_sqs[0] == lmb_up_pos:
                        # clicked and released on same square
                        if click_counter == 2:
                            # if clicked and released on the same square twice - deselect
                            clicked_sqs.clear()
                                            
                    else: 
                        # clicked and released on different squares, register 2nd square, try to make a move
                        clicked_sqs.append(lmb_up_pos) # add target square
                        move_played = Move(clicked_sqs[0], clicked_sqs[1], curr_state) # register the move
                        for i in range(len(valid_moves)):
                            if move_played == valid_moves[i]: # testing if move is valid
                                update_move(move_played, valid_moves[i])
                                if move_played.is_promotion:
                                    promotion = True # move to promotion branch
                                    promotion_sqs = get_promotion_squares(move_played.end_sq) # generate squares and pieces for promotion screen
                                    curr_state.remove_piece(move_played.start_sq) # remove pawn for promotion screen (for visual purposes)
                                    play_sound(move_played)
                                else:
                                    curr_state.make_move(move_played)
                                    play_sound(move_played)
                                    move_made = True
                                    get_notation = True # to display notation only on new moves, not undo/redo
                                break

                        clicked_sqs.clear()
                        
                elif event.type == pygame.KEYUP and not is_lmb_pressed:
                    if event.key == pygame.K_LEFT:
                        clicked_sqs.clear()
                        curr_state.undo_last_move()
                        move_made = True
                        game_over = False
                    if event.key == pygame.K_RIGHT:
                        clicked_sqs.clear()
                        if curr_state.undo_log:                        
                            curr_state.redo_undone_move()
                            move_made = True
                            animate_move(curr_state, screen, curr_state.move_log[-1], clock) # animate last move if something is in the log
                            play_sound(curr_state.move_log[-1])
                    if event.key == pygame.K_r:
                        # completely reset the game
                        curr_state = GameState()
                        valid_moves = curr_state.get_valid_moves()
                        move_made = False
                        clicked_piece = '--'
                        player_color = 'w'
                        clicked_sqs.clear()
                        game_over = False
                        human_turn = (curr_state.white_to_move and player_one) or (not curr_state.white_to_move and player_two)
        
            else:
                # Promotion screen
                if human_turn:
                    if event.type == pygame.QUIT:
                        run = False  
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # LMB pressed
                        clicked_sqs.append(get_square(event.pos)) # remember initial click square
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and clicked_sqs: # LMB is released
                        clicked_sqs.append(get_square(event.pos)) # remember square where button is released
                        if clicked_sqs[1] not in promotion_sqs: # if we don't release in promotion area, revert to move before promoting
                            promotion = False
                            curr_state.add_piece(move_played.start_sq, move_played.piece_moved)
                        elif clicked_sqs[0] == clicked_sqs[1]: # if clicked and released on the same square - choose that piece
                            move_played.promotion_piece = promotion_sqs[clicked_sqs[0]] # assign chosen piece to promote to
                            curr_state.make_move(move_played)
                            move_made = True
                            get_notation = True # to display notation only on new moves, not undo/redo
                            promotion = False

                        clicked_sqs.clear()
            

        
        is_lmb_pressed = pygame.mouse.get_pressed()[0]
        if promotion:
            draw_promotion(curr_state, screen, move_played.end_sq)       
        elif  is_lmb_pressed and not promotion and clicked_sqs: # if mouse is moved with LMB pressed and piece selected, display moving animation, else draw static board
            draw_moving_state(curr_state, screen, valid_moves, clicked_sqs[0])
        else:
            draw_board(screen)
            highlight_last_move(curr_state, screen)
            if clicked_sqs:
                highlight_start_sq(screen, clicked_sqs[0])
                highlight_moves(curr_state, screen, valid_moves, clicked_sqs[0])
            draw_pieces(curr_state, screen)
        # AI moves
        if not game_over and not human_turn:
            # move_played = ChessAI.find_best_move_greedy(curr_state, valid_moves)
            move_played = ChessAI.find_best_move(ChessAI.find_move_negamax_ab_pruning, gs=curr_state, valid_moves=valid_moves, depth=ChessAI.DEPTH)
            
            if move_played is None:
                move_played = ChessAI.find_random_move(valid_moves)
            if move_played.is_promotion:
                move_played.promotion_piece = player_color + 'Q'
            
            curr_state.make_move(move_played)
            animate_move(curr_state, screen, move_played, clock)
            play_sound(move_played)
            move_made = True
            get_notation = True
        
        # Move completed handling
        if move_made == True:
            move_made = False
            player_color = 'w' if curr_state.white_to_move else 'b'
            valid_moves = curr_state.get_valid_moves()
            if curr_state.checkmate or curr_state.stalemate: # update check, checkmate and stalemate attributes
                move_played.is_checkmate = curr_state.checkmate
                move_played.is_stalemate = curr_state.stalemate
                game_over = True
            elif curr_state.in_check():
                move_played.is_check = True

                # for i in range(len(curr_state.board)):
                #     for j in range(len(curr_state.board[0])):
                #         if curr_state.board[i][j] == player_color + 'K':
                #             r, c = i, j
                #             break
                # print(r, c)
                # draw_check(screen, (r, c))           
            if get_notation:
                if not curr_state.white_to_move: # notate white's move
                    print(str(curr_state.fullmoves) + '. ' + move_played.get_chess_notation(), end=' ')
                else:
                    print(move_played.get_chess_notation())
                get_notation = False
        
        # End of the game
        if game_over:
            if curr_state.checkmate:
                if player_color == 'w':
                    draw_end_text(screen, 'Black won')
                else:
                    draw_end_text(screen, 'White won')
            elif curr_state.stalemate:
                draw_end_text(screen, 'Draw')
                    
        
        clock.tick(FPS)
        pygame.display.flip()
   
        
        
if __name__ == "__main__": 
    SIZE = WIDTH, HEIGHT = 960, 960 # size of the board in pixels
    DIMENSIONS = 8 # number of square in a row/column
    SQ_SIZE = HEIGHT // DIMENSIONS
    COLORS = [(214, 228, 229), (73, 113, 116)] # light squares, dark squares
    HIGHLIGHT_COLORS = [(222, 178, 164), (136, 107, 95)] # highlight for light and dark squares
    LAST_MOVE_COLOR = (242, 211, 136)
    CHECK_COLOR = (255, 100, 100)
    IMAGES = {}
    SOUNDS = {}
    TRANSPARENT_IMAGES = {}
    FPS = 150
    
    pygame.init()
    load_images_svg()
    load_sounds()
    main()
    

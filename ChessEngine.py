import copy

class GameState():
    '''
    Class provides information on current position in the chess game:
     - state of the board
     - move log
    '''
    def __init__(self):
        self.board = [
            ['bR','bN','bB','bQ','bK','bB','bN','bR'],            
            ['bP','bP','bP','bP','bP','bP','bP','bP'],
            ['--','--','--','--','--','--','--','--'],
            ['--','--','--','--','--','--','--','--'],
            ['--','--','--','--','--','--','--','--'],
            ['--','--','--','--','--','--','--','--'],
            ['wP','wP','wP','wP','wP','wP','wP','wP'],
            ['wR','wN','wB','wQ','wK','wB','wN','wR']]     
        
        self.move_functions = {'P': self.get_pawn_moves,
                               'R': self.get_rook_moves,
                               'N': self.get_knight_moves,
                               'B': self.get_bishop_moves,
                               'Q': self.get_queen_moves,
                               'K': self.get_king_moves
                                }
        
        self.white_to_move = True
        self.move_log = []
        self.undo_log = []
        self.checkmate = False
        self.stalemate = False
        self.enpassant_possible = () # track square (row, col) that can be taken en passant, if exists
        self.castle_rights = (True, True, True, True) # white queen side, white king side, black queen side, black king side
        self.castle_rights_log = [self.castle_rights]
        self.fullmoves = 1 # for notation, increments after black's move
        self.halfmoves = 0 # half moves without captures
        self.halfmove_log = [0]
        
        
    def get_piece(self, square: tuple[int, int]) -> str:
        '''Fetches which piece is located on the specified square, returns '--' if empty'''
        
        return self.board[square[0]][square[1]]
    
    def remove_piece(self, square: tuple[int, int]) -> None:
        '''Updates specified board square with the "empty" notation ('--') replacing what is currently there'''
        
        self.board[square[0]][square[1]] = '--'
        
    def add_piece(self, square: tuple[int, int], piece: str) -> None:
        '''Updates specified board square with specified piece replacing what is currently there'''
        
        self.board[square[0]][square[1]] = piece
                
    def make_move(self, move) -> None:
        '''
        Updates the board to reflect move specified in the passed "Move" class:
         - sets initial square to '--'
         - sets target square to the moved piece/promotion piece
         - logs the move
         - updates turn order
        '''
        self.remove_piece(move.start_sq)
        if move.is_promotion:
            self.add_piece(move.end_sq,move.promotion_piece)
        else:
            self.add_piece(move.end_sq, move.piece_moved)
        if move.is_enpassant:
            self.remove_piece((move.start_row, move.end_col))    
        if move.is_castling:
            if move.start_col > move.end_col: # queen side castle
                self.remove_piece((move.start_row, 0))
                self.add_piece((move.start_row, move.end_col + 1), move.piece_moved[0] + 'R')
            else: # king side castle
                self.remove_piece((move.start_row, len(self.board[0]) - 1))
                self.add_piece((move.start_row, move.end_col - 1), move.piece_moved[0] + 'R')
                
            
        self.move_log.append(move) # save move to the log so we can undo
        self.undo_log.clear()
        self.white_to_move = not self.white_to_move # switch turns
        
        # en passant
        if move.piece_moved[1] == 'P' and abs(move.end_row - move.start_row) == 2: # if pawn moved 2 squares update en passant attr
            self.enpassant_possible = ((move.end_row + move.start_row)//2, move.start_col)
        else:
            self.enpassant_possible = ()
        
        # castle rights
        wqs, wks, bqs, bks = self.castle_rights
        # no castling if any pieces move
        if move.piece_moved == 'wK':
            wqs = False
            wks = False
        elif move.piece_moved == 'bK':
            bqs = False
            bks = False
        elif move.piece_moved == 'wR':
            if wqs and move.start_sq == (len(self.board) - 1, 0): # white queen side rook
                wqs = False
            elif wks and move.start_sq == (len(self.board) - 1, len(self.board[0]) - 1): # white king side rook
                wks = False
        elif move.piece_moved == 'bR':
            if bqs and move.start_sq == (0, 0): # black queen side rook
                bqs = False
            elif bks and move.start_sq == (0, len(self.board[0]) - 1): # black king side rook    
                bks = False
                
        # no castling if rooks are captured      
        if move.piece_captured == 'wR':
            if move.end_sq == (len(self.board) - 1, 0):
                wqs = False
            elif move.end_sq == (len(self.board) - 1, len(self.board[0]) - 1):
                wks = False
        elif move.piece_captured == 'bR':
            if move.end_sq == (0, 0):
                bqs = False
            if move.end_sq == (0, len(self.board[0]) - 1):
                bks = False
        self.castle_rights = (wqs, wks, bqs, bks)
        self.castle_rights_log.append(self.castle_rights)
         
        # update move number
        if self.white_to_move:
            self.fullmoves += 1
        
        # update consecutive halfmoves without captures/pawn moves for draw
        if move.piece_captured == '--' and not move.piece_moved.endswith('P'):
            self.halfmoves += 1
        else:
            self.halfmove_log.append(self.halfmoves) # log for undoing moves
            self.halfmoves = 0
        
        # draw
        if self.halfmoves == 50:
            self.stalemate = True
        
        
    def undo_last_move(self) -> None:
        '''Rolls back last played move'''
        
        if len(self.move_log) == 0: # if no moves in log do nothing
            return
        move = self.move_log.pop()
        self.undo_log.append(move)
        self.add_piece(move.start_sq, move.piece_moved)
        
        if move.is_enpassant:
            self.remove_piece(move.end_sq)
            self.add_piece((move.start_row, move.end_col), move.piece_captured) # add back captured pawn if en passant
        else:
            self.add_piece(move.end_sq, move.piece_captured)
        
        if move.is_castling:
            if move.start_col > move.end_col: # queen side castle
                self.remove_piece((move.start_row, move.end_col + 1))
                self.add_piece((move.start_row, 0), move.piece_moved[0] + 'R')
            else: # king side castle
                self.remove_piece((move.start_row, move.end_col - 1))                
                self.add_piece((move.start_row, len(self.board[0]) - 1), move.piece_moved[0] + 'R')
        
        self.white_to_move = not self.white_to_move # switch turns
        
        # en passant
        if self.move_log: # if something is left in the log, check if en passant was possible last turn
            prev_move = self.move_log[-1]
            if prev_move.piece_moved[1] == 'P' and abs(prev_move.end_row - prev_move.start_row) == 2:
                self.enpassant_possible = ((prev_move.end_row + prev_move.start_row)//2, prev_move.start_col)
            else:
                self.enpassant_possible = ()
        else:
            self.enpassant_possible = ()
            
        # castling rights
        self.castle_rights_log.pop()
        self.castle_rights = self.castle_rights_log[-1]
        
        # checkmate/stalemate
        self.stalemate = False
        self.checkmate = False
        
        # update move number
        if not self.white_to_move:
            self.fullmoves -= 1
            
        # update halfmoves
        if self.halfmoves > 0:
            self.halfmoves -= 1
        else:
            self.halfmoves = self.halfmove_log.pop()
        
        
        
    def redo_undone_move(self) -> None:
        '''Replays last cancelled move'''
        
        if len(self.undo_log) == 0: # if no moves in log do nothing
            return
        move = self.undo_log.pop()
        self.move_log.append(move)
        self.remove_piece(move.start_sq)
        
        if move.is_promotion:
            self.add_piece(move.end_sq,move.promotion_piece)
        else:
            self.add_piece(move.end_sq, move.piece_moved)
        
        if move.is_enpassant:
            self.remove_piece((move.start_row, move.end_col)) # remove captured pawn if en passant
        
        if move.is_castling:
            if move.start_col > move.end_col: # queen side castle
                self.remove_piece((move.start_row, 0))
                self.add_piece((move.start_row, move.end_col + 1), move.piece_moved[0] + 'R')
            else: # king side castle
                self.remove_piece((move.start_row, len(self.board[0]) - 1))
                self.add_piece((move.start_row, move.end_col - 1), move.piece_moved[0] + 'R')
        
        self.white_to_move = not self.white_to_move # switch turns

        # en passant       
        if move.piece_moved[1] == 'P' and abs(move.end_row - move.start_row) == 2: # if pawn moved 2 squares update en passant attr
            self.enpassant_possible = ((move.end_row + move.start_row)//2, move.start_col)
        else:
            self.enpassant_possible = ()
            
        # castle rights
        wqs, wks, bqs, bks = self.castle_rights 
        # no castling if any pieces move
        if move.piece_moved == 'wK':
            wqs = False
            wks = False
        elif move.piece_moved == 'bK':
            bqs = False
            bks = False
        elif move.piece_moved == 'wR':
            if wqs and move.start_sq == (len(self.board) - 1, 0): # white queen side rook
                wqs = False
            elif wks and move.start_sq == (len(self.board) - 1, len(self.board[0]) - 1): # white king side rook
                wks = False
        elif move.piece_moved == 'bR':
            if bqs and move.start_sq == (0, 0): # black queen side rook
                bqs = False
            elif bks and move.start_sq == (0, len(self.board[0]) - 1): # black king side rook    
                bks = False
        
        # no castling if rooks are captured      
        if move.piece_captured == 'wR':
            if move.end_sq == (len(self.board) - 1, 0):
                wqs = False
            elif move.end_sq == (len(self.board) - 1, len(self.board[0]) - 1):
                wks = False
        elif move.piece_captured == 'bR':
            if move.end_sq == (0, 0):
                bqs = False
            if move.end_sq == (0, len(self.board[0]) - 1):
                bks = False      
        self.castle_rights = (wqs, wks, bqs, bks)
        self.castle_rights_log.append(self.castle_rights)
        
        # update move number
        if self.white_to_move:
            self.fullmoves += 1
        
        # update consecutive halfmoves
        if move.piece_captured == '--' and not move.piece_moved.endswith('P'):
            self.halfmoves += 1
        else:
            self.halfmove_log.append(self.halfmoves) # log for undoing moves
            self.halfmoves = 0
        
        # draw
        if self.halfmoves == 50:
            self.stalemate = True
            
    def get_pawn_moves(self, r: int, c: int) -> list:
        '''Return all possible moves for a pawn based on position and color (not considering opening king checks)'''
        
        pawn_moves = []
        if self.white_to_move:
            d = -1
            opp_color = 'b'
            prom_row = 0
        else:
            d = 1
            opp_color = 'w'
            prom_row = len(self.board) - 1

        if r != prom_row: # to avoid index out of range, pawns can't be on edge row
            if  c > 0 and self.board[r + d * 1][c - 1].startswith(opp_color): # take to the left
                if r + d * 1 == prom_row:               
                    pawn_moves.append(Move((r, c), (r + d * 1, c - 1), self, is_promotion=True)) # take to the left
                else:
                    pawn_moves.append(Move((r, c), (r + d * 1, c - 1), self))
            if c < len(self.board[0]) - 1 and self.board[r + d * 1][c + 1].startswith(opp_color): # take to the right
                if r + d * 1 == prom_row:             
                    pawn_moves.append(Move((r, c), (r + d * 1, c + 1), self, is_promotion=True))
                else:
                    pawn_moves.append(Move((r, c), (r + d * 1, c + 1), self))
        
            if self.enpassant_possible: 
                ep_row, ep_col = self.enpassant_possible
                if r == ep_row - d * 1 and (c == ep_col - 1 or c == ep_col + 1):
                    pawn_moves.append(Move((r, c), (ep_row, ep_col), self, is_enpassant=True)) # en passant
                    
            if self.board[r + d * 1] [c] == '--': 
                if r + d * 1 == prom_row:   
                    pawn_moves.append(Move((r, c), (r + d * 1, c), self, is_promotion=True)) # move forward one square
                else:
                    pawn_moves.append(Move((r, c), (r + d * 1, c), self)) # move forward one square
                if r == (len(self.board) - 1) - prom_row + d * 1 and self.board[r + d * 2][c] == '--': # first condition checking if pawn is on starting row (1 for black, 6 for white)
                    pawn_moves.append(Move((r, c), (r + d * 2, c), self)) # move forward 2 squares
        
        return pawn_moves
        
    def get_rook_moves(self, r: int, c: int) -> list:
        '''Return all possible moves for a rook based on position and color (not considering opening king checks)'''
        
        rook_moves = []
        my_color = self.get_piece((r, c))[0] # get color of moving rook
        move_vectors = [(-1, 0), (0, 1), (1, 0), (0, -1)] # possible move directions
        
        for v in move_vectors:
            for i in range(1, 8):
                row = r + v[0] * i
                col = c + v[1] * i
                if (row < 0) or (row >= len(self.board)) or (col < 0) or (col >= len(self.board[0])): # out of board bounds
                    break  
                color = self.get_piece((row, col))[0]
                if color == my_color: # stop if we reach same colored piece
                    break
                rook_moves.append(Move((r, c), (row, col), self))
                if color != '-': # stop if we reach opposite colored piece but add this cell
                    break    
        return rook_moves
    
    def get_knight_moves(self, r: int, c: int) -> list:
        '''Return all possible moves for a knight based on position and color (not considering opening king checks)'''
        
        knight_moves = []
        my_color = self.get_piece((r, c))[0] # get color of moving knight
        move_vectors = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)] # possible move directions
        
        for v in move_vectors:
            row = r + v[0]
            col = c + v[1]
            if (row < 0) or (row >= len(self.board)) or (col < 0) or (col >= len(self.board[0])): # out of board bounds
                continue  
            color = self.get_piece((row, col))[0]
            if color != my_color: # stop if we reach same colored piece
                knight_moves.append(Move((r, c), (row, col), self))

        return knight_moves
        
    def get_bishop_moves(self, r: int, c: int) -> list:
        '''Return all possible moves for a bishop based on position and color (not considering opening king checks)'''
        
        bishop_moves = []
        my_color = self.get_piece((r, c))[0] # get color of moving bishop
        move_vectors = [(-1, -1), (-1, 1), (1, -1), (1, 1)] # possible move directions
        
        for v in move_vectors:
            for i in range(1, 8):
                row = r + v[0] * i
                col = c + v[1] * i
                if (row < 0) or (row >= len(self.board)) or (col < 0) or (col >= len(self.board[0])): # out of board bounds
                    break  
                color = self.get_piece((row, col))[0]
                if color == my_color: # stop if we reach same colored piece
                    break
                bishop_moves.append(Move((r, c), (row, col), self))
                if color != '-': # stop if we reach opposite colored piece but add this cell
                    break    
        return bishop_moves

    def get_queen_moves(self, r: int, c: int) -> list:
        '''Return all possible moves for a queen based on position and color (not considering opening king checks)'''
        
        queen_moves = self.get_bishop_moves(r, c) + self.get_rook_moves(r, c)
        return queen_moves        

    def get_king_moves(self, r: int, c: int) -> list:
        '''Return all possible moves for a king based on position and color (not considering opening king checks)'''
        
        king_moves = []
        my_color = self.get_piece((r, c))[0] # get color of moving king
        move_vectors = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (0, 1), (1, 0), (0, -1)] # possible move directions
        
        for v in move_vectors:
            row = r + v[0]
            col = c + v[1]
            if (row < 0) or (row >= len(self.board)) or (col < 0) or (col >= len(self.board[0])): # out of board bounds
                continue  
            color = self.get_piece((row, col))[0]
            if color != my_color: # stop if we reach same colored piece
                king_moves.append(Move((r, c), (row, col), self))

        king_moves.extend(self.get_castle_moves(r, c, my_color)) # add castling
        
        return king_moves
    
    def get_castle_moves(self, r, c, my_color) -> list:
        '''Generates possible castling moves'''
        
        castle_moves = []
        
        if self.in_check():
            return castle_moves # can't castle if in check
        
        if (my_color == 'w' and self.castle_rights[0]) or (my_color == 'b' and self.castle_rights[2]): # can only castle if you haven't lost castling rights
            castle_moves.extend(self.get_qs_castle_moves(r, c, my_color)) 
                  
        if (my_color == 'w' and self.castle_rights[1]) or (my_color == 'b' and self.castle_rights[3]): # can only castle if you haven't lost castling rights
            castle_moves.extend(self.get_ks_castle_moves(r, c, my_color))                    
        
        return castle_moves 
    
    def get_ks_castle_moves(self, r, c, my_color) -> list:
        
        ks_castle_moves = []
        
        if self.board[r][c + 1] == '--' and self.board[r][c + 2] == '--': # check that space is empty between king and rook    
            # only checking that intermediate square is in check, because final position is checked in get_valid_moves
            self.remove_piece((r, c)) 
            self.add_piece((r, c + 1), my_color + 'K') # moving king 1 square over
            in_check = self.in_check()
            self.remove_piece((r, c + 1))
            self.add_piece((r, c), my_color + 'K') # reverting position
            if not in_check:
                ks_castle_moves.append(Move((r, c), (r, c + 2), self, is_castling=True))
            
        return ks_castle_moves
      
    def get_qs_castle_moves(self, r, c, my_color) -> list:
        
        qs_castle_moves = []
        
        if self.board[r][c - 1] == '--' and self.board[r][c - 2] == '--' and self.board[r][c - 3] == '--': # check that space is empty between king and rook
            # only checking that intermediate square is in check, because final position is checked in get_valid_moves
            self.remove_piece((r, c)) 
            self.add_piece((r, c - 1), my_color + 'K') # moving king 1 square over
            in_check = self.in_check()
            self.remove_piece((r, c - 1))
            self.add_piece((r, c), my_color + 'K') # reverting position
            if not in_check:
                qs_castle_moves.append(Move((r, c), (r, c - 2), self, is_castling=True))
        
        return qs_castle_moves
               
    def get_all_moves(self) -> list:
        '''All moves in current position without considering opening king to checks'''
        # does not include castling, it goes straight to valid moves as checks have already been made
           
        all_moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                colored_piece = self.get_piece((r,c))
                if colored_piece == '--': # skip empty cells
                    continue
                color, piece = colored_piece[0], colored_piece[1] # separate color and piece itself
                turn = 'w' if self.white_to_move else 'b'
                if color == turn: # only process cells with relevant color of pieces
                    moves = self.move_functions[piece](r, c) # call appropriate function based on the piece
                    all_moves.extend(moves)                               
        return all_moves
    
    def get_valid_moves(self) -> list:
        '''All available moves in current position that are allowed by chess rules'''
        
        valid_moves = []
        temp_undo_log = copy.deepcopy(self.undo_log) # save undo log state
        temp_stalemate = self.stalemate # save stalemate state
        
        for move in self.get_all_moves(): # go through all possible moves
            self.make_move(move) # make a test move
            self.white_to_move = not self.white_to_move # switch turn back to original player
            if not self.in_check():
                valid_moves.append(move)
            self.white_to_move = not self.white_to_move # switch turns back before undoing move 
            self.undo_last_move() # revert test move
                
        self.undo_log = temp_undo_log # restore undo log
        self.stalemate = temp_stalemate # restore stalemate
        
        if len(valid_moves) == 0: # if no moves - either it's checkmate or stalemate
            if self.in_check() == True:
                self.checkmate = True
            else:
                self.stalemate = True
                                
        return valid_moves
              
    def in_check(self):
        ''' Validating check without generating opponent's moves'''
        
        if self.white_to_move:
            my_color = 'w'
            opp_color = 'b'
            for i in range(len(self.board)): 
                for j in range(len(self.board[0])):
                    if self.board[i][j] == 'wK': # finding white king square
                        r, c = i, j
                        break

        else:
            my_color = 'b'
            opp_color = 'w'
            for i in range(len(self.board)):
                for j in range(len(self.board[0])):
                    if self.board[i][j] == 'bK': # finding black king square
                        r, c = i, j
                        break            

        
        move_vectors = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (0, 1), (1, 0), (0, -1)]
        knight_moves = [(-1, -2), (-1, 2), (1, -2), (1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
        
        for j, v in enumerate(move_vectors):
            for i in range(1, 8):
                row = r + v[0] * i
                col = c + v[1] * i
                if (row < 0) or (row >= len(self.board)) or (col < 0) or (col >= len(self.board[0])): # out of board bounds
                    break  
                colored_piece = self.get_piece((row, col))
                color = colored_piece[0]
                piece = colored_piece[1]
                if color == my_color: # if closest piece is same color - no check
                    break
                if color == opp_color: 
                    if piece =='Q': # queen checks
                        return True
                    elif 0 <= j <= 3 and piece == 'B': # bishop checks
                        return True
                    elif 4 <= j <= 7 and piece == 'R': # rook checks
                        return True
                    elif i == 1 and my_color == 'w' and 0 <= j <= 1 and piece == 'P': # pawn checks for white
                        return True
                    elif i == 1 and my_color == 'b' and 2 <= j <= 3 and piece == 'P': # pawn checks for black
                        return True
                    elif i == 1 and piece == 'K': # not actually a check, but needed so that kings can't walk into each other
                        return True
                    break # stop looking at a vector after finding one opponent's piece
        
        for move in knight_moves:
            row = r + move[0]
            col = c + move[1]
            if (row < 0) or (row >= len(self.board)) or (col < 0) or (col >= len(self.board[0])): # out of board bounds
                continue
            colored_piece = self.get_piece((row, col))
            color = colored_piece[0]
            piece = colored_piece[1]
            if color == opp_color and piece == 'N':
                return True
        
        return False
                         
        

class Move():
    '''
    Class provides information on a chess move in a given game state:
     - starting and destination squares
     - moved and captured piece ('--' if none)
     - chess notation
    '''
    
    ranks_to_rows = {'1': 7, '2': 6, '3': 5, '4': 4, '5': 3, '6': 2, '7': 1, '8': 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}
    
    def __init__(self, start_sq: tuple[int, int], end_sq: tuple[int, int], gs: GameState, is_enpassant = False, is_promotion = False, is_castling = False):
        self.start_sq = start_sq
        self.end_sq = end_sq
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.is_enpassant = is_enpassant
        self.piece_moved = gs.get_piece(self.start_sq)
        if self.is_enpassant:
            self.piece_captured = 'bP' if self.piece_moved == 'wP' else 'wP' # special case for en passant because we're moving to empty square
        else:
            self.piece_captured = gs.get_piece(self.end_sq)
        self.is_promotion = is_promotion
        self.promotion_piece = self.piece_moved[0] + 'Q' # default to queen just in case
        self.is_castling = is_castling
        self.is_checkmate = False
        self.is_stalemate = False
        self.is_check = False
        
    
    def __eq__(self, other):
        '''Overrides the default implementation'''
        
        if isinstance(other, Move):
            return (self.start_sq == other.start_sq) and (self.end_sq == other.end_sq)
        return NotImplemented
    
    def __hash__(self):
        '''Overrides the default implementation'''
        
        return hash(tuple(sorted(self.__dict__.items()))) 
        
    
    def get_chess_notation(self) -> str:
        '''
        Returns move description in FIDE standard algebraic notation
        More info:
        https://en.wikipedia.org/wiki/Algebraic_notation_(chess)#Notation_for_moves
        '''
        
        # !!!ADD IF 2 KNIGHTS/ROOKS CAN TAKE AT THE SAME TIME
        notation = ''
        if self.is_castling:
            if self.start_col > self.end_col:
                notation = 'O-O-O'
            else:
                notation = 'O-O' 
        elif self.piece_moved.endswith('P'): # for pawns
            notation = self.get_rank_file(self.end_sq)
            if self.piece_captured != '--': 
                notation = self.get_rank_file(self.start_sq)[0] + 'x' + notation # add start file + x if captured smth  
            if self.is_promotion:
                notation += '=' + self.promotion_piece[1] # add "=Q" or "=N" for pawn promotion      
        else: # for other pieces
            notation = self.piece_moved[-1] + self.get_rank_file(self.end_sq)
            if self.piece_captured != '--': 
                notation = notation[0] + 'x' + notation[1:] # add x if captured smth
                
        if self.is_checkmate:
            notation += '#'
        elif self.is_stalemate:
            notation += 'S'
        elif self.is_check:
            notation += '+'
        return notation
    
    def get_rank_file(self, square: tuple[int, int]) -> str:
        '''
        Convert indices for specified square from matrix coords to rank and file chess notation (1-8, a-h)
        Examples: (0,1) -> b1; (5,3) -> f5
        '''
        
        return self.cols_to_files[square[1]] + self.rows_to_ranks[square[0]]
        
if __name__ == '__main__':
    test = GameState()
    test_2 = test
    # test_move = Move((6,3), (4,3), test)
    all_moves = test.get_all_moves()
    for move in all_moves:
        print(move.get_chess_notation())
import copy
import random
from ChessEngine import GameState, Move


piece_value = {'K': 0,
               'Q': 9,
               'R': 5,
               'B': 3,
               'N': 3,
               'P': 1}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3


def find_best_move(function, **kwargs) -> Move:
    ''' Helper function to call other specified functions based on chosen algorithm'''
    global best_moves, counter
    
    gs = kwargs['gs']
    
    best_moves = []
    temp_undo_log = copy.deepcopy(gs.undo_log)
    counter = 0
    function(**kwargs)
    # print('Board states evaluated:', counter)
    gs.undo_log = temp_undo_log
    return best_moves[random.randint(0, len(best_moves) - 1)]

def get_material_score(gs: GameState) -> int:
    '''Get material score for current board state. + for white pieces - for black pieces '''
    
    score = 0
    for row in gs.board:
        for square in row:
            if square[0] == 'w':
                score += piece_value[square[1]]
            elif square[0] == 'b':
                score -= piece_value[square[1]]
    return score

def get_board_score(gs: GameState) -> int: 
    '''Assess current board state. + good for white, - good for black'''

    if gs.checkmate:
        if gs.white_to_move:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif gs.stalemate:
        return STALEMATE
    
    score = 0
    for row in gs.board:
        for square in row:
            if square[0] == 'w':
                score += piece_value[square[1]]
            elif square[0] == 'b':
                score -= piece_value[square[1]]
    return score

def find_random_move(gs: GameState, valid_moves: list[Move]) -> Move:
    '''Generate a random move out of all possible moves'''
    return valid_moves[random.randint(0, len(valid_moves) - 1)]

def find_move_greedy(gs: GameState, valid_moves: list[Move]) -> Move:
    '''Find best move our of valid moves based on material score'''
    
    global best_moves
    
    color_multi = 1 if gs.white_to_move else -1
    best_score = float('-inf')
    
    for move in valid_moves:
        if move.is_promotion:
            move.promotion_piece = move.piece_moved[0] + 'Q'
        gs.make_move(move)
        gs.get_valid_moves()
        if gs.checkmate:
            score = CHECKMATE
        elif gs.stalemate:
            score = STALEMATE
        else:
            score = color_multi * get_material_score(gs)
        if score > best_score:
            best_score = score
            best_moves.clear()
            best_moves.append(move)
        elif score == best_score:
            best_moves.append(move) 
        
        gs.undo_last_move()

    return best_moves[random.randint(0, len(best_moves) - 1)]

def find_move_minmax_no_recursion(gs: GameState, valid_moves: list[Move]) -> Move:
    '''Minmax algorithm to find best move (1 move deep)'''
    global best_moves
    
    best_score = float('inf')
    color_multi = 1 if gs.white_to_move else -1

    for move in valid_moves:
        branch_max_score = float('-inf') # set min value that we compare against
        gs.make_move(move)
        opp_moves = gs.get_valid_moves()
        
        # if no moves for opponent, draw or checkmate
        if gs.checkmate:
            branch_max_score = -CHECKMATE
        elif gs.stalemate:
            branch_max_score = STALEMATE
        
        else:
            for opp_move in opp_moves:
                # find max score for opponent after each player move
                if opp_move.is_promotion:
                    opp_move.promotion_piece = opp_move.piece_moved[0] + 'Q' # always promote to queen for ai
                gs.make_move(opp_move)
                gs.get_valid_moves()
                if gs.checkmate:
                    score = CHECKMATE
                elif gs.stalemate:
                    score = STALEMATE
                else:
                    score = - color_multi * get_material_score(gs)
                if score > branch_max_score:
                    branch_max_score = score                            
                gs.undo_last_move()
        
        # find min out of all best opponent scores
        if branch_max_score < best_score:
            best_score = branch_max_score
            best_moves.clear()
            best_moves.append(move)
        elif branch_max_score == best_score:
            best_moves.append(move) 
        
        gs.undo_last_move()  

    return best_moves[random.randint(0, len(best_moves) - 1)]

def find_move_minmax(gs: GameState, valid_moves: list[Move], depth: int) -> int:
    '''Minmax algorithm to find best move for AI based on depth'''
    
    global best_moves
    f = open('move_log.txt', 'a')
    if depth == 0:
        return get_board_score(gs)
    
    if gs.white_to_move:
        max_score = float('-inf')
        for move in valid_moves:
            gs.make_move(move)
            next_moves = gs.get_valid_moves()
            score = find_move_minmax(gs, next_moves, depth - 1)
            if score > max_score:
                max_score = score
                if depth == DEPTH:
                    best_moves.clear()
                    best_moves.append(move)
            elif score == max_score:
                if depth == DEPTH:
                    best_moves.append(move)
            gs.undo_last_move()       
        return max_score

    else:
        min_score = float('inf')
        for move in valid_moves:
            gs.make_move(move)
            next_moves = gs.get_valid_moves()
            score = find_move_minmax(gs, next_moves, depth - 1)
            if score < min_score:
                min_score = score
                if depth == DEPTH:
                    best_moves.clear()
                    best_moves.append(move)
            elif score == min_score:
                if depth == DEPTH:
                    best_moves.append(move)
            gs.undo_last_move()

        return min_score
    
def find_move_negamax(gs: GameState, valid_moves: list[Move], depth: int):
    '''Negamax algorithm to find best move for AI based on depth'''

    
    global best_moves, counter
    
    counter += 1 # number of calls for this function
    color_multi = 1 if gs.white_to_move else -1 # multiplier for negamax to work, so best score is always positive
    
    if depth == 0:
        if gs.checkmate:
            return -color_multi * get_board_score(gs)
        else:
            return color_multi * get_board_score(gs) # base case for recursion

    max_score = float('-inf')
    for move in valid_moves:
        gs.make_move(move)
        next_moves = gs.get_valid_moves()
        # always find max score inside because of -color_multi, and then always find min score outside because of - before function call
        score = -find_move_negamax(gs, next_moves, depth - 1)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                best_moves.clear()
                best_moves.append(move)
        elif score == max_score:
            if depth == DEPTH:
                best_moves.append(move)
        gs.undo_last_move()
    return max_score

def find_move_negamax_ab_pruning(gs: GameState, valid_moves: list[Move], depth: int, alpha: float = float('-inf'), beta: float = float('inf')):
    '''Negamax algorithm with alpha-beta pruning to find best move for AI based on depth'''
    
    global best_moves, counter
    
    counter += 1 # number of calls for this function
    color_multi = 1 if gs.white_to_move else -1 # multiplier for negamax to work, so best score is always positive
    
    if depth == 0:
        if gs.checkmate:
            return -color_multi * get_board_score(gs)
        else:
            return color_multi * get_board_score(gs) # base case for recursion

    # Implement move ordering to increase efficiency
    max_score = float('-inf')
    for move in valid_moves:
        gs.make_move(move)
        next_moves = gs.get_valid_moves()
        # always find max score inside because of -color_multi, and then always find min score outside because of - before function call
        score = -find_move_negamax_ab_pruning(gs, next_moves, depth - 1, -beta, -alpha)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                best_moves.clear()
                best_moves.append(move)
        elif score == max_score:
            if depth == DEPTH:
                best_moves.append(move)
        gs.undo_last_move()
        if max_score > alpha: #pruning happens
            alpha = max_score # new best thus far
        if alpha >= beta:
            break
    return max_score



if __name__ == "__main__":
    new = GameState()
    print(get_material_score(new))
    

#!/usr/bin/env python3
"""
Syncridor - A strategic pathfinding board game

This is an independent implementation inspired by classic strategy board games.
Copyright (c) 2025 synctam@gmail.com

Licensed under the MIT License. See LICENSE file for details.
"""

import pygame
import sys
import math
from enum import Enum
from typing import List, Tuple, Optional
import time

# 初期化
pygame.init()

# 定数
VERSION = "v1.1.0"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 700
BOARD_SIZE = 9
CELL_SIZE = 50
WALL_THICKNESS = 8
BOARD_OFFSET_X = 100
BOARD_OFFSET_Y = 50

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
BLUE = (0, 100, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100)
BROWN = (139, 69, 19)

class GameMode(Enum):
    HUMAN_VS_HUMAN = 1
    HUMAN_VS_AI = 2
    AI_VS_AI = 3

class Player(Enum):
    PLAYER1 = 1
    PLAYER2 = 2

class ActionType(Enum):
    MOVE = 1
    PLACE_WALL = 2

class AIStrategy(Enum):
    AGGRESSIVE = 1    # 積極的に相手を妨害
    DEFENSIVE = 2     # 自分のゴールを優先
    BALANCED = 3      # バランス型（現在の戦略）

class Direction(Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

class Wall:
    def __init__(self, row: int, col: int, is_horizontal: bool, player: Player = None):
        self.row = row
        self.col = col
        self.is_horizontal = is_horizontal
        self.player = player
    
    def __eq__(self, other):
        return (self.row == other.row and 
                self.col == other.col and 
                self.is_horizontal == other.is_horizontal)

class SyncridorGame:
    def __init__(self, mode: GameMode = GameMode.HUMAN_VS_AI):
        self.mode = mode
        self.board_size = BOARD_SIZE
        # AI戦略を設定（プレイヤー1は守備的、プレイヤー2は攻撃的）
        self.player1_strategy = AIStrategy.DEFENSIVE
        self.player2_strategy = AIStrategy.AGGRESSIVE
        self.reset_game()
        
    def reset_game(self):
        # プレイヤー位置
        self.player1_pos = (8, 4)  # 下側中央
        self.player2_pos = (0, 4)  # 上側中央
        
        # 壁の残り数
        self.player1_walls = 10
        self.player2_walls = 10
        
        # 配置された壁のリスト
        self.walls = []
        
        # 現在のプレイヤー
        self.current_player = Player.PLAYER1
        
        # ゲーム状態
        self.game_over = False
        self.winner = None
        
        # AI用の思考時間制御
        self.ai_move_time = 1.0  # 秒
        self.last_ai_move = 0
    
    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < self.board_size and 0 <= col < self.board_size
    
    def can_move_to(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if not self.is_valid_position(to_row, to_col):
            return False
        
        # 直接移動の場合
        if abs(from_row - to_row) + abs(from_col - to_col) == 1:
            return not self.is_wall_blocking(from_pos, to_pos)
        
        # ジャンプ移動の場合
        if abs(from_row - to_row) == 2 and from_col == to_col:
            middle_pos = ((from_row + to_row) // 2, from_col)
            if (middle_pos == self.player1_pos or middle_pos == self.player2_pos):
                return (not self.is_wall_blocking(from_pos, middle_pos) and
                        not self.is_wall_blocking(middle_pos, to_pos))
        
        if abs(from_col - to_col) == 2 and from_row == to_row:
            middle_pos = (from_row, (from_col + to_col) // 2)
            if (middle_pos == self.player1_pos or middle_pos == self.player2_pos):
                return (not self.is_wall_blocking(from_pos, middle_pos) and
                        not self.is_wall_blocking(middle_pos, to_pos))
        
        # 斜めジャンプの場合
        if abs(from_row - to_row) == 1 and abs(from_col - to_col) == 1:
            # 相手プレイヤーが隣接していて、その先に壁がある場合
            other_player_pos = self.player2_pos if self.current_player == Player.PLAYER1 else self.player1_pos
            
            if abs(from_row - other_player_pos[0]) + abs(from_col - other_player_pos[1]) == 1:
                # 相手プレイヤーの先に壁があるかチェック
                dr = other_player_pos[0] - from_row
                dc = other_player_pos[1] - from_col
                straight_jump = (other_player_pos[0] + dr, other_player_pos[1] + dc)
                
                if (not self.is_valid_position(straight_jump[0], straight_jump[1]) or
                    self.is_wall_blocking(other_player_pos, straight_jump)):
                    return not self.is_wall_blocking(from_pos, other_player_pos)
        
        return False
    
    def is_wall_blocking(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        row1, col1 = pos1
        row2, col2 = pos2
        
        for wall in self.walls:
            if wall.is_horizontal:
                # 水平な壁
                if row1 != row2 and min(row1, row2) == wall.row:
                    if wall.col <= min(col1, col2) < wall.col + 2:
                        return True
            else:
                # 垂直な壁
                if col1 != col2 and min(col1, col2) == wall.col:
                    if wall.row <= min(row1, row2) < wall.row + 2:
                        return True
        
        return False
    
    def can_place_wall(self, wall: Wall) -> bool:
        # 範囲チェック
        if wall.is_horizontal:
            if wall.row < 0 or wall.row >= self.board_size - 1 or wall.col < 0 or wall.col >= self.board_size - 1:
                return False
        else:
            if wall.row < 0 or wall.row >= self.board_size - 1 or wall.col < 0 or wall.col >= self.board_size - 1:
                return False
        
        # 既存の壁との重複チェック
        for existing_wall in self.walls:
            if wall == existing_wall:
                return False
            
            # 交差チェック
            if wall.is_horizontal and not existing_wall.is_horizontal:
                if (wall.row == existing_wall.row and 
                    wall.col <= existing_wall.col < wall.col + 2):
                    return False
            elif not wall.is_horizontal and existing_wall.is_horizontal:
                if (existing_wall.row == wall.row and 
                    existing_wall.col <= wall.col < existing_wall.col + 2):
                    return False
            elif wall.is_horizontal == existing_wall.is_horizontal:
                if wall.is_horizontal:
                    if (wall.row == existing_wall.row and 
                        not (wall.col + 2 <= existing_wall.col or existing_wall.col + 2 <= wall.col)):
                        return False
                else:
                    if (wall.col == existing_wall.col and 
                        not (wall.row + 2 <= existing_wall.row or existing_wall.row + 2 <= wall.row)):
                        return False
        
        # パスの存在チェック（簡易版）
        temp_walls = self.walls + [wall]
        return self.has_path_to_goal(self.player1_pos, 0, temp_walls) and \
               self.has_path_to_goal(self.player2_pos, 8, temp_walls)
    
    def has_path_to_goal(self, start_pos: Tuple[int, int], goal_row: int, walls: List[Wall]) -> bool:
        # BFSでゴールへのパスがあるかチェック
        visited = set()
        queue = [start_pos]
        
        while queue:
            pos = queue.pop(0)
            if pos in visited:
                continue
            visited.add(pos)
            
            if pos[0] == goal_row:
                return True
            
            row, col = pos
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (row + dr, col + dc)
                if (self.is_valid_position(new_pos[0], new_pos[1]) and 
                    new_pos not in visited and
                    not self.is_wall_blocking_with_walls(pos, new_pos, walls)):
                    queue.append(new_pos)
        
        return False
    
    def is_wall_blocking_with_walls(self, pos1: Tuple[int, int], pos2: Tuple[int, int], walls: List[Wall]) -> bool:
        row1, col1 = pos1
        row2, col2 = pos2
        
        for wall in walls:
            if wall.is_horizontal:
                if row1 != row2 and min(row1, row2) == wall.row:
                    if wall.col <= min(col1, col2) < wall.col + 2:
                        return True
            else:
                if col1 != col2 and min(col1, col2) == wall.col:
                    if wall.row <= min(row1, row2) < wall.row + 2:
                        return True
        
        return False
    
    def move_player(self, new_pos: Tuple[int, int]) -> bool:
        current_pos = self.player1_pos if self.current_player == Player.PLAYER1 else self.player2_pos
        
        if self.can_move_to(current_pos, new_pos):
            if self.current_player == Player.PLAYER1:
                self.player1_pos = new_pos
                if new_pos[0] == 0:  # ゴールに到達
                    self.game_over = True
                    self.winner = Player.PLAYER1
            else:
                self.player2_pos = new_pos
                if new_pos[0] == 8:  # ゴールに到達
                    self.game_over = True
                    self.winner = Player.PLAYER2
            
            self.current_player = Player.PLAYER2 if self.current_player == Player.PLAYER1 else Player.PLAYER1
            return True
        
        return False
    
    def place_wall(self, wall: Wall) -> bool:
        walls_left = self.player1_walls if self.current_player == Player.PLAYER1 else self.player2_walls
        
        if walls_left > 0 and self.can_place_wall(wall):
            wall.player = self.current_player  # 壁にプレイヤー情報を設定
            self.walls.append(wall)
            if self.current_player == Player.PLAYER1:
                self.player1_walls -= 1
            else:
                self.player2_walls -= 1
            
            self.current_player = Player.PLAYER2 if self.current_player == Player.PLAYER1 else Player.PLAYER1
            return True
        
        return False
    
    def get_valid_moves(self, player_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        valid_moves = []
        row, col = player_pos
        
        # 基本的な4方向
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_pos = (row + dr, col + dc)
            if self.can_move_to(player_pos, new_pos):
                valid_moves.append(new_pos)
        
        # ジャンプ移動
        for dr, dc in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
            new_pos = (row + dr, col + dc)
            if self.can_move_to(player_pos, new_pos):
                valid_moves.append(new_pos)
        
        # 斜めジャンプ
        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_pos = (row + dr, col + dc)
            if self.can_move_to(player_pos, new_pos):
                valid_moves.append(new_pos)
        
        return valid_moves
    
    def get_shortest_path_length(self, start_pos: Tuple[int, int], goal_row: int, walls: List[Wall] = None) -> int:
        """BFSでゴールまでの最短距離を計算"""
        if walls is None:
            walls = self.walls
        
        visited = set()
        queue = [(start_pos, 0)]
        
        while queue:
            pos, distance = queue.pop(0)
            if pos in visited:
                continue
            visited.add(pos)
            
            if pos[0] == goal_row:
                return distance
            
            row, col = pos
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (row + dr, col + dc)
                if (self.is_valid_position(new_pos[0], new_pos[1]) and 
                    new_pos not in visited and
                    not self.is_wall_blocking_with_walls(pos, new_pos, walls)):
                    queue.append((new_pos, distance + 1))
        
        return float('inf')  # パスが見つからない場合
    
    def get_shortest_path(self, start_pos: Tuple[int, int], goal_row: int, walls: List[Wall] = None) -> List[Tuple[int, int]]:
        """BFSでゴールまでの最短経路を取得"""
        if walls is None:
            walls = self.walls
        
        visited = set()
        queue = [(start_pos, [start_pos])]
        
        while queue:
            pos, path = queue.pop(0)
            if pos in visited:
                continue
            visited.add(pos)
            
            if pos[0] == goal_row:
                return path
            
            row, col = pos
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_pos = (row + dr, col + dc)
                if (self.is_valid_position(new_pos[0], new_pos[1]) and 
                    new_pos not in visited and
                    not self.is_wall_blocking_with_walls(pos, new_pos, walls)):
                    queue.append((new_pos, path + [new_pos]))
        
        return []  # パスが見つからない場合
    
    def find_strategic_wall(self) -> Optional[Wall]:
        """戦略的な壁の配置を見つける"""
        current_player_pos = self.player1_pos if self.current_player == Player.PLAYER1 else self.player2_pos
        opponent_pos = self.player2_pos if self.current_player == Player.PLAYER1 else self.player1_pos
        
        current_goal_row = 0 if self.current_player == Player.PLAYER1 else 8
        opponent_goal_row = 8 if self.current_player == Player.PLAYER1 else 0
        
        # 現在の最短距離を計算
        current_distance = self.get_shortest_path_length(current_player_pos, current_goal_row)
        opponent_distance = self.get_shortest_path_length(opponent_pos, opponent_goal_row)
        
        # 相手の最短経路を取得
        opponent_path = self.get_shortest_path(opponent_pos, opponent_goal_row)
        
        best_wall = None
        best_score = -1
        
        # 可能な壁の位置を試す
        for row in range(self.board_size - 1):
            for col in range(self.board_size - 1):
                for is_horizontal in [True, False]:
                    wall = Wall(row, col, is_horizontal)
                    
                    if self.can_place_wall(wall):
                        temp_walls = self.walls + [wall]
                        
                        # 壁を置いた後の距離を計算
                        new_current_distance = self.get_shortest_path_length(current_player_pos, current_goal_row, temp_walls)
                        new_opponent_distance = self.get_shortest_path_length(opponent_pos, opponent_goal_row, temp_walls)
                        
                        # 戦略的スコアを計算
                        opponent_delay = new_opponent_distance - opponent_distance
                        current_delay = new_current_distance - current_distance
                        
                        # 基本スコア：相手を遅らせることを重視、自分の遅延は減点
                        score = opponent_delay * 2 - current_delay
                        
                        # 相手が自分より近い場合、より積極的に妨害
                        if opponent_distance < current_distance:
                            score += opponent_delay * 1.5
                        
                        # 相手の経路を直接妨害する壁にボーナス
                        if len(opponent_path) > 1:
                            path_intersect_bonus = self.calculate_path_intersection_bonus(wall, opponent_path)
                            score += path_intersect_bonus
                        
                        # 垂直壁の戦略的価値を向上
                        if not is_horizontal:
                            # 垂直壁に一般的なボーナスを追加（水平壁との選択確率を均等に）
                            score += 1.0
                            
                            # 相手が横方向に迂回する必要がある場合、垂直壁の価値を上げる
                            if abs(opponent_pos[1] - current_player_pos[1]) > 1:  # 横方向に離れている
                                score += 1.5
                            
                            # 相手がサイドから回り込もうとしている場合
                            if opponent_pos[1] <= 3 or opponent_pos[1] >= 5:  # 端寄りにいる場合
                                score += 2.0
                            
                            # 中央付近での垂直壁は迂回路を増やす効果
                            if 2 <= col <= 5:  # 中央付近
                                score += 1.0
                        
                        if score > best_score:
                            best_score = score
                            best_wall = wall
        
        return best_wall if best_score > 0 else None
    
    def calculate_path_intersection_bonus(self, wall: Wall, opponent_path: List[Tuple[int, int]]) -> float:
        """壁が相手の経路を妨害する度合いを計算"""
        bonus = 0.0
        
        for i in range(len(opponent_path) - 1):
            pos1 = opponent_path[i]
            pos2 = opponent_path[i + 1]
            
            # この壁が経路の移動を妨害するかチェック
            if self.is_wall_blocking_with_walls(pos1, pos2, [wall]):
                # 経路の前半を妨害する場合、より高いボーナス
                path_position = i / len(opponent_path)
                if path_position < 0.5:  # 経路の前半
                    bonus += 2.0
                else:  # 経路の後半
                    bonus += 1.0
        
        return bonus
    
    def ai_make_move_aggressive(self):
        """攻撃的AIの動作 - 相手の妨害を優先"""
        current_pos = self.player2_pos if self.current_player == Player.PLAYER2 else self.player1_pos
        opponent_pos = self.player1_pos if self.current_player == Player.PLAYER2 else self.player2_pos
        goal_row = 8 if self.current_player == Player.PLAYER2 else 0
        opponent_goal_row = 0 if self.current_player == Player.PLAYER2 else 8
        
        current_distance = self.get_shortest_path_length(current_pos, goal_row)
        opponent_distance = self.get_shortest_path_length(opponent_pos, opponent_goal_row)
        walls_left = self.player2_walls if self.current_player == Player.PLAYER2 else self.player1_walls
        
        # 距離差に基づく戦略判断
        distance_diff = current_distance - opponent_distance
        
        # 攻撃的AI：距離が不利または互角なら60%で壁、有利なら20%で壁
        wall_probability = 0.6 if distance_diff >= 0 else 0.2
        should_place_wall = (pygame.time.get_ticks() % 100) < (wall_probability * 100)
        
        if walls_left > 0 and should_place_wall:
            strategic_wall = self.find_strategic_wall()
            if strategic_wall and self.place_wall(strategic_wall):
                return True
        
        # 最短経路に沿って移動
        current_path = self.get_shortest_path(current_pos, goal_row)
        if len(current_path) > 1:
            next_pos = current_path[1]  # 次のステップ
            if self.can_move_to(current_pos, next_pos):
                return self.move_player(next_pos)
        
        # 最短経路が使えない場合、従来の移動方法
        valid_moves = self.get_valid_moves(current_pos)
        if valid_moves:
            best_move = min(valid_moves, key=lambda pos: abs(pos[0] - goal_row))
            return self.move_player(best_move)
        
        return False

    def ai_make_move_defensive(self):
        """守備的AIの動作 - 自分のゴールを優先"""
        current_pos = self.player2_pos if self.current_player == Player.PLAYER2 else self.player1_pos
        opponent_pos = self.player1_pos if self.current_player == Player.PLAYER2 else self.player2_pos
        goal_row = 8 if self.current_player == Player.PLAYER2 else 0
        opponent_goal_row = 0 if self.current_player == Player.PLAYER2 else 8
        
        current_distance = self.get_shortest_path_length(current_pos, goal_row)
        opponent_distance = self.get_shortest_path_length(opponent_pos, opponent_goal_row)
        walls_left = self.player2_walls if self.current_player == Player.PLAYER2 else self.player1_walls
        
        # 距離差に基づく戦略判断
        distance_diff = current_distance - opponent_distance
        
        # 守備的AI：相手が2歩以上近い場合は40%で壁、1歩近い場合は20%、有利な場合は5%で壁
        if distance_diff >= 2:
            wall_probability = 0.4
        elif distance_diff == 1:
            wall_probability = 0.2
        else:
            wall_probability = 0.05
        should_place_wall = (pygame.time.get_ticks() % 100) < (wall_probability * 100)
        
        if walls_left > 0 and should_place_wall:
            strategic_wall = self.find_strategic_wall()
            if strategic_wall and self.place_wall(strategic_wall):
                return True
        
        # 最短経路に沿って移動
        current_path = self.get_shortest_path(current_pos, goal_row)
        if len(current_path) > 1:
            next_pos = current_path[1]  # 次のステップ
            if self.can_move_to(current_pos, next_pos):
                return self.move_player(next_pos)
        
        # 最短経路が使えない場合、従来の移動方法
        valid_moves = self.get_valid_moves(current_pos)
        if valid_moves:
            best_move = min(valid_moves, key=lambda pos: abs(pos[0] - goal_row))
            return self.move_player(best_move)
        
        return False

    def ai_make_move_balanced(self):
        """バランス型AIの動作 - 距離に基づく適応的戦略"""
        current_pos = self.player2_pos if self.current_player == Player.PLAYER2 else self.player1_pos
        opponent_pos = self.player1_pos if self.current_player == Player.PLAYER2 else self.player2_pos
        goal_row = 8 if self.current_player == Player.PLAYER2 else 0
        opponent_goal_row = 0 if self.current_player == Player.PLAYER2 else 8
        
        current_distance = self.get_shortest_path_length(current_pos, goal_row)
        opponent_distance = self.get_shortest_path_length(opponent_pos, opponent_goal_row)
        walls_left = self.player2_walls if self.current_player == Player.PLAYER2 else self.player1_walls
        
        # 距離差に基づく戦略判断
        distance_diff = current_distance - opponent_distance
        
        # バランス型AI：距離差に応じて壁の確率を調整（15-45%）
        if distance_diff >= 1:  # 不利な場合
            wall_probability = 0.45
        elif distance_diff == 0:  # 互角の場合
            wall_probability = 0.3
        else:  # 有利な場合
            wall_probability = 0.15
        
        should_place_wall = (pygame.time.get_ticks() % 100) < (wall_probability * 100)
        
        if walls_left > 0 and should_place_wall:
            strategic_wall = self.find_strategic_wall()
            if strategic_wall and self.place_wall(strategic_wall):
                return True
        
        # 最短経路に沿って移動
        current_path = self.get_shortest_path(current_pos, goal_row)
        if len(current_path) > 1:
            next_pos = current_path[1]  # 次のステップ
            if self.can_move_to(current_pos, next_pos):
                return self.move_player(next_pos)
        
        # 最短経路が使えない場合、従来の移動方法
        valid_moves = self.get_valid_moves(current_pos)
        if valid_moves:
            best_move = min(valid_moves, key=lambda pos: abs(pos[0] - goal_row))
            return self.move_player(best_move)
        
        return False

    def ai_make_move(self):
        """戦略に応じてAIの動作を選択"""
        current_strategy = self.player1_strategy if self.current_player == Player.PLAYER1 else self.player2_strategy
        
        if current_strategy == AIStrategy.AGGRESSIVE:
            return self.ai_make_move_aggressive()
        elif current_strategy == AIStrategy.DEFENSIVE:
            return self.ai_make_move_defensive()
        else:  # BALANCED
            return self.ai_make_move_balanced()

class SyncridorUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Syncridor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.game = None
        self.selected_cell = None
        self.placing_wall = False
        self.wall_horizontal = True
        self.show_menu = True
    
    def draw_menu(self):
        self.screen.fill(WHITE)
        
        title_text = self.font.render("Syncridor", True, BLACK)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        menu_options = [
            ("1. Human vs Human", GameMode.HUMAN_VS_HUMAN),
            ("2. Human vs AI", GameMode.HUMAN_VS_AI),
            ("3. AI vs AI", GameMode.AI_VS_AI)
        ]
        
        for i, (text, mode) in enumerate(menu_options):
            color = BLUE if i == 0 else BLACK
            option_text = self.small_font.render(text, True, color)
            option_rect = option_text.get_rect(center=(WINDOW_WIDTH // 2, 200 + i * 50))
            self.screen.blit(option_text, option_rect)
        
        instruction_text = self.small_font.render("Press 1, 2, or 3 to select game mode", True, GRAY)
        instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, 400))
        self.screen.blit(instruction_text, instruction_rect)
    
    def draw_board(self):
        # ボードの背景
        board_rect = pygame.Rect(BOARD_OFFSET_X, BOARD_OFFSET_Y, 
                                CELL_SIZE * self.game.board_size, 
                                CELL_SIZE * self.game.board_size)
        pygame.draw.rect(self.screen, LIGHT_GRAY, board_rect)
        
        # グリッド線
        for i in range(self.game.board_size + 1):
            # 縦線
            x = BOARD_OFFSET_X + i * CELL_SIZE
            pygame.draw.line(self.screen, BLACK, 
                           (x, BOARD_OFFSET_Y), 
                           (x, BOARD_OFFSET_Y + CELL_SIZE * self.game.board_size))
            # 横線
            y = BOARD_OFFSET_Y + i * CELL_SIZE
            pygame.draw.line(self.screen, BLACK, 
                           (BOARD_OFFSET_X, y), 
                           (BOARD_OFFSET_X + CELL_SIZE * self.game.board_size, y))
        
        # ゴールライン
        goal1_rect = pygame.Rect(BOARD_OFFSET_X, BOARD_OFFSET_Y, 
                                CELL_SIZE * self.game.board_size, CELL_SIZE)
        goal2_rect = pygame.Rect(BOARD_OFFSET_X, BOARD_OFFSET_Y + CELL_SIZE * (self.game.board_size - 1), 
                                CELL_SIZE * self.game.board_size, CELL_SIZE)
        pygame.draw.rect(self.screen, GREEN, goal1_rect, 3)
        pygame.draw.rect(self.screen, BLUE, goal2_rect, 3)
    
    def draw_walls(self):
        for wall in self.game.walls:
            if wall.is_horizontal:
                x = BOARD_OFFSET_X + wall.col * CELL_SIZE
                y = BOARD_OFFSET_Y + (wall.row + 1) * CELL_SIZE - WALL_THICKNESS // 2
                width = CELL_SIZE * 2
                height = WALL_THICKNESS
            else:
                x = BOARD_OFFSET_X + (wall.col + 1) * CELL_SIZE - WALL_THICKNESS // 2
                y = BOARD_OFFSET_Y + wall.row * CELL_SIZE
                width = WALL_THICKNESS
                height = CELL_SIZE * 2
            
            # プレイヤーに応じて壁の色を変更
            wall_color = BROWN  # デフォルト色
            if wall.player == Player.PLAYER1:
                wall_color = BLUE
            elif wall.player == Player.PLAYER2:
                wall_color = RED
            
            pygame.draw.rect(self.screen, wall_color, (x, y, width, height))
    
    def draw_wall_preview(self):
        if not self.placing_wall:
            return
            
        mouse_pos = pygame.mouse.get_pos()
        cell = self.get_cell_from_mouse(mouse_pos)
        
        if cell and 0 <= cell[0] < self.game.board_size - 1 and 0 <= cell[1] < self.game.board_size - 1:
            row, col = cell
            preview_wall = Wall(row, col, self.wall_horizontal)
            
            if self.game.can_place_wall(preview_wall):
                if self.wall_horizontal:
                    x = BOARD_OFFSET_X + col * CELL_SIZE
                    y = BOARD_OFFSET_Y + (row + 1) * CELL_SIZE - WALL_THICKNESS // 2
                    width = CELL_SIZE * 2
                    height = WALL_THICKNESS
                else:
                    x = BOARD_OFFSET_X + (col + 1) * CELL_SIZE - WALL_THICKNESS // 2
                    y = BOARD_OFFSET_Y + row * CELL_SIZE
                    width = WALL_THICKNESS
                    height = CELL_SIZE * 2
                
                # 半透明のプレビュー表示
                if self.game.current_player == Player.PLAYER1:
                    preview_color = (BLUE[0], BLUE[1], BLUE[2], 128)
                else:
                    preview_color = (RED[0], RED[1], RED[2], 128)
                preview_surface = pygame.Surface((width, height), pygame.SRCALPHA)
                preview_surface.fill(preview_color)
                self.screen.blit(preview_surface, (x, y))
    
    def draw_players(self):
        # プレイヤー1 (青)
        row1, col1 = self.game.player1_pos
        x1 = BOARD_OFFSET_X + col1 * CELL_SIZE + CELL_SIZE // 2
        y1 = BOARD_OFFSET_Y + row1 * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, BLUE, (x1, y1), CELL_SIZE // 3)
        
        # プレイヤー2 (赤)
        row2, col2 = self.game.player2_pos
        x2 = BOARD_OFFSET_X + col2 * CELL_SIZE + CELL_SIZE // 2
        y2 = BOARD_OFFSET_Y + row2 * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, RED, (x2, y2), CELL_SIZE // 3)
    
    def draw_ui(self):
        # 現在のプレイヤー表示
        current_text = f"Current Player: {'Blue' if self.game.current_player == Player.PLAYER1 else 'Red'}"
        text_surface = self.small_font.render(current_text, True, BLACK)
        self.screen.blit(text_surface, (10, 10))
        
        # 壁の残り数
        walls1_text = f"Blue Walls: {self.game.player1_walls}"
        walls2_text = f"Red Walls: {self.game.player2_walls}"
        walls1_surface = self.small_font.render(walls1_text, True, BLUE)
        walls2_surface = self.small_font.render(walls2_text, True, RED)
        
        # 壁の向き表示
        if self.placing_wall:
            orientation_text = f"Wall Direction: {'Horizontal' if self.wall_horizontal else 'Vertical'} (Press T to rotate)"
            orientation_surface = self.small_font.render(orientation_text, True, BLACK)
            self.screen.blit(orientation_surface, (10, 35))
        # 壁の残り数の位置を調整
        wall_y_offset = 65 if self.placing_wall else 40
        self.screen.blit(walls1_surface, (10, wall_y_offset))
        self.screen.blit(walls2_surface, (10, wall_y_offset + 30))
        
        # 操作説明
        instructions = [
            "Left click: Move/Select",
            "Right click: Place wall",
            "T: Rotate wall direction",
            "Space: Toggle wall mode",
            "R: Restart game",
            "M: Main menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text_surface = self.small_font.render(instruction, True, BLACK)
            self.screen.blit(text_surface, (WINDOW_WIDTH - 200, 10 + i * 25))
        
        # バージョン表示
        version_text = self.small_font.render(VERSION, True, GRAY)
        self.screen.blit(version_text, (WINDOW_WIDTH - 60, WINDOW_HEIGHT - 25))
        
        # ゲーム終了時
        if self.game.game_over:
            winner_text = f"{'Blue' if self.game.winner == Player.PLAYER1 else 'Red'} Wins!"
            text_surface = self.font.render(winner_text, True, BLACK)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
            pygame.draw.rect(self.screen, WHITE, text_rect.inflate(20, 10))
            self.screen.blit(text_surface, text_rect)
    
    def get_cell_from_mouse(self, mouse_pos):
        x, y = mouse_pos
        col = (x - BOARD_OFFSET_X) // CELL_SIZE
        row = (y - BOARD_OFFSET_Y) // CELL_SIZE
        
        if 0 <= row < self.game.board_size and 0 <= col < self.game.board_size:
            return (row, col)
        return None
    
    def get_wall_from_mouse(self, mouse_pos):
        x, y = mouse_pos
        
        # マウス位置から壁の位置を計算
        rel_x = x - BOARD_OFFSET_X
        rel_y = y - BOARD_OFFSET_Y
        
        if self.wall_horizontal:
            # 水平壁
            col = rel_x // CELL_SIZE
            row = (rel_y - CELL_SIZE // 2) // CELL_SIZE
            if 0 <= row < self.game.board_size - 1 and 0 <= col < self.game.board_size - 1:
                return Wall(row, col, True)
        else:
            # 垂直壁
            col = (rel_x - CELL_SIZE // 2) // CELL_SIZE
            row = rel_y // CELL_SIZE
            if 0 <= row < self.game.board_size - 1 and 0 <= col < self.game.board_size - 1:
                return Wall(row, col, False)
        
        return None
    
    def handle_menu_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.game = SyncridorGame(GameMode.HUMAN_VS_HUMAN)
                self.show_menu = False
            elif event.key == pygame.K_2:
                self.game = SyncridorGame(GameMode.HUMAN_VS_AI)
                self.show_menu = False
            elif event.key == pygame.K_3:
                self.game = SyncridorGame(GameMode.AI_VS_AI)
                self.show_menu = False
    
    def handle_game_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.placing_wall = not self.placing_wall
            elif event.key == pygame.K_t:
                if self.placing_wall:
                    self.wall_horizontal = not self.wall_horizontal
            elif event.key == pygame.K_r:
                self.game.reset_game()
            elif event.key == pygame.K_m:
                self.show_menu = True
                self.game = None
        
        elif event.type == pygame.MOUSEBUTTONDOWN and not self.game.game_over:
            # AIのターンの場合は入力を無視
            if ((self.game.mode == GameMode.HUMAN_VS_AI and self.game.current_player == Player.PLAYER2) or
                self.game.mode == GameMode.AI_VS_AI):
                return
            
            mouse_pos = pygame.mouse.get_pos()
            
            if event.button == 1:  # 左クリック
                if self.placing_wall:
                    # 壁配置モードの場合
                    wall = self.get_wall_from_mouse(mouse_pos)
                    if wall:
                        if self.game.place_wall(wall):
                            self.placing_wall = False  # 配置成功後は壁モードを解除
                else:
                    # 通常の移動
                    cell = self.get_cell_from_mouse(mouse_pos)
                    if cell:
                        self.game.move_player(cell)
            
            elif event.button == 3:  # 右クリック - 壁配置モード切り替え
                self.placing_wall = not self.placing_wall
    
    def update_ai(self):
        current_time = time.time()
        
        # AIのターンかチェック
        should_ai_move = False
        if self.game.mode == GameMode.HUMAN_VS_AI and self.game.current_player == Player.PLAYER2:
            should_ai_move = True
        elif self.game.mode == GameMode.AI_VS_AI:
            should_ai_move = True
        
        if (should_ai_move and not self.game.game_over and 
            current_time - self.game.last_ai_move > self.game.ai_move_time):
            self.game.ai_make_move()
            self.game.last_ai_move = current_time
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.show_menu:
                    self.handle_menu_input(event)
                else:
                    self.handle_game_input(event)
            
            self.screen.fill(WHITE)
            
            if self.show_menu:
                self.draw_menu()
            else:
                if self.game:
                    self.update_ai()
                    self.draw_board()
                    self.draw_walls()
                    self.draw_wall_preview()
                    self.draw_players()
                    self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Syncridor - Strategic Pathfinding Game")
    print("Copyright (c) 2025 synctam@gmail.com")
    print("Licensed under MIT License")
    print("=" * 50)
    
    ui = SyncridorUI()
    ui.run()
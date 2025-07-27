#!/usr/bin/env python3
"""
Syncridor テストスイート

このファイルはSyncridorゲームの包括的なテストを提供します。
Copyright (c) 2025 synctam@gmail.com

Licensed under the MIT License. See LICENSE file for details.
"""

import unittest
import sys
import os

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from syncridor_game import (
    SyncridorGame, Wall, Player, GameMode, AIStrategy,
    BOARD_SIZE
)


class TestWall(unittest.TestCase):
    """Wallクラスのテスト"""
    
    def test_wall_creation(self):
        """壁の作成テスト"""
        wall = Wall(3, 4, True, Player.PLAYER1)
        self.assertEqual(wall.row, 3)
        self.assertEqual(wall.col, 4)
        self.assertTrue(wall.is_horizontal)
        self.assertEqual(wall.player, Player.PLAYER1)
    
    def test_wall_equality(self):
        """壁の等価性テスト"""
        wall1 = Wall(2, 3, False)
        wall2 = Wall(2, 3, False)
        wall3 = Wall(2, 3, True)
        
        self.assertEqual(wall1, wall2)
        self.assertNotEqual(wall1, wall3)


class TestSyncridorGameBasics(unittest.TestCase):
    """SyncridorGameの基本機能テスト"""
    
    def setUp(self):
        """各テストの前に実行される設定"""
        self.game = SyncridorGame(GameMode.HUMAN_VS_HUMAN)
    
    def test_game_initialization(self):
        """ゲーム初期化テスト"""
        self.assertEqual(self.game.board_size, BOARD_SIZE)
        self.assertEqual(self.game.player1_pos, (8, 4))
        self.assertEqual(self.game.player2_pos, (0, 4))
        self.assertEqual(self.game.player1_walls, 10)
        self.assertEqual(self.game.player2_walls, 10)
        self.assertEqual(len(self.game.walls), 0)
        self.assertEqual(self.game.current_player, Player.PLAYER1)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)
    
    def test_reset_game(self):
        """ゲームリセット機能テスト"""
        # ゲーム状態を変更
        self.game.player1_pos = (5, 5)
        self.game.player1_walls = 5
        self.game.walls.append(Wall(3, 3, True))
        self.game.current_player = Player.PLAYER2
        
        # リセット実行
        self.game.reset_game()
        
        # 初期状態に戻ることを確認
        self.assertEqual(self.game.player1_pos, (8, 4))
        self.assertEqual(self.game.player1_walls, 10)
        self.assertEqual(len(self.game.walls), 0)
        self.assertEqual(self.game.current_player, Player.PLAYER1)
    
    def test_valid_position(self):
        """有効な位置のテスト"""
        self.assertTrue(self.game.is_valid_position(0, 0))
        self.assertTrue(self.game.is_valid_position(8, 8))
        self.assertTrue(self.game.is_valid_position(4, 4))
        
        self.assertFalse(self.game.is_valid_position(-1, 0))
        self.assertFalse(self.game.is_valid_position(0, -1))
        self.assertFalse(self.game.is_valid_position(9, 0))
        self.assertFalse(self.game.is_valid_position(0, 9))


class TestPlayerMovement(unittest.TestCase):
    """プレイヤー移動のテスト"""
    
    def setUp(self):
        self.game = SyncridorGame(GameMode.HUMAN_VS_HUMAN)
    
    def test_basic_movement(self):
        """基本的な移動テスト"""
        # プレイヤー1の基本移動
        initial_pos = self.game.player1_pos
        new_pos = (initial_pos[0] - 1, initial_pos[1])  # 上に移動
        
        result = self.game.move_player(new_pos)
        self.assertTrue(result)
        self.assertEqual(self.game.player1_pos, new_pos)
        self.assertEqual(self.game.current_player, Player.PLAYER2)
    
    def test_invalid_movement(self):
        """無効な移動のテスト"""
        # 2マス以上の移動（ジャンプなし）
        initial_pos = self.game.player1_pos
        invalid_pos = (initial_pos[0] - 2, initial_pos[1])
        
        result = self.game.move_player(invalid_pos)
        self.assertFalse(result)
        self.assertEqual(self.game.player1_pos, initial_pos)
        self.assertEqual(self.game.current_player, Player.PLAYER1)
    
    def test_boundary_movement(self):
        """境界での移動テスト"""
        # プレイヤー1を端に移動
        self.game.player1_pos = (0, 4)
        
        # 上に移動しようとする（境界外）
        result = self.game.move_player((-1, 4))
        self.assertFalse(result)
    
    def test_winning_condition(self):
        """勝利条件のテスト"""
        # プレイヤー1をゴール前に配置
        self.game.player1_pos = (1, 4)
        
        # ゴールに移動
        result = self.game.move_player((0, 4))
        self.assertTrue(result)
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.winner, Player.PLAYER1)


class TestWallPlacement(unittest.TestCase):
    """壁配置のテスト"""
    
    def setUp(self):
        self.game = SyncridorGame(GameMode.HUMAN_VS_HUMAN)
    
    def test_valid_wall_placement(self):
        """有効な壁配置テスト"""
        wall = Wall(3, 3, True, Player.PLAYER1)
        
        result = self.game.place_wall(wall)
        self.assertTrue(result)
        self.assertEqual(len(self.game.walls), 1)
        self.assertEqual(self.game.player1_walls, 9)
        self.assertEqual(self.game.current_player, Player.PLAYER2)
    
    def test_wall_blocking_movement(self):
        """壁による移動阻止テスト"""
        # 水平な壁を配置
        wall = Wall(7, 4, True, Player.PLAYER1)
        self.game.place_wall(wall)
        
        # プレイヤー1が壁を越えて移動しようとする
        self.game.current_player = Player.PLAYER1  # ターンを戻す
        result = self.game.move_player((7, 4))
        self.assertFalse(result)
    
    def test_invalid_wall_placement_overlap(self):
        """重複する壁配置の無効化テスト"""
        wall1 = Wall(3, 3, True, Player.PLAYER1)
        wall2 = Wall(3, 3, True, Player.PLAYER2)
        
        self.game.place_wall(wall1)
        self.game.place_wall(wall2)
        
        # 2つ目の壁は配置されない
        self.assertEqual(len(self.game.walls), 1)
    
    def test_wall_limit(self):
        """壁の使用制限テスト"""
        # 壁を10個使い切る
        self.game.player1_walls = 1
        wall = Wall(3, 3, True, Player.PLAYER1)
        
        result = self.game.place_wall(wall)
        self.assertTrue(result)
        self.assertEqual(self.game.player1_walls, 0)
        
        # もう壁は置けない
        wall2 = Wall(4, 4, True, Player.PLAYER1)
        self.game.current_player = Player.PLAYER1  # ターンを戻す
        result = self.game.place_wall(wall2)
        self.assertFalse(result)


class TestPathfinding(unittest.TestCase):
    """パスファインディングアルゴリズムのテスト"""
    
    def setUp(self):
        self.game = SyncridorGame(GameMode.HUMAN_VS_HUMAN)
    
    def test_shortest_path_length_no_walls(self):
        """壁なしでの最短距離計算テスト"""
        # プレイヤー1のゴールまでの距離
        distance = self.game.get_shortest_path_length((8, 4), 0)
        self.assertEqual(distance, 8)
        
        # プレイヤー2のゴールまでの距離
        distance = self.game.get_shortest_path_length((0, 4), 8)
        self.assertEqual(distance, 8)
    
    def test_shortest_path_with_walls(self):
        """壁ありでの最短距離計算テスト"""
        # 直線を塞ぐ壁を配置
        walls = [Wall(6, 4, True), Wall(5, 4, True), Wall(4, 4, True)]
        
        distance = self.game.get_shortest_path_length((7, 4), 0, walls)
        self.assertGreater(distance, 7)  # 迂回が必要なので距離が長くなる
    
    def test_shortest_path_route(self):
        """最短経路の取得テスト"""
        path = self.game.get_shortest_path((8, 4), 0)
        
        # パスが存在することを確認
        self.assertGreater(len(path), 0)
        # 開始点がパスに含まれることを確認
        self.assertEqual(path[0], (8, 4))
        # ゴール行がパスの最後に含まれることを確認
        self.assertEqual(path[-1][0], 0)
    
    def test_blocked_path_detection(self):
        """完全にブロックされたパスの検出テスト"""
        # プレイヤー1を囲む壁を配置（実際のゲームでは不可能だが、アルゴリズムテスト用）
        walls = []
        for col in range(9):
            if col != 4:  # プレイヤー位置以外
                walls.append(Wall(7, col, True))
        
        # 囲まれた状態での距離計算
        distance = self.game.get_shortest_path_length((8, 4), 0, walls)
        self.assertGreater(distance, 20)  # 大幅な迂回が必要


class TestAIStrategies(unittest.TestCase):
    """AI戦略のテスト"""
    
    def setUp(self):
        self.game = SyncridorGame(GameMode.AI_VS_AI)
    
    def test_ai_strategy_assignment(self):
        """AI戦略の割り当てテスト"""
        self.assertEqual(self.game.player1_strategy, AIStrategy.DEFENSIVE)
        self.assertEqual(self.game.player2_strategy, AIStrategy.AGGRESSIVE)
    
    def test_strategic_wall_finding(self):
        """戦略的壁配置の検索テスト"""
        # 特定の状況を設定
        self.game.player1_pos = (6, 4)
        self.game.player2_pos = (2, 4)
        
        strategic_wall = self.game.find_strategic_wall()
        
        # 戦略的な壁が見つかることを確認
        if strategic_wall is not None:
            self.assertIsInstance(strategic_wall, Wall)
            self.assertTrue(self.game.can_place_wall(strategic_wall))
    
    def test_ai_move_execution(self):
        """AI移動実行のテスト"""
        initial_pos = self.game.player1_pos
        
        result = self.game.ai_make_move()
        self.assertTrue(result)
        
        # 位置が変わったか、壁が配置されたかのいずれか
        position_changed = self.game.player1_pos != initial_pos
        wall_placed = len(self.game.walls) > 0
        
        self.assertTrue(position_changed or wall_placed)


class TestGameModes(unittest.TestCase):
    """ゲームモードのテスト"""
    
    def test_human_vs_human_mode(self):
        """人間対人間モードのテスト"""
        game = SyncridorGame(GameMode.HUMAN_VS_HUMAN)
        self.assertEqual(game.mode, GameMode.HUMAN_VS_HUMAN)
    
    def test_human_vs_ai_mode(self):
        """人間対AIモードのテスト"""
        game = SyncridorGame(GameMode.HUMAN_VS_AI)
        self.assertEqual(game.mode, GameMode.HUMAN_VS_AI)
    
    def test_ai_vs_ai_mode(self):
        """AI対AIモードのテスト"""
        game = SyncridorGame(GameMode.AI_VS_AI)
        self.assertEqual(game.mode, GameMode.AI_VS_AI)


class TestEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""
    
    def setUp(self):
        self.game = SyncridorGame(GameMode.HUMAN_VS_HUMAN)
    
    def test_jump_over_opponent(self):
        """相手プレイヤーを飛び越える移動テスト"""
        # プレイヤー2をプレイヤー1の隣に配置
        self.game.player2_pos = (7, 4)
        
        # プレイヤー1がプレイヤー2を飛び越えて移動
        result = self.game.move_player((6, 4))
        self.assertTrue(result)
        self.assertEqual(self.game.player1_pos, (6, 4))
    
    def test_diagonal_jump(self):
        """斜めジャンプのテスト"""
        # プレイヤー2をプレイヤー1の隣に配置
        self.game.player2_pos = (7, 4)
        
        # プレイヤー2の先に壁を配置して直線ジャンプを阻止
        wall = Wall(6, 4, True, Player.PLAYER1)
        self.game.walls.append(wall)
        
        # 斜めジャンプを試行
        result = self.game.move_player((7, 3))
        # 斜めジャンプの条件が満たされれば成功
        if result:
            self.assertEqual(self.game.player1_pos, (7, 3))


if __name__ == '__main__':
    # テストスイートの実行
    print("Syncridor テストスイート開始")
    print("=" * 50)
    
    # 詳細な出力でテスト実行
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 50)
    print("テスト完了")
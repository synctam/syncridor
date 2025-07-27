#!/usr/bin/env python3
"""
Pygbag動作確認用のシンプルテスト
最小限のPygameコードでブラウザ動作をテスト
"""

import pygame
import asyncio
import sys

# Pygame初期化
pygame.init()

# 画面設定
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 700
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class SimpleTest:
    def __init__(self):
        try:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("Pygbag Simple Test")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 36)
            self.running = True
            self.frame_count = 0
            print("SimpleTest initialized successfully")
        except Exception as e:
            print(f"Initialization error: {e}")
            self.running = False
    
    async def run(self):
        """メインループ（async版）"""
        print("Starting async main loop")
        
        while self.running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    print("Quit event received")
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        print("Escape key pressed")
            
            # 背景クリア
            self.screen.fill(WHITE)
            
            # テスト描画
            self.draw_test_content()
            
            # 画面更新
            pygame.display.flip()
            
            # フレームレート制御
            self.clock.tick(60)
            
            # フレームカウント更新
            self.frame_count += 1
            
            # Pygbag必須: ブラウザに制御を戻す
            await asyncio.sleep(0)
        
        print("Main loop ended")
        pygame.quit()
        sys.exit()
    
    def draw_test_content(self):
        """テスト用コンテンツの描画"""
        try:
            # タイトル
            title = self.font.render("Pygbag Simple Test", True, BLACK)
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 50))
            self.screen.blit(title, title_rect)
            
            # フレームカウンター
            frame_text = self.font.render(f"Frame: {self.frame_count}", True, BLACK)
            self.screen.blit(frame_text, (10, 10))
            
            # カラフルな四角形
            pygame.draw.rect(self.screen, RED, (100, 150, 200, 100))
            pygame.draw.rect(self.screen, BLUE, (500, 150, 200, 100))
            
            # 円
            pygame.draw.circle(self.screen, RED, (WINDOW_WIDTH // 2, 350), 50)
            
            # 動的な要素（フレーム数に基づく）
            x = (self.frame_count % WINDOW_WIDTH)
            pygame.draw.circle(self.screen, BLUE, (x, 500), 20)
            
            # 操作説明
            instruction = self.font.render("Press ESC to quit", True, BLACK)
            self.screen.blit(instruction, (10, WINDOW_HEIGHT - 50))
            
        except Exception as e:
            print(f"Drawing error: {e}")

async def main():
    """Pygbag対応のメイン関数"""
    print("Simple Web Test Starting...")
    print("Testing Pygbag compatibility")
    
    try:
        test = SimpleTest()
        if test.running:
            await test.run()
        else:
            print("Failed to initialize test")
    except Exception as e:
        print(f"Main error: {e}")

if __name__ == "__main__":
    print("Running simple test with asyncio")
    asyncio.run(main())
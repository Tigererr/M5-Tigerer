import time
import random
import M5
from M5 import *
import machine

# --- ИНИЦИАЛИЗАЦИЯ ---
M5.begin()
M5.Lcd.setRotation(3)

# --- ЦВЕТА ---
BLACK = 0x000000
WHITE = 0xFFFFFF
YELLOW = 0xFFFF00
ORANGE = 0xFFA500
GREEN = 0x00FF00
CYAN = 0x00FFFF
RED = 0xFF0000
NAVY = 0x000080
GRAY = 0x808080
MAGENTA = 0xFF00FF
DARK_GRAY = 0x222222

# --- СОСТОЯНИЯ ---
BOOT, MENU, GAME_TETRIS, GAME_SHARK, GAME_SLOTS, SENSORS, SETTINGS = range(7)
current_state = MENU

# --- НАСТРОЙКИ ---
brightness = 150
screen_timeout = 15
screen_always_on = False
show_boot_tiger = True
last_activity_time = time.ticks_ms()
is_screen_off = False
settings_index = 0
settings_total_items = 5

# --- МЕНЮ ---
menu_index = 0
menu_items = ["TETRIS", "SHARK", "SLOTS", "SENSORS", "CONFIG"]
menu_icons = ["T", "S", "$", "G", "*"]

# --- ТЕТРИС (глобальные) ---
tetris_init = False
pieceX, pieceY = 4, 0
last_pieceX, last_pieceY = 4, 0
score_tetris = 0
tetris_fall_counter = 0
TETRIS_FALL_DELAY = 1
grid = [[0] * 10 for _ in range(15)]

# --- АКУЛА (глобальные) ---
shark_init = False
fishY, sharkX, sharkY, score_shark, shark_alive = 60, 240, 60, 0, True
fish_lastY = 60
shark_lastX = 240
shark_move_counter = 0
SHARK_MOVE_DELAY = 3

# --- СЛОТЫ (глобальные) ---
slots_init = False
slot1, slot2, slot3 = 0, 0, 0
slot_symbols = ["7", "X", "$", "#"]
spinning = False
slot_score = 100
slot_pause_until = 0

# --- ДАТЧИКИ ---
sensors_init = False
last_batt_level = -1

# --- ВСПОМОГАТЕЛЬНЫЕ ---
_batt_history = []


def get_battery_level():
    global _batt_history
    try:
        raw = M5.Power.getBatteryLevel()
    except:
        return -1

    if raw < 0:
        return -1

    _batt_history.append(raw)
    if len(_batt_history) > 5:
        _batt_history.pop(0)

    total = 0
    for v in _batt_history:
        total += v
    return total // len(_batt_history)


def is_btn_c_pressed():
    try:
        if hasattr(M5, 'BtnPWR'):
            return M5.BtnPWR.wasPressed()
        elif hasattr(M5, 'BtnC'):
            return M5.BtnC.wasPressed()
    except:
        pass
    return False


def draw_battery_icon(x, y):
    level = get_battery_level()
    if level == -1:
        return
    M5.Lcd.fillRect(x, y, 20, 10, BLACK)
    M5.Lcd.drawRect(x, y, 16, 8, WHITE)
    M5.Lcd.fillRect(x + 16, y + 2, 2, 4, WHITE)

    color = RED
    if level > 50:
        color = GREEN
    elif level > 20:
        color = YELLOW

    fill_width = int((level / 100.0) * 14)
    if fill_width > 0:
        M5.Lcd.fillRect(x + 1, y + 1, fill_width, 6, color)

    M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(x + 20, y)
    M5.Lcd.print(str(level) + "%")


# --- ЗАГРУЗКА ---
def draw_boot_screen():
    M5.Lcd.clear(BLACK)
    start_time = time.ticks_ms()

    if show_boot_tiger:
        tiger_map = [
            "..2......2..",
            "..21....12..",
            ".2112222112.",
            ".2111111112.",
            "211222222112",
            "211231132112",
            "211221122112",
            "211111111112",
            ".2112434112.",
            ".2112222112.",
            "..21111112..",
            "..21111112..",
            "...222222...",
        ]
        ox, oy, px_size = 74, 10, 6
        colors = {0: BLACK, 1: ORANGE, 2: BLACK, 3: WHITE, 4: 0xFFC0CB}

        for r, row in enumerate(tiger_map):
            for c, char in enumerate(row):
                if char != '.':
                    M5.Lcd.fillRect(ox + c * px_size, oy + r * px_size, px_size, px_size, colors[int(char)])

        while time.ticks_diff(time.ticks_ms(), start_time) < 2000:
            M5.update()
            if M5.BtnA.wasPressed():
                break
            time.sleep_ms(20)

    if not show_boot_tiger:
        ox, oy = 75, 20
        M5.Lcd.fillRect(ox, oy, 50, 50, ORANGE)
        M5.Lcd.fillRect(ox - 8, oy + 8, 8, 15, ORANGE)
        M5.Lcd.fillRect(ox + 50, oy + 8, 8, 15, ORANGE)
        M5.Lcd.fillRect(ox + 3, oy - 6, 12, 6, BLACK)
        M5.Lcd.fillRect(ox + 35, oy - 6, 12, 6, BLACK)
        M5.Lcd.fillRect(ox + 15, oy + 15, 20, 10, BLACK)
        M5.Lcd.fillRect(ox + 5, oy + 25, 10, 6, WHITE)
        M5.Lcd.fillRect(ox + 35, oy + 25, 10, 6, WHITE)
        M5.Lcd.fillRect(ox + 8, oy + 25, 4, 6, GREEN)
        M5.Lcd.fillRect(ox + 38, oy + 25, 4, 6, GREEN)

        M5.Lcd.setTextColor(GREEN)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 80)
        M5.Lcd.print("TIGER OS v2.4 [Bruce]")
        M5.Lcd.setCursor(10, 95)
        M5.Lcd.print("Init Hardware... OK")
        M5.Lcd.setCursor(10, 110)
        M5.Lcd.print("Loading...")
        prog_y = 120
    else:
        M5.Lcd.setTextColor(GREEN)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 90)
        M5.Lcd.print("TIGER OS v2.4 [Bruce]")
        M5.Lcd.setCursor(10, 105)
        M5.Lcd.print("Init Hardware... OK")
        M5.Lcd.setCursor(10, 120)
        M5.Lcd.print("Loading...")
        prog_y = 132

    M5.Lcd.drawRect(10, prog_y, 100, 8, GREEN)
    for i in range(0, 11):
        M5.Lcd.fillRect(12, prog_y + 2, i * 9, 4, GREEN)
        time.sleep_ms(50)


# --- МЕНЮ ---
def draw_menu():
    M5.Lcd.clear(BLACK)
    M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(5, 5)
    M5.Lcd.print("MENU [A:Run B/C:Move]")
    M5.Lcd.drawLine(0, 16, 240, 16, DARK_GRAY)
    draw_battery_icon(185, 2)

    icon_char = menu_icons[menu_index]
    title = menu_items[menu_index]

    M5.Lcd.drawRect(70, 30, 100, 60, CYAN)
    M5.Lcd.drawRect(72, 32, 96, 56, CYAN)

    M5.Lcd.fillRect(74, 34, 92, 52, BLACK)
    M5.Lcd.fillRect(0, 96, 240, 24, BLACK)

    M5.Lcd.setTextColor(CYAN)
    M5.Lcd.setTextSize(5)
    M5.Lcd.setCursor(110, 40)
    M5.Lcd.print(icon_char)

    M5.Lcd.setTextColor(YELLOW)
    M5.Lcd.setTextSize(2)
    text_x = 120 - (len(title) * 6)
    M5.Lcd.setCursor(text_x, 100)
    M5.Lcd.print(title)


def handle_menu():
    global menu_index, current_state, score_tetris, pieceY, last_batt_level
    global tetris_init, shark_init, slots_init, sensors_init

    if get_battery_level() != last_batt_level:
        last_batt_level = get_battery_level()
        draw_battery_icon(185, 2)

    if M5.BtnB.wasPressed():
        menu_index = (menu_index + 1) % 5
        draw_menu()
    if is_btn_c_pressed():
        menu_index = (menu_index - 1) % 5
        draw_menu()

    if M5.BtnA.wasPressed():
        if menu_index == 0:
            current_state = GAME_TETRIS
            tetris_init = False
        elif menu_index == 1:
            current_state = GAME_SHARK
            shark_init = False
        elif menu_index == 2:
            current_state = GAME_SLOTS
            slots_init = False
        elif menu_index == 3:
            current_state = SENSORS
            sensors_init = False
        elif menu_index == 4:
            current_state = SETTINGS
            draw_settings()


# --- ТЕТРИС ---
def tetris_draw_frame():
    M5.Lcd.clear(BLACK)
    M5.Lcd.drawRect(40, 10, 60, 110, WHITE)
    M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(110, 60)
    M5.Lcd.print("A:Left")
    M5.Lcd.setCursor(110, 75)
    M5.Lcd.print("B:Right")
    M5.Lcd.setCursor(110, 90)
    M5.Lcd.print("C:Exit")
    M5.Lcd.setCursor(110, 20)
    M5.Lcd.print("Score:")
    M5.Lcd.setCursor(110, 32)
    M5.Lcd.print("0    ")


def tetris_redraw_grid():
    M5.Lcd.fillRect(41, 11, 58, 108, BLACK)
    for r in range(15):
        for c in range(10):
            if grid[r][c] != 0:
                M5.Lcd.fillRect(40 + c * 6, 10 + r * 6, 6, 6, grid[r][c])


def tetris_game_over():
    global tetris_init, pieceX, pieceY, last_pieceX, last_pieceY, score_tetris, tetris_fall_counter

    M5.Lcd.clear(BLACK)
    M5.Lcd.setTextColor(RED)
    M5.Lcd.setTextSize(2)
    M5.Lcd.setCursor(30, 40)
    M5.Lcd.print("Game Over!")
    M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(30, 70)
    M5.Lcd.print("Score: " + str(score_tetris))
    M5.Lcd.setTextColor(YELLOW)
    M5.Lcd.setCursor(30, 100)
    M5.Lcd.print("A:Restart  C:Exit")

    while True:
        M5.update()
        if M5.BtnA.wasPressed():
            for r in range(15):
                for c in range(10):
                    grid[r][c] = 0
            pieceX, pieceY = 4, 0
            last_pieceX, last_pieceY = 4, 0
            score_tetris = 0
            tetris_fall_counter = 0
            tetris_init = False
            return GAME_TETRIS
        if is_btn_c_pressed():
            tetris_init = False
            draw_menu()
            return MENU
        time.sleep_ms(20)


def run_tetris():
    global pieceX, pieceY, last_pieceX, last_pieceY, score_tetris
    global current_state, grid, tetris_init, tetris_fall_counter

    if not tetris_init:
        tetris_draw_frame()
        pieceX, pieceY = 4, 0
        last_pieceX, last_pieceY = 4, 0
        score_tetris = 0
        tetris_fall_counter = 0
        tetris_init = True

    if M5.BtnA.wasPressed():
        if pieceX > 0:
            M5.Lcd.fillRect(40 + pieceX * 6, 10 + pieceY, 6, 6, BLACK)
            pieceX -= 1
    if M5.BtnB.wasPressed():
        if pieceX < 9:
            M5.Lcd.fillRect(40 + pieceX * 6, 10 + pieceY, 6, 6, BLACK)
            pieceX += 1

    tetris_fall_counter += 1
    can_fall = False
    if tetris_fall_counter >= TETRIS_FALL_DELAY:
        can_fall = True

    collision = False
    if can_fall:
        tetris_fall_counter = 0
        test_y = pieceY + 1
        test_next_row = (test_y + 6) // 6
        blocked = False

        if test_y + 6 > 102:
            blocked = True
        elif test_next_row < 15:
            if grid[test_next_row][pieceX] != 0:
                blocked = True

        if blocked:
            collision = True
        else:
            M5.Lcd.fillRect(40 + pieceX * 6, 10 + pieceY, 6, 6, BLACK)
            pieceY += 1

    if collision:
        land_row = pieceY // 6
        if land_row < 0:
            land_row = 0
        if land_row >= 15:
            land_row = 14

        if land_row <= 1:
            current_state = tetris_game_over()
            return

        M5.Lcd.fillRect(40 + pieceX * 6, 10 + pieceY, 6, 6, BLACK)
        grid[land_row][pieceX] = CYAN

        cleared = 0
        for r in range(15):
            full = True
            for c in range(10):
                if grid[r][c] == 0:
                    full = False
                    break
            if full:
                for r2 in range(r, 0, -1):
                    for c in range(10):
                        grid[r2][c] = grid[r2 - 1][c]
                for c in range(10):
                    grid[0][c] = 0
                cleared += 1

        score_tetris += cleared * 100 + 10
        tetris_redraw_grid()

        M5.Lcd.fillRect(110, 32, 100, 12, BLACK)
        M5.Lcd.setTextColor(WHITE)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(110, 32)
        M5.Lcd.print(str(score_tetris))

        pieceY = 0
        pieceX = random.randint(0, 9)
        tetris_fall_counter = 0

        if grid[0][pieceX] != 0:
            current_state = tetris_game_over()
            return

    if pieceY < 102:
        M5.Lcd.fillRect(40 + pieceX * 6, 10 + pieceY, 6, 6, CYAN)
    last_pieceX, last_pieceY = pieceX, pieceY

    if is_btn_c_pressed():
        tetris_init = False
        current_state = MENU
        draw_menu()


# --- АКУЛА ---
def shark_draw_frame():
    M5.Lcd.clear(NAVY)
    M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(5, 5)
    M5.Lcd.print("Score: 0 | A:Up B:Dwn C:Exit")


def run_shark():
    global shark_init, shark_alive, fishY, sharkX, sharkY, score_shark
    global current_state, fish_lastY, shark_lastX, shark_move_counter

    if not shark_init:
        shark_draw_frame()
        fishY, sharkY = 60, 60
        fish_lastY = 60
        sharkX = 240
        shark_lastX = 240
        score_shark = 0
        shark_alive = True
        shark_move_counter = 0
        shark_init = True

    if not shark_alive:
        M5.Lcd.clear(BLACK)
        M5.Lcd.setTextColor(RED)
        M5.Lcd.setTextSize(2)
        M5.Lcd.setCursor(50, 40)
        M5.Lcd.print("Eaten!")
        M5.Lcd.setTextColor(WHITE)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(40, 70)
        M5.Lcd.print("Score: " + str(score_shark))
        M5.Lcd.setTextColor(YELLOW)
        M5.Lcd.setCursor(30, 100)
        M5.Lcd.print("A:Restart  C:Exit")

        while True:
            M5.update()
            if M5.BtnA.wasPressed():
                shark_init = False
                return
            if is_btn_c_pressed():
                shark_init = False
                current_state = MENU
                draw_menu()
                return
            time.sleep_ms(20)

    M5.Lcd.fillRect(30, fish_lastY, 12, 8, NAVY)
    if shark_lastX > -30:
        M5.Lcd.fillRect(shark_lastX, sharkY, 30, 16, NAVY)

    if M5.BtnA.wasPressed():
        fishY -= 12
    if M5.BtnB.wasPressed():
        fishY += 12
    if fishY > 125:
        fishY = 125
    if fishY < 5:
        fishY = 5

    shark_move_counter += 1
    if shark_move_counter >= SHARK_MOVE_DELAY:
        shark_move_counter = 0
        sharkX -= 6
        if sharkX < -30:
            sharkX = 240
            sharkY = random.randint(15, 105)
            score_shark += 1
            M5.Lcd.fillRect(5, 5, 160, 15, NAVY)
            M5.Lcd.setTextColor(WHITE)
            M5.Lcd.setCursor(5, 5)
            M5.Lcd.print("Score: " + str(score_shark) + " | A:Up B:Dwn C:Exit")

    if 15 < sharkX < 50:
        if abs(fishY - sharkY) < 14:
            shark_alive = False
            return

    M5.Lcd.fillRect(30, fishY, 12, 8, YELLOW)
    M5.Lcd.fillRect(sharkX, sharkY, 30, 16, GRAY)
    M5.Lcd.fillRect(sharkX, sharkY + 4, 6, 4, RED)

    fish_lastY = fishY
    shark_lastX = sharkX

    if is_btn_c_pressed():
        shark_init = False
        current_state = MENU
        draw_menu()


# --- СЛОТЫ ---
def slots_draw_static():
    M5.Lcd.clear(BLACK)
    M5.Lcd.setTextColor(MAGENTA)
    M5.Lcd.setTextSize(2)
    M5.Lcd.setCursor(60, 10)
    M5.Lcd.print("777 CASINO")
    M5.Lcd.drawRect(30, 40, 40, 40, WHITE)
    M5.Lcd.drawRect(100, 40, 40, 40, WHITE)
    M5.Lcd.drawRect(170, 40, 40, 40, WHITE)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setTextColor(GREEN)
    M5.Lcd.setCursor(10, 110)
    M5.Lcd.print("Bal: $" + str(slot_score) + " | A: SPIN | C: Exit")


def slots_draw_values():
    M5.Lcd.fillRect(32, 42, 36, 36, BLACK)
    M5.Lcd.fillRect(102, 42, 36, 36, BLACK)
    M5.Lcd.fillRect(172, 42, 36, 36, BLACK)
    M5.Lcd.setTextColor(YELLOW)
    M5.Lcd.setTextSize(3)
    M5.Lcd.setCursor(42, 48)
    M5.Lcd.print(slot_symbols[slot1])
    M5.Lcd.setCursor(112, 48)
    M5.Lcd.print(slot_symbols[slot2])
    M5.Lcd.setCursor(182, 48)
    M5.Lcd.print(slot_symbols[slot3])


def slots_update_balance():
    M5.Lcd.fillRect(10, 110, 220, 15, BLACK)
    M5.Lcd.setTextColor(GREEN)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(10, 110)
    M5.Lcd.print("Bal: $" + str(slot_score) + " | A: SPIN | C: Exit")


def run_slots():
    global slots_init, spinning, slot1, slot2, slot3, slot_score
    global current_state, slot_pause_until

    if not slots_init:
        slots_draw_static()
        slots_draw_values()
        slot_pause_until = 0
        slots_init = True

    now = time.ticks_ms()
    if not spinning and now > slot_pause_until:
        if M5.BtnA.wasPressed() and slot_score >= 10:
            slot_score -= 10
            slots_update_balance()
            spinning = True
            spins = random.randint(10, 20)
            for _ in range(spins):
                slot1 = random.randint(0, 3)
                slot2 = random.randint(0, 3)
                slot3 = random.randint(0, 3)
                slots_draw_values()
                time.sleep_ms(60)

            if slot1 == slot2 and slot2 == slot3:
                slot_score += 100
            elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
                slot_score += 20

            slots_draw_values()
            slots_update_balance()
            slot_pause_until = time.ticks_ms() + 1000
            spinning = False

    if is_btn_c_pressed():
        slots_init = False
        current_state = MENU
        draw_menu()


# --- ДАТЧИКИ ---
def run_sensors():
    global sensors_init, current_state

    if not sensors_init:
        M5.Lcd.clear(BLACK)
        M5.Lcd.setTextColor(CYAN)
        M5.Lcd.setTextSize(2)
        M5.Lcd.setCursor(10, 10)
        M5.Lcd.print("IMU Accel")
        M5.Lcd.setTextColor(YELLOW)
        M5.Lcd.setTextSize(1)
        M5.Lcd.setCursor(10, 115)
        M5.Lcd.print("C: Exit")
        sensors_init = True

    try:
        ax, ay, az = M5.Imu.getAccel()
        if abs(ax) < 0.05:
            ax = 0.0
        if abs(ay) < 0.05:
            ay = 0.0
        if abs(az) < 0.05:
            az = 0.0
    except:
        ax, ay, az = 0.0, 0.0, 0.0

    M5.Lcd.fillRect(10, 40, 200, 60, BLACK)
    M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setTextSize(1)
    M5.Lcd.setCursor(10, 45)
    M5.Lcd.print("X: {:.2f} G".format(ax))
    M5.Lcd.setCursor(10, 65)
    M5.Lcd.print("Y: {:.2f} G".format(ay))
    M5.Lcd.setCursor(10, 85)
    M5.Lcd.print("Z: {:.2f} G".format(az))

    if is_btn_c_pressed():
        sensors_init = False
        current_state = MENU
        draw_menu()


# --- НАСТРОЙКИ ---
def draw_settings():
    M5.Lcd.clear(BLACK)
    M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setTextSize(2)
    M5.Lcd.setCursor(10, 10)
    M5.Lcd.print("Settings")

    M5.Lcd.setTextSize(1)
    y_pos = 35

    if settings_index == 0:
        M5.Lcd.setTextColor(YELLOW)
    else:
        M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setCursor(10, y_pos)
    M5.Lcd.print("Bright: " + str(brightness) + "   ")

    y_pos += 15
    if settings_index == 1:
        M5.Lcd.setTextColor(YELLOW)
    else:
        M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setCursor(10, y_pos)
    if screen_always_on:
        M5.Lcd.print("Dim: OFF    ")
    else:
        M5.Lcd.print("Dim: " + str(screen_timeout) + "s    ")

    y_pos += 15
    if settings_index == 2:
        M5.Lcd.setTextColor(YELLOW)
    else:
        M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setCursor(10, y_pos)
    if show_boot_tiger:
        M5.Lcd.print("Boot Tiger: ON  ")
    else:
        M5.Lcd.print("Boot Tiger: OFF ")

    y_pos += 15
    if settings_index == 3:
        M5.Lcd.setTextColor(YELLOW)
    else:
        M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setCursor(10, y_pos)
    M5.Lcd.print("Reboot Device   ")

    y_pos += 15
    if settings_index == 4:
        M5.Lcd.setTextColor(YELLOW)
    else:
        M5.Lcd.setTextColor(WHITE)
    M5.Lcd.setCursor(10, y_pos)
    M5.Lcd.print("Back to Menu    ")

    M5.Lcd.setTextColor(YELLOW)
    M5.Lcd.setCursor(10, 115)
    M5.Lcd.print("C: Exit")
    draw_battery_icon(185, 2)


def handle_settings():
    global settings_index, brightness, screen_timeout, current_state
    global last_batt_level, screen_always_on, show_boot_tiger

    if M5.BtnB.wasPressed():
        settings_index = (settings_index + 1) % settings_total_items
        draw_settings()
    if is_btn_c_pressed():
        settings_index = (settings_index - 1) % settings_total_items
        draw_settings()

    if M5.BtnA.wasPressed():
        if settings_index == 0:
            if brightness >= 250:
                brightness = 50
            else:
                brightness += 50
            M5.Lcd.setBrightness(brightness)
            draw_settings()

        elif settings_index == 1:
            if not screen_always_on:
                if screen_timeout >= 30:
                    screen_always_on = True
                else:
                    screen_timeout += 5
            else:
                screen_always_on = False
                screen_timeout = 5
            draw_settings()

        elif settings_index == 2:
            show_boot_tiger = not show_boot_tiger
            draw_settings()

        elif settings_index == 3:
            M5.Lcd.clear(BLACK)
            M5.Lcd.setTextColor(RED)
            M5.Lcd.setTextSize(2)
            M5.Lcd.setCursor(40, 55)
            M5.Lcd.print("Rebooting...")
            time.sleep_ms(500)
            machine.reset()

        elif settings_index == 4:
            current_state = MENU
            draw_menu()

    batt = get_battery_level()
    if batt != last_batt_level:
        last_batt_level = batt
        draw_battery_icon(185, 2)


# --- СТАРТ ---
M5.Lcd.setBrightness(brightness)
draw_boot_screen()

current_state = MENU
draw_menu()
last_batt_level = get_battery_level()

while True:
    M5.update()
    now = time.ticks_ms()

    if current_state != BOOT and not is_screen_off and not screen_always_on:
        if time.ticks_diff(now, last_activity_time) > (screen_timeout * 1000):
            M5.Lcd.setBrightness(0)
            is_screen_off = True

    if M5.BtnA.wasPressed() or M5.BtnB.wasPressed() or is_btn_c_pressed():
        last_activity_time = now
        if is_screen_off:
            M5.Lcd.setBrightness(brightness)
            is_screen_off = False
            time.sleep_ms(200)
            continue

    if is_screen_off:
        time.sleep_ms(30)
        continue

    if current_state == MENU:
        handle_menu()
    elif current_state == GAME_TETRIS:
        run_tetris()
    elif current_state == GAME_SHARK:
        run_shark()
    elif current_state == GAME_SLOTS:
        run_slots()
    elif current_state == SENSORS:
        run_sensors()
    elif current_state == SETTINGS:
        handle_settings()

    time.sleep_ms(20)
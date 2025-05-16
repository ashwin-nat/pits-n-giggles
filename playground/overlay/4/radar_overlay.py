import pygame
import math
import random
import win32gui
import win32con
import win32api
import time

# ========== CONFIG ==========
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 400
CAR_COUNT = 22
FPS = 30
RADAR_RANGE = 100  # meters in each direction
PIXELS_PER_METER = 2
CAR_LENGTH = 20    # in pixels (increased size)
CAR_WIDTH = 10     # in pixels (increased size)
MAX_CAR_DISTANCE = 100  # meters

# ========== GLOBAL STATE ==========
overlay_enabled = True
display_message = ""
message_timer = 0
windowed_mode = False  # Default to windowless mode

# ========== STUB DATA ==========
class CarStub:
    def __init__(self, angle_offset):
        self.angle_offset = angle_offset
        self.radius = 40 + random.uniform(-10, 10)
        self.yaw = angle_offset
        self.x = self.radius * math.cos(math.radians(self.angle_offset))
        self.z = self.radius * math.sin(math.radians(self.angle_offset))

    def update(self, frame):
        angle = self.angle_offset + frame * 0.5
        self.x = self.radius * math.cos(math.radians(angle))
        self.z = self.radius * math.sin(math.radians(angle))
        self.yaw = (angle + 90) % 360  # tangent to the orbit

def generate_stub_data(frame):
    cars = []
    for i, car in enumerate(car_stubs):
        car.update(frame)
        cars.append({
            "world-position": {"x": car.x, "z": car.z},
            "orientation": {"yaw": car.yaw}
        })
    return {
        "car-motion-data": cars,
        "player-index": 0
    }

# ========== WINDOWS UTILS ==========
def make_window_clickthrough(hwnd):
    """Makes the window click-through, allowing it to be transparent and non-interactive."""
    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                           extended_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)

def make_window_interactive(hwnd):
    """Makes the window interactive again, allowing dragging and resizing."""
    extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    new_style = extended_style & ~win32con.WS_EX_TRANSPARENT
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                           new_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)

def keep_window_on_top(hwnd):
    """Ensure the window stays on top and doesn't minimize when clicked elsewhere"""
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

def get_window_handle(title):
    def enum_callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd) and title in win32gui.GetWindowText(hwnd):
            result.append(hwnd)
    handles = []
    win32gui.EnumWindows(enum_callback, handles)
    return handles[0] if handles else None

# ========== DRAWING ==========
def draw_car(screen, dx, dz, yaw_deg, is_player):
    cx = WINDOW_WIDTH // 2 + int(dx * PIXELS_PER_METER)
    cz = WINDOW_HEIGHT // 2 + int(dz * PIXELS_PER_METER)
    yaw_rad = math.radians(-yaw_deg)

    # Rectangle points centered on (0,0)
    half_len = CAR_LENGTH // 2
    half_wid = CAR_WIDTH // 2
    corners = [
        (-half_len, -half_wid),
        (-half_len,  half_wid),
        ( half_len,  half_wid),
        ( half_len, -half_wid),
    ]

    # Rotate and translate to center
    rotated = []
    for x, y in corners:
        rx = x * math.cos(yaw_rad) - y * math.sin(yaw_rad)
        ry = x * math.sin(yaw_rad) + y * math.cos(yaw_rad)
        rotated.append((cx + int(rx), cz + int(ry)))

    color = (0, 255, 0) if is_player else (255, 0, 0)
    pygame.draw.polygon(screen, color, rotated)

def draw_radar(screen, data):
    screen.fill((0, 0, 0, 0))  # transparent color key

    player = data["car-motion-data"][data["player-index"]]
    px = player["world-position"]["x"]
    pz = player["world-position"]["z"]

    for i, car in enumerate(data["car-motion-data"]):
        cx = car["world-position"]["x"]
        cz = car["world-position"]["z"]
        yaw = car["orientation"]["yaw"]

        dx = cx - px
        dz = cz - pz

        # Euclidean distance check
        distance = math.sqrt(dx**2 + dz**2)
        if distance > MAX_CAR_DISTANCE:
            continue  # skip cars outside the range

        draw_car(screen, dx, dz, yaw, i == data["player-index"])

def draw_message_overlay(screen, text):
    global message_timer
    if message_timer > 0:
        font = pygame.font.SysFont("Arial", 20)
        rendered = font.render(text, True, (255, 255, 255))
        screen.blit(rendered, (10, 10))
        message_timer -= 1

# ========== MAIN ==========
# ========== MAIN ==========
def main():
    global overlay_enabled, display_message, message_timer, windowed_mode, WINDOW_WIDTH, WINDOW_HEIGHT

    pygame.init()
    pygame.display.set_caption("F1 Radar Overlay")

    # Set mode to windowless by default (transparent, no border)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.NOFRAME | pygame.SRCALPHA)
    hwnd = get_window_handle("F1 Radar Overlay")
    keep_window_on_top(hwnd)

    # Initially set the window to click-through (windowless mode)
    make_window_clickthrough(hwnd)

    # Ensure the window is resizable and movable (windowed mode)
    is_resizable = True
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)

    clock = pygame.time.Clock()
    frame = 0

    running = True
    while running:
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    windowed_mode = not windowed_mode
                    if windowed_mode:
                        # Switch to windowed mode (resizable and moveable)
                        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                        make_window_interactive(hwnd)  # Enable interaction with the window
                        display_message = "Windowed Mode - Move & Resize"
                    else:
                        # Switch to windowless mode (transparent and always on top)
                        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.NOFRAME | pygame.SRCALPHA)
                        make_window_clickthrough(hwnd)  # Disable interaction
                        display_message = "Windowless Mode - Locked"
                    message_timer = FPS * 2  # show for 2 seconds

            elif event.type == pygame.VIDEORESIZE:
                # Update the window size when resized
                WINDOW_WIDTH, WINDOW_HEIGHT = event.size
                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.SRCALPHA)

        data = generate_stub_data(frame)
        draw_radar(screen, data)
        draw_message_overlay(screen, display_message)

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()


# ========== CAR STUBS SETUP ==========
car_stubs = [CarStub(i * (360 / CAR_COUNT)) for i in range(CAR_COUNT)]

if __name__ == "__main__":
    main()

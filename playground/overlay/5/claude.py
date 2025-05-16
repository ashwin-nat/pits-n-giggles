import pygame
import json
import time
import math
import sys
import os
from typing import Dict, List, Any, Tuple

# Make window stay on top and be transparent
os.environ['SDL_VIDEO_WINDOW_POS'] = '20,20'

class F1ProximityRadar:
    def __init__(self, width=300, height=300):
        pygame.init()

        # Set up window parameters
        self.width = width
        self.height = height
        self.borderless_mode = True  # Start in borderless mode by default
        self.dragging = False
        self.drag_offset = (0, 0)

        # Create the initial window
        self.setup_window()

        # Set up a clock for controlling frame rate
        self.clock = pygame.time.Clock()

        # Cars data - will be updated with real data
        self.cars_data = []
        self.player_index = 0

        # Colors - using extremely transparent elements for better overlay
        self.bg_color = (0, 0, 0, 40)  # Almost completely transparent black
        self.grid_color = (50, 50, 50, 100)  # Subtle grid lines
        self.player_color = (0, 255, 0, 180)  # Semi-transparent green for player
        self.other_car_color = (220, 220, 220, 180)  # Semi-transparent light gray for other cars

        # Radar parameters
        self.center_x = width // 2
        self.center_y = height // 2
        self.radar_range = 50  # How many meters around the player to show
        self.car_width = 2.0  # Meters
        self.car_length = 4.5  # Meters
        self.pixel_per_meter = min(width, height) / (self.radar_range * 2)

        # Detection range circle parameters
        self.detection_range = 30  # meters

        # UI elements
        self.font = pygame.font.SysFont(None, 20)

    def setup_window(self):
        if os.name == 'nt':
            import ctypes

        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TOPMOST = 0x00000008
        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001

        if self.borderless_mode:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

        if os.name == 'nt':
            hwnd = pygame.display.get_wm_info()["window"]

            # Always set topmost and layered style (no transparent flag = not click-through)
            exstyle = ctypes.windll.user32.GetWindowLongA(hwnd, GWL_EXSTYLE)
            new_exstyle = exstyle | WS_EX_LAYERED | WS_EX_TOPMOST
            ctypes.windll.user32.SetWindowLongA(hwnd, GWL_EXSTYLE, new_exstyle)

            # Layered window alpha: fully opaque (no transparency)
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x2)

            # Ensure it stays topmost
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)

        pygame.display.set_caption("F1 Proximity Radar")


    def toggle_window_mode(self):
        """Toggle between borderless and windowed mode"""
        self.borderless_mode = not self.borderless_mode
        self.setup_window()
        # Recalculate center coordinates when window is resized
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.pixel_per_meter = min(self.width, self.height) / (self.radar_range * 2)

    def update_data(self, data: Dict[str, Any]):
        """Update the radar with new telemetry data"""
        self.cars_data = data.get("car-motion-data", [])
        self.player_index = data.get("player-index", 0)

    def world_to_radar(self, car_x: float, car_z: float, player_x: float, player_z: float,
                      player_fwd_x: float, player_fwd_z: float, player_right_x: float, player_right_z: float) -> Tuple[float, float]:
        """Convert world coordinates to radar coordinates based on player's orientation"""
        # Calculate relative position vector from player to car
        rel_x = car_x - player_x
        rel_z = car_z - player_z

        # Project onto player's forward and right vectors to get local coordinates
        forward_proj = rel_x * player_fwd_x + rel_z * player_fwd_z
        right_proj = rel_x * player_right_x + rel_z * player_right_z

        # Convert to screen coordinates (player at center)
        # Forward direction is up on screen (-y), right direction is right on screen (+x)
        screen_x = self.center_x + right_proj * self.pixel_per_meter
        screen_y = self.center_y - forward_proj * self.pixel_per_meter

        return screen_x, screen_y

    def render(self):
        """Render the radar screen"""
        # Clear screen with completely transparent background
        self.screen.fill((0, 0, 0, 0))

        # Ensure transparency is preserved by using SRCALPHA
        background = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Use an almost transparent background (only slight darkening)
        background.fill((0, 0, 0, 40))  # Very low alpha value for minimal darkening
        self.screen.blit(background, (0, 0))

        # Draw grid lines
        grid_spacing = 10  # meters
        grid_pixels = grid_spacing * self.pixel_per_meter

        # Vertical grid lines
        for x in range(int(self.center_x - self.width//2), int(self.center_x + self.width//2), int(grid_pixels)):
            pygame.draw.line(self.screen, self.grid_color, (x, 0), (x, self.height), 1)

        # Horizontal grid lines
        for y in range(int(self.center_y - self.height//2), int(self.center_y + self.height//2), int(grid_pixels)):
            pygame.draw.line(self.screen, self.grid_color, (0, y), (self.width, y), 1)

        # Draw detection range circle
        detection_radius = self.detection_range * self.pixel_per_meter
        pygame.draw.circle(self.screen, (30, 30, 30), (self.center_x, self.center_y),
                          int(detection_radius), 1)

        # Draw dotted centerlines for reference
        for i in range(0, self.width, 8):
            pygame.draw.line(self.screen, (50, 50, 50), (i, self.center_y), (i+4, self.center_y), 1)
        for i in range(0, self.height, 8):
            pygame.draw.line(self.screen, (50, 50, 50), (self.center_x, i), (self.center_x, i+4), 1)

        # If we have car data
        if self.cars_data and len(self.cars_data) > self.player_index:
            player_car = self.cars_data[self.player_index]
            player_pos = player_car.get("world-position", {"x": 0, "y": 0, "z": 0})
            player_forward = player_car.get("world-forward-dir", {"x": 0, "y": 0, "z": 1})
            player_right = player_car.get("world-right-dir", {"x": 1, "y": 0, "z": 0})

            # Normalize player direction vectors if needed
            fwd_mag = math.sqrt(player_forward["x"]**2 + player_forward["z"]**2)
            if fwd_mag > 0:
                fwd_x = player_forward["x"] / fwd_mag
                fwd_z = player_forward["z"] / fwd_mag
            else:
                fwd_x, fwd_z = 0, 1

            right_mag = math.sqrt(player_right["x"]**2 + player_right["z"]**2)
            if right_mag > 0:
                right_x = player_right["x"] / right_mag
                right_z = player_right["z"] / right_mag
            else:
                right_x, right_z = 1, 0

            # Draw player car in center (simplified rectangle)
            car_length_px = self.car_length * self.pixel_per_meter
            car_width_px = self.car_width * self.pixel_per_meter

            # Draw player car (simplified as rectangular shape with arrow)
            player_rect = pygame.Rect(
                self.center_x - car_width_px/2,
                self.center_y - car_length_px/2,
                car_width_px,
                car_length_px
            )
            pygame.draw.rect(self.screen, self.player_color, player_rect)

            # Draw direction indicator on player car
            pygame.draw.line(self.screen, (255, 255, 255),
                            (self.center_x, self.center_y),
                            (self.center_x, self.center_y - car_length_px/2), 2)

            # Draw other cars
            for i, car in enumerate(self.cars_data):
                if i == self.player_index:
                    continue

                car_pos = car.get("world-position", {"x": 0, "y": 0, "z": 0})
                car_forward = car.get("world-forward-dir", {"x": 0, "y": 0, "z": 1})

                # Calculate distance to player
                dx = car_pos["x"] - player_pos["x"]
                dz = car_pos["z"] - player_pos["z"]
                distance = math.sqrt(dx*dx + dz*dz)

                # Only show cars within detection range
                if distance < self.radar_range:
                    # Convert car position to radar coordinates
                    car_screen_x, car_screen_y = self.world_to_radar(
                        car_pos["x"], car_pos["z"],
                        player_pos["x"], player_pos["z"],
                        fwd_x, fwd_z, right_x, right_z
                    )

                    # Calculate car orientation relative to player
                    car_fwd_x = car_forward["x"]
                    car_fwd_z = car_forward["z"]

                    # Normalize
                    car_fwd_mag = math.sqrt(car_fwd_x**2 + car_fwd_z**2)
                    if car_fwd_mag > 0:
                        car_fwd_x /= car_fwd_mag
                        car_fwd_z /= car_fwd_mag

                    # Calculate angle in player's reference frame
                    dot_product = car_fwd_x * fwd_x + car_fwd_z * fwd_z
                    cross_product = car_fwd_x * right_z - car_fwd_z * right_x
                    angle = math.atan2(cross_product, dot_product)

                    # Draw car representation as a rotated rectangle
                    car_length_px = self.car_length * self.pixel_per_meter
                    car_width_px = self.car_width * self.pixel_per_meter

                    # Create car corners (using simplified representation)
                    half_length = car_length_px / 2
                    half_width = car_width_px / 2

                    # Calculate corner positions
                    cos_a = math.cos(angle)
                    sin_a = math.sin(angle)

                    corners = [
                        (car_screen_x + sin_a*half_width - cos_a*half_length,
                         car_screen_y - cos_a*half_width - sin_a*half_length),
                        (car_screen_x - sin_a*half_width - cos_a*half_length,
                         car_screen_y + cos_a*half_width - sin_a*half_length),
                        (car_screen_x - sin_a*half_width + cos_a*half_length,
                         car_screen_y + cos_a*half_width + sin_a*half_length),
                        (car_screen_x + sin_a*half_width + cos_a*half_length,
                         car_screen_y - cos_a*half_width + sin_a*half_length)
                    ]

                    # Draw car as polygon with arrow indicating direction
                    pygame.draw.polygon(self.screen, self.other_car_color, corners)

                    # Calculate front center point to draw direction indicator
                    front_x = car_screen_x + cos_a * half_length
                    front_y = car_screen_y + sin_a * half_length

                    # Draw direction indicator line
                    pygame.draw.line(self.screen, (255, 255, 255),
                                    (car_screen_x, car_screen_y),
                                    (front_x, front_y), 1)

        # Draw controls info if in windowed mode
        if not self.borderless_mode:
            controls_text = self.font.render("T: Toggle Mode | ESC: Quit", True, (200, 200, 200))
            self.screen.blit(controls_text, (10, 10))

        pygame.display.flip()

    def handle_window_events(self, event):
        """Handle window-related events like dragging and resizing"""
        # Window resize event
        if event.type == pygame.VIDEORESIZE:
            self.width, self.height = event.size
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            # Update center coordinates
            self.center_x = self.width // 2
            self.center_y = self.height // 2
            self.pixel_per_meter = min(self.width, self.height) / (self.radar_range * 2)
            # Re-apply window settings after resize
            self.setup_window()

        # Mouse events for dragging in windowed mode
        elif not self.borderless_mode and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
            self.dragging = True
            self.drag_offset = event.pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif not self.borderless_mode and event.type == pygame.MOUSEMOTION and self.dragging:
            if os.name == 'nt':
                # On Windows, use Win32 API to move the window
                import ctypes
                hwnd = pygame.display.get_wm_info()["window"]
                x, y = ctypes.windll.user32.GetCursorPos()
                x -= self.drag_offset[0]
                y -= self.drag_offset[1]
                ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001)
            else:
                # On other platforms, this is platform-dependent and may not work well
                # This is a simple attempt that might work on some systems
                x, y = pygame.mouse.get_pos()
                pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE | pygame.NOFRAME)
                os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x-self.drag_offset[0]},{y-self.drag_offset[1]}"

        # Toggle window mode with T key
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
            self.toggle_window_mode()

    def generate_sample_data(self):
        """Generate sample car data for demonstration"""
        cars_data = []
        num_cars = 10
        time_factor = time.time()

        # Create player car (centered at origin, pointing forward)
        player_car = {
            "world-position": {
                "x": 0,
                "y": 0,
                "z": 0
            },
            "world-velocity": {
                "x": 0,
                "y": 0,
                "z": 30
            },
            "world-forward-dir": {
                "x": 0,
                "y": 0,
                "z": 1
            },
            "world-right-dir": {
                "x": 1,
                "y": 0,
                "z": 0
            },
            "g-force": {
                "lateral": 0,
                "longitudinal": 1.2,
                "vertical": 0
            },
            "orientation": {
                "yaw": 0,
                "pitch": 0,
                "roll": 0
            }
        }
        cars_data.append(player_car)

        # Generate surrounding cars with realistic positions
        # Some cars in front, some behind, some alongside
        positions = [
            # Car directly ahead
            (0, 15, 0),
            # Car directly behind
            (0, -12, 0),
            # Cars alongside (left and right)
            (3, 0, 0),
            (-3, 5, 0),
            # Car diagonally ahead-right
            (2.5, 8, 0),
            # Moving car that circles the player
            (20 * math.cos(time_factor), 20 * math.sin(time_factor), 0),
            # Two cars racing side by side
            (-8, 25, 0),
            (-5, 25.5, 0),
            # Car making an overtaking move
            (1.5 * math.sin(time_factor), 8 + 2 * math.cos(time_factor), 0),
        ]

        # Add cars at those positions
        for i, (rel_x, rel_z, rel_y) in enumerate(positions[:num_cars-1]):
            # Add some movement over time
            rel_x += 0.5 * math.sin(time_factor * (i+1) * 0.3)
            rel_z += 0.2 * math.cos(time_factor * (i+1) * 0.5)

            # Calculate car orientation (pointing roughly in direction of movement)
            yaw = math.atan2(rel_x, rel_z) + (0.1 * math.sin(time_factor * (i+1) * 0.2))

            forward_x = math.sin(yaw)
            forward_z = math.cos(yaw)
            right_x = math.cos(yaw)
            right_z = -math.sin(yaw)

            car = {
                "world-position": {
                    "x": rel_x,
                    "y": rel_y,
                    "z": rel_z
                },
                "world-velocity": {
                    "x": 5 * math.sin(yaw),
                    "y": 0,
                    "z": 5 * math.cos(yaw)
                },
                "world-forward-dir": {
                    "x": forward_x,
                    "y": 0,
                    "z": forward_z
                },
                "world-right-dir": {
                    "x": right_x,
                    "y": 0,
                    "z": right_z
                },
                "g-force": {
                    "lateral": 0.2 * math.sin(time_factor * 2),
                    "longitudinal": 0.3 * math.cos(time_factor * 2),
                    "vertical": 0.1 * math.sin(time_factor * 5)
                },
                "orientation": {
                    "yaw": math.degrees(yaw),
                    "pitch": 0,
                    "roll": 2 * math.sin(time_factor)
                }
            }
            cars_data.append(car)

        # Return the data in expected format
        return {
            "car-motion-data": cars_data,
            "player-index": 0
        }
    def run(self):
        """Main loop for the radar application"""
        running = True
        last_update = 0
        update_interval = 1/60  # 60 times per second

        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        running = False

                    # Handle window events (like resizing and moving)
                    self.handle_window_events(event)

                current_time = time.time()
                if current_time - last_update >= update_interval:
                    # In a real implementation, this would receive data from your game
                    # For now, generate sample data
                    sample_data = self.generate_sample_data()
                    self.update_data(sample_data)
                    last_update = current_time

                self.render()
                self.clock.tick(60)  # Cap at 60 FPS

        except Exception as e:
            print(f"Error in radar application: {e}")
        finally:
            pygame.quit()
            sys.exit()


# Example integration with external data source
def integrate_with_external_data(data_receiver):
    """
    Example of how to integrate with your external data source

    Args:
        data_receiver: A function that retrieves the car telemetry data
                      in the expected format
    """
    radar = F1ProximityRadar(width=300, height=300)

    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False

                # Handle window events
                radar.handle_window_events(event)

            # Get data from your external source
            game_data = data_receiver()

            # Update radar with game data
            radar.update_data(game_data)

            # Render and maintain frame rate
            radar.render()
            radar.clock.tick(60)
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    # Create and run the radar with sample data
    radar = F1ProximityRadar(width=300, height=300)
    radar.run()
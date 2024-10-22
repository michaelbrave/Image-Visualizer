import pygame
import math
import random
import os
import json
from PIL import Image

class ImageNode:
    def __init__(self, image_path, x, y):
        self.image_path = image_path
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.connections = set()
        self.anchored = False
        self.base_radius = 30
        self.radius = self.base_radius
        self.hover_scale = 1.0
        
        # Load and scale the image
        self.original_image = Image.open(image_path)
        self.update_image()

    def update_image(self):
        current_size = (int(self.radius * 2), int(self.radius * 2))
        temp_image = self.original_image.copy()
        temp_image.thumbnail(current_size, Image.Resampling.LANCZOS)
        mode = temp_image.mode
        size = temp_image.size
        data = temp_image.tobytes()
        self.image = pygame.image.fromstring(data, size, mode)
        self.mask = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(self.mask, (255, 255, 255, 255), (int(self.radius), int(self.radius)), int(self.radius))
        self.image.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def set_hover_scale(self, scale):
        if self.hover_scale != scale:
            self.hover_scale = scale
            self.radius = self.base_radius * scale
            self.update_image()

class NetworkVisualizer:
    def __init__(self, width=1000, height=1000, save_file="network_state.json"):
        pygame.init()
        self.width = width
        self.height = height
        self.save_file = save_file
        
        # Initialize pygame display
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE | pygame.DROPFILE)
        pygame.display.set_caption("Image Network Visualizer")
        
        # Initialize core attributes
        self.nodes = []
        self.clock = pygame.time.Clock()
        self.selected_node = None
        self.hover_node = None
        
        # Add boundary parameters
        self.padding = 50
        self.min_window_size = (400, 400)
        
        # Physics parameters
        self.spring_length = 150
        self.spring_strength = 0.02
        self.repulsion = 300
        self.damping = 0.95
        self.max_velocity = 10
        
        # UI parameters
        self.hover_scale = 1.3
        self.connection_radius = 60
        self.font = pygame.font.Font(None, 24)
        self.instructions = [
            "Drop image files to add them",
            "Drag nodes to move them",
            "Drag one node to another to connect/disconnect",
            "Space to anchor/unanchor",
            "Delete/Backspace to remove selected",
            "S to save, L to load",
            "Esc to quit"
        ]

    def add_image(self, image_path, x=None, y=None):
        if x is None:
            x = random.randint(50, self.width - 50)
        if y is None:
            y = random.randint(50, self.height - 50)
        node = ImageNode(image_path, x, y)
        self.nodes.append(node)
        return node

    def remove_node(self, node):
        if node in self.nodes:
            for other_node in self.nodes:
                other_node.connections.discard(node)
            self.nodes.remove(node)

    def toggle_connection(self, node1, node2):
        if node1 != node2:
            if node2 in node1.connections:
                node1.connections.remove(node2)
                node2.connections.remove(node1)
            else:
                node1.connections.add(node2)
                node2.connections.add(node1)

    def save_state(self):
        data = {
            "nodes": [
                {
                    "image_path": node.image_path,
                    "x": node.x,
                    "y": node.y,
                    "anchored": node.anchored,
                    "connections": [self.nodes.index(conn) for conn in node.connections]
                }
                for node in self.nodes
            ]
        }
        with open(self.save_file, "w") as f:
            json.dump(data, f)
        print(f"State saved to {self.save_file}")

    def load_state(self):
        try:
            with open(self.save_file, "r") as f:
                data = json.load(f)
            self.nodes = []
            # Load nodes
            for node_data in data["nodes"]:
                node = self.add_image(node_data["image_path"], node_data["x"], node_data["y"])
                node.anchored = node_data.get("anchored", False)
            # Load connections
            for i, node_data in enumerate(data["nodes"]):
                for conn_index in node_data["connections"]:
                    self.nodes[i].connections.add(self.nodes[conn_index])
            print(f"State loaded from {self.save_file}")
        except FileNotFoundError:
            print(f"No save file found at {self.save_file}")

    def find_node_at_pos(self, x, y):
        for node in self.nodes:
            dx = x - node.x
            dy = y - node.y
            if math.sqrt(dx * dx + dy * dy) < node.radius:
                return node
        return None

    def apply_forces(self):
        # Skip physics if dragging a node
        if self.selected_node:
            return

        for node in self.nodes:
            if node.anchored:
                continue

            fx = fy = 0

            # Apply spring forces from connections
            for connected_node in node.connections:
                dx = connected_node.x - node.x
                dy = connected_node.y - node.y
                distance = math.sqrt(dx * dx + dy * dy)
                if distance == 0:
                    continue
                force = (distance - self.spring_length) * self.spring_strength
                fx += (dx / distance) * force
                fy += (dy / distance) * force

            # Apply repulsion forces from other nodes
            for other_node in self.nodes:
                if other_node != node:
                    dx = other_node.x - node.x
                    dy = other_node.y - node.y
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance < 1:
                        continue
                    force = self.repulsion / (distance * distance)
                    fx -= (dx / distance) * force
                    fy -= (dy / distance) * force

            # Update velocity and position
            node.vx = (node.vx + fx) * self.damping
            node.vy = (node.vy + fy) * self.damping

            # Limit velocity
            speed = math.sqrt(node.vx * node.vx + node.vy * node.vy)
            if speed > self.max_velocity:
                node.vx = (node.vx / speed) * self.max_velocity
                node.vy = (node.vy / speed) * self.max_velocity

            # Update position with boundary checking
            node.x = max(self.padding, min(self.width - self.padding, node.x + node.vx))
            node.y = max(self.padding, min(self.height - self.padding, node.y + node.vy))

    def draw_instructions(self):
        y = 10
        for instruction in self.instructions:
            text = self.font.render(instruction, True, (100, 100, 100))
            self.screen.blit(text, (10, y))
            y += 25

    def run(self):
        running = True
        while running:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    width = max(event.w, self.min_window_size[0])
                    height = max(event.h, self.min_window_size[1])
                    self.width = width
                    self.height = height
                    self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE | pygame.DROPFILE)
                elif event.type == pygame.DROPFILE:
                    image_path = event.file
                    self.add_image(image_path, mouse_x, mouse_y)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.selected_node = self.find_node_at_pos(mouse_x, mouse_y)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.selected_node:
                        target_node = self.find_node_at_pos(mouse_x, mouse_y)
                        if target_node and target_node != self.selected_node:
                            self.toggle_connection(self.selected_node, target_node)
                    self.selected_node = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.selected_node:
                        self.selected_node.anchored = not self.selected_node.anchored
                    elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and self.selected_node:
                        self.remove_node(self.selected_node)
                        self.selected_node = None
                    elif event.key == pygame.K_s:
                        self.save_state()
                    elif event.key == pygame.K_l:
                        self.load_state()
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            # Reset hover states
            self.hover_node = None
            for node in self.nodes:
                node.set_hover_scale(1.0)

            # Handle selected node
            if self.selected_node:
                self.selected_node.x, self.selected_node.y = mouse_x, mouse_y
                self.selected_node.vx = self.selected_node.vy = 0
                
                # Check for potential connections
                for node in self.nodes:
                    if node != self.selected_node:
                        dx = mouse_x - node.x
                        dy = mouse_y - node.y
                        if math.sqrt(dx * dx + dy * dy) < self.connection_radius:
                            self.hover_node = node
                            node.set_hover_scale(self.hover_scale)
                            self.selected_node.set_hover_scale(self.hover_scale)
                            break

            # Update physics and draw
            self.apply_forces()
            self.screen.fill((255, 255, 255))

            # Draw connections
            for node in self.nodes:
                for connected_node in node.connections:
                    pygame.draw.line(self.screen, (200, 200, 200), 
                                  (int(node.x), int(node.y)), 
                                  (int(connected_node.x), int(connected_node.y)), 2)

            # Draw nodes
            for node in self.nodes:
                pygame.draw.circle(self.screen, (240, 240, 240), 
                                (int(node.x), int(node.y)), int(node.radius))
                image_rect = node.image.get_rect(center=(int(node.x), int(node.y)))
                self.screen.blit(node.image, image_rect)
                
                if node.anchored:
                    pygame.draw.circle(self.screen, (0, 120, 255), 
                                    (int(node.x), int(node.y)), int(node.radius + 2), 3)
                if node == self.selected_node:
                    pygame.draw.circle(self.screen, (0, 255, 0), 
                                    (int(node.x), int(node.y)), int(node.radius + 2), 2)

            self.draw_instructions()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    visualizer = NetworkVisualizer()
    visualizer.run()
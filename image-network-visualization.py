import pygame
import math
import random
import os
import json
from PIL import Image

class ImageNode:
    def __init__(self, width=800, height=600, save_file="network_state.json"):
        pygame.init()
        self.width = width
        self.height = height
        # Create a resizable window
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Image Network Visualizer")
        
        # Other initializations
        self.nodes = []
        self.selected_node = None
        self.hover_node = None
        self.clock = pygame.time.Clock()
        self.save_file = save_file

        # Load and scale the image
        self.image_path = image_path  # Save image path for saving/loading state
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
    def __init__(self, width=800, height=600, save_file="network_state.json"):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Image Network Visualizer")
        
        self.nodes = []
        self.selected_node = None
        self.hover_node = None
        self.clock = pygame.time.Clock()
        self.save_file = save_file  # JSON file to save/load state

        # Physics and UI parameters
        self.spring_length = 100
        self.spring_strength = 0.03
        self.repulsion = 500
        self.damping = 0.98
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
            "F11 for fullscreen",
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
                    "anchored": node.anchored,  # Save anchored status
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
                node.anchored = node_data.get("anchored", False)  # Restore anchored status
            # Load connections
            for i, node_data in enumerate(data["nodes"]):
                for conn_index in node_data["connections"]:
                    self.nodes[i].connections.add(self.nodes[conn_index])
                    self.nodes[conn_index].connections.add(self.nodes[i])
            print(f"State loaded from {self.save_file}")
        except FileNotFoundError:
            print(f"No save file found at {self.save_file}")

    def toggle_fullscreen(self):
        if self.screen.get_flags() & pygame.FULLSCREEN:
            pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        else:
            pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        # Re-render the screen after the fullscreen change
        self.draw_instructions()
        pygame.display.flip()

    def find_node_at_pos(self, x, y):
        for node in self.nodes:
            dx = x - node.x
            dy = y - node.y
            if math.sqrt(dx * dx + dy * dy) < node.radius:
                return node
        return None

    def apply_forces(self):
        for node in self.nodes:
            if node.anchored or node == self.selected_node:
                continue
            for connected_node in node.connections:
                dx = connected_node.x - node.x
                dy = connected_node.y - node.y
                distance = math.sqrt(dx * dx + dy * dy)
                if distance == 0:
                    continue
                force = (distance - self.spring_length) * self.spring_strength
                node.vx += (dx / distance) * force
                node.vy += (dy / distance) * force
            if node != self.hover_node:
                for other_node in self.nodes:
                    if other_node != node and other_node != self.selected_node:
                        dx = other_node.x - node.x
                        dy = other_node.y - node.y
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance < 1:
                            continue
                        force = self.repulsion / (distance * distance)
                        node.vx -= (dx / distance) * force
                        node.vy -= (dy / distance) * force
            node.vx *= self.damping
            node.vy *= self.damping
            node.x += node.vx
            node.y += node.vy

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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()  # Fullscreen toggle
                    elif event.key == pygame.K_s:
                        self.save_state()
                    elif event.key == pygame.K_l:
                        self.load_state()
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            self.hover_node = None
            for node in self.nodes:
                node.set_hover_scale(1.0)

            if self.selected_node:
                self.selected_node.x, self.selected_node.y = mouse_x, mouse_y
                self.selected_node.vx = 0
                self.selected_node.vy = 0
                for node in self.nodes:
                    if node != self.selected_node:
                        dx = mouse_x - node.x
                        dy = mouse_y - node.y
                        if math.sqrt(dx * dx + dy * dy) < self.connection_radius:
                            self.hover_node = node
                            node.set_hover_scale(self.hover_scale)
                            self.selected_node.set_hover_scale(self.hover_scale)
                            break

            self.apply_forces()
            self.screen.fill((255, 255, 255))

            for node in self.nodes:
                for connected_node in node.connections:
                    pygame.draw.line(self.screen, (200, 200, 200), (node.x, node.y), (connected_node.x, connected_node.y), 2)

            for node in self.nodes:
                pygame.draw.circle(self.screen, (240, 240, 240), (int(node.x), int(node.y)), int(node.radius))
                image_rect = node.image.get_rect(center=(int(node.x), int(node.y)))
                self.screen.blit(node.image, image_rect)
                if node.anchored:
                    pygame.draw.circle(self.screen, (0, 120, 255), (int(node.x), int(node.y)), int(node.radius + 2), 3)
                if node == self.selected_node:
                    pygame.draw.circle(self.screen, (0, 255, 0), (int(node.x), int(node.y)), int(node.radius) + 2, 2)

            self.draw_instructions()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    visualizer = NetworkVisualizer()
    visualizer.run()

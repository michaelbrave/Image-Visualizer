import pygame
import math
import random
from pygame import gfxdraw
import os
from PIL import Image

class ImageNode:
    def __init__(self, image_path, x, y, radius=40):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.radius = radius
        self.base_radius = radius  # Store the original radius
        self.anchored = False
        self.connections = set()  # Store only the currently connected nodes
        self.hover_scale = 1.0  # Add scale factor for hover effect
        
        # Load and scale the image
        self.original_image = Image.open(image_path)
        self.update_image()
    
    def update_image(self):
        # Scale image based on current radius (affected by hover)
        current_size = (int(self.radius * 2), int(self.radius * 2))
        temp_image = self.original_image.copy()
        temp_image.thumbnail(current_size, Image.Resampling.LANCZOS)
        
        # Convert PIL image to pygame surface
        mode = temp_image.mode
        size = temp_image.size
        data = temp_image.tobytes()
        self.image = pygame.image.fromstring(data, size, mode)
        
        # Create circular mask
        self.mask = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(self.mask, (255, 255, 255, 255),
                         (int(self.radius), int(self.radius)), int(self.radius))
        self.image.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    def set_hover_scale(self, scale):
        if self.hover_scale != scale:
            self.hover_scale = scale
            self.radius = self.base_radius * scale
            self.update_image()

class NetworkVisualizer:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.DROPFILE)
        pygame.display.set_caption("Image Network Visualizer - Drop images to add")
        
        self.nodes = []
        self.selected_node = None
        self.hover_node = None
        self.clock = pygame.time.Clock()
        
        # Physics parameters
        self.gravity = 0.5
        self.spring_length = 100
        self.spring_strength = 0.03
        self.repulsion = 500
        self.damping = 0.98
        
        # UI parameters
        self.hover_scale = 1.3  # How much to scale up on hover
        self.connection_radius = 60  # Detection radius for connections
        
        # UI elements
        self.font = pygame.font.Font(None, 24)
        self.instructions = [
            "Drop image files to add them",
            "Drag nodes to move them",
            "Drag one node to another to connect/disconnect",
            "Space to anchor/unanchor",
            "Delete/Backspace to remove selected",
            "Esc to quit"
        ]
    
    def add_image(self, image_path, x=None, y=None):
        try:
            if x is None:
                x = random.randint(50, self.width - 50)
            if y is None:
                y = random.randint(50, self.height - 50)
            
            node = ImageNode(image_path, x, y)
            self.nodes.append(node)
            return node
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def remove_node(self, node):
        if node in self.nodes:
            # Remove all connections involving this node
            for other_node in self.nodes:
                if node in other_node.connections:
                    other_node.connections.remove(node)
            self.nodes.remove(node)
    
    def toggle_connection(self, node1, node2):
        if node1 != node2:
            if node2 in node1.connections:
                # Remove connection
                node1.connections.remove(node2)
                node2.connections.remove(node1)
            else:
                # Add connection
                node1.connections.add(node2)
                node2.connections.add(node1)
    
    def find_node_at_pos(self, x, y):
        for node in self.nodes:
            dx = x - node.x
            dy = y - node.y
            if math.sqrt(dx*dx + dy*dy) < node.radius:
                return node
        return None
    
    def apply_forces(self):
        for node in self.nodes:
            if node.anchored or node == self.selected_node:
                continue
                
            # Apply spring forces for connections
            for connected_node in node.connections:
                dx = connected_node.x - node.x
                dy = connected_node.y - node.y
                distance = math.sqrt(dx * dx + dy * dy)
                if distance == 0:
                    continue
                    
                # Spring force
                force = (distance - self.spring_length) * self.spring_strength
                node.vx += (dx / distance) * force
                node.vy += (dy / distance) * force
            
            # Only apply repulsion if not being dragged onto
            if node != self.hover_node:
                # Apply repulsion from other nodes
                for other_node in self.nodes:
                    if other_node != node and other_node != self.selected_node:
                        dx = other_node.x - node.x
                        dy = other_node.y - node.y
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance < 1:
                            continue
                            
                        # Repulsion force
                        force = self.repulsion / (distance * distance)
                        node.vx -= (dx / distance) * force
                        node.vy -= (dy / distance) * force
            
            # Update position
            node.vx *= self.damping
            node.vy *= self.damping
            node.x += node.vx
            node.y += node.vy
            
            # Boundary conditions
            padding = node.base_radius
            if node.x < padding:
                node.x = padding
                node.vx *= -0.5
            elif node.x > self.width - padding:
                node.x = self.width - padding
                node.vx *= -0.5
            if node.y < padding:
                node.y = padding
                node.vy *= -0.5
            elif node.y > self.height - padding:
                node.y = self.height - padding
                node.vy *= -0.5
    
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
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            # Update hover states and node positions
            self.hover_node = None
            for node in self.nodes:
                node.set_hover_scale(1.0)  # Reset scale
                
            if self.selected_node:
                # Update selected node position
                self.selected_node.x, self.selected_node.y = mouse_x, mouse_y
                self.selected_node.vx = 0
                self.selected_node.vy = 0
                
                # Check for hover over other nodes
                for node in self.nodes:
                    if node != self.selected_node:
                        dx = mouse_x - node.x
                        dy = mouse_y - node.y
                        distance = math.sqrt(dx*dx + dy*dy)
                        if distance < self.connection_radius:
                            self.hover_node = node
                            node.set_hover_scale(self.hover_scale)
                            self.selected_node.set_hover_scale(self.hover_scale)
                            break
            
            # Apply physics
            self.apply_forces()
            
            # Draw
            self.screen.fill((255, 255, 255))
            
            # Draw connections
            for node in self.nodes:
                for connected_node in node.connections:
                    pygame.draw.line(self.screen, (200, 200, 200),
                                  (node.x, node.y),
                                  (connected_node.x, connected_node.y), 2)
            
            # Draw nodes
            for node in self.nodes:
                # Draw circle background
                pygame.draw.circle(self.screen, (240, 240, 240),
                                (int(node.x), int(node.y)), int(node.radius))
                
                # Draw image
                image_rect = node.image.get_rect(center=(int(node.x), int(node.y)))
                self.screen.blit(node.image, image_rect)
                
                # Draw anchor indicator (blue outline)
                if node.anchored:
                    pygame.draw.circle(self.screen, (0, 120, 255),
                                    (int(node.x), int(node.y)), int(node.radius + 2), 3)
                
                # Highlight selected node
                if node == self.selected_node:
                    pygame.draw.circle(self.screen, (0, 255, 0),
                                    (int(node.x), int(node.y)), int(node.radius) + 2, 2)
            
            # Draw instructions
            self.draw_instructions()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

# Example usage
if __name__ == "__main__":
    visualizer = NetworkVisualizer()
    visualizer.run()

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
        self.anchored = False
        self.connections = set()
        
        # Load and scale the image
        original_image = Image.open(image_path)
        # Scale image to fit in circle while maintaining aspect ratio
        size = (radius * 2, radius * 2)
        original_image.thumbnail(size, Image.Resampling.LANCZOS)
        # Convert PIL image to pygame surface
        mode = original_image.mode
        size = original_image.size
        data = original_image.tobytes()
        self.image = pygame.image.fromstring(data, size, mode)
        
        # Create circular mask
        self.mask = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(self.mask, (255, 255, 255, 255),
                         (radius, radius), radius)
        self.image.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

class NetworkVisualizer:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.DROPFILE)
        pygame.display.set_caption("Image Network Visualizer - Drop images to add")
        
        self.nodes = []
        self.selected_node = None
        self.clock = pygame.time.Clock()
        
        # Physics parameters
        self.gravity = 0.5
        self.spring_length = 100
        self.spring_strength = 0.03
        self.repulsion = 500
        self.damping = 0.98
        
        # UI elements
        self.font = pygame.font.Font(None, 24)
        self.instructions = [
            "Drop image files to add them",
            "Drag nodes to move them",
            "Drag one node to another to connect",
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
            # Remove all connections to this node
            for other_node in self.nodes:
                other_node.connections.discard(node)
            self.nodes.remove(node)
    
    def connect_nodes(self, node1, node2):
        if node1 != node2:
            node1.connections.add(node2)
            node2.connections.add(node1)
    
    def apply_forces(self):
        for node in self.nodes:
            if node.anchored:
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
            
            # Apply repulsion from other nodes
            for other_node in self.nodes:
                if other_node != node:
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
            padding = node.radius
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.DROPFILE:
                    # Handle dropped image file
                    image_path = event.file
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.add_image(image_path, mouse_x, mouse_y)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    for node in self.nodes:
                        dx = mouse_x - node.x
                        dy = mouse_y - node.y
                        if math.sqrt(dx*dx + dy*dy) < node.radius:
                            self.selected_node = node
                            break
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.selected_node:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        for node in self.nodes:
                            if node != self.selected_node:
                                dx = mouse_x - node.x
                                dy = mouse_y - node.y
                                if math.sqrt(dx*dx + dy*dy) < node.radius:
                                    self.connect_nodes(self.selected_node, node)
                                    break
                    self.selected_node = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.selected_node:
                        self.selected_node.anchored = not self.selected_node.anchored
                    elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and self.selected_node:
                        self.remove_node(self.selected_node)
                        self.selected_node = None
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            # Update selected node position if dragging
            if self.selected_node:
                self.selected_node.x, self.selected_node.y = pygame.mouse.get_pos()
                self.selected_node.vx = 0
                self.selected_node.vy = 0
            
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
                                (int(node.x), int(node.y)), node.radius)
                
                # Draw image
                image_rect = node.image.get_rect(center=(int(node.x), int(node.y)))
                self.screen.blit(node.image, image_rect)
                
                # Draw anchor indicator
                if node.anchored:
                    pygame.draw.circle(self.screen, (255, 0, 0),
                                    (int(node.x), int(node.y)), 5)
                
                # Highlight selected node
                if node == self.selected_node:
                    pygame.draw.circle(self.screen, (0, 255, 0),
                                    (int(node.x), int(node.y)), node.radius + 2, 2)
            
            # Draw instructions
            self.draw_instructions()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

# Example usage
if __name__ == "__main__":
    visualizer = NetworkVisualizer()
    visualizer.run()

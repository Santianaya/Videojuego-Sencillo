"""
RPG GAME - Shadow Legends
Versión completa con Pygame
Arquitectura profesional + Gráficos 2D

Autor: Claude AI Senior Developer
Tecnologías: Python 3.10+, Pygame 2.5+
"""

import pygame
import sys
import random
import json
import math
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Inicializar Pygame
pygame.init()
pygame.mixer.init()

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

class Config:
    """Configuración global del juego."""
    
    # Ventana
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FPS = 60
    TITLE = "Shadow Legends - RPG"
    
    # Colores (diseño moderno)
    COLOR_BG = (20, 20, 30)
    COLOR_PRIMARY = (100, 80, 255)
    COLOR_SECONDARY = (255, 100, 150)
    COLOR_SUCCESS = (80, 200, 120)
    COLOR_DANGER = (255, 80, 80)
    COLOR_WARNING = (255, 200, 80)
    COLOR_TEXT = (240, 240, 250)
    COLOR_TEXT_DIM = (150, 150, 160)
    COLOR_PANEL = (30, 30, 45)
    COLOR_PANEL_LIGHT = (45, 45, 65)
    
    # Gameplay
    PLAYER_SPEED = 300  # pixels/segundo
    CAMERA_SMOOTHNESS = 0.1
    
    # UI
    FONT_SIZE_SMALL = 16
    FONT_SIZE_NORMAL = 20
    FONT_SIZE_LARGE = 28
    FONT_SIZE_TITLE = 48
    
    PANEL_PADDING = 20
    BUTTON_HEIGHT = 50


# ============================================================================
# UTILIDADES Y HELPERS
# ============================================================================

class Timer:
    """Timer para animaciones y efectos temporales."""
    
    def __init__(self, duration: float):
        self.duration = duration
        self.start_time = 0
        self.active = False
    
    def start(self):
        """Inicia el timer."""
        self.start_time = pygame.time.get_ticks()
        self.active = True
    
    def update(self) -> bool:
        """Actualiza el timer. Retorna True si terminó."""
        if not self.active:
            return False
        
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
        if elapsed >= self.duration:
            self.active = False
            return True
        return False
    
    def get_progress(self) -> float:
        """Retorna el progreso (0.0 a 1.0)."""
        if not self.active:
            return 1.0
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
        return min(elapsed / self.duration, 1.0)


class Camera:
    """Cámara para seguir al jugador suavemente."""
    
    def __init__(self, width: int, height: int):
        self.camera = pygame.Rect(0, 0, width, height)
        self.target_x = 0
        self.target_y = 0
    
    def update(self, target_rect: pygame.Rect):
        """Actualiza la posición de la cámara para seguir al objetivo."""
        self.target_x = target_rect.centerx - Config.SCREEN_WIDTH // 2
        self.target_y = target_rect.centery - Config.SCREEN_HEIGHT // 2
        
        # Smooth following
        self.camera.x += (self.target_x - self.camera.x) * Config.CAMERA_SMOOTHNESS
        self.camera.y += (self.target_y - self.camera.y) * Config.CAMERA_SMOOTHNESS
    
    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Aplica el offset de la cámara a un rect."""
        return rect.move(-self.camera.x, -self.camera.y)
    
    def apply_pos(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Aplica el offset de la cámara a una posición."""
        return (pos[0] - self.camera.x, pos[1] - self.camera.y)


class ParticleSystem:
    """Sistema de partículas para efectos visuales."""
    
    @dataclass
    class Particle:
        x: float
        y: float
        vx: float
        vy: float
        life: float
        color: Tuple[int, int, int]
        size: float
    
    def __init__(self):
        self.particles: List[ParticleSystem.Particle] = []
    
    def emit(self, x: float, y: float, color: Tuple[int, int, int], count: int = 10):
        """Emite partículas en una posición."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 150)
            self.particles.append(ParticleSystem.Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(0.5, 1.5),
                color=color,
                size=random.uniform(2, 6)
            ))
    
    def update(self, dt: float):
        """Actualiza las partículas."""
        for particle in self.particles[:]:
            particle.life -= dt
            if particle.life <= 0:
                self.particles.remove(particle)
                continue
            
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 300 * dt  # Gravedad
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Dibuja las partículas."""
        for particle in self.particles:
            alpha = int(255 * (particle.life / 1.5))
            color = (*particle.color, alpha)
            pos = camera.apply_pos((int(particle.x), int(particle.y)))
            
            # Crear superficie temporal con alpha
            s = pygame.Surface((int(particle.size * 2), int(particle.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (int(particle.size), int(particle.size)), int(particle.size))
            surface.blit(s, pos)


# ============================================================================
# RECURSOS Y ASSETS
# ============================================================================

class AssetManager:
    """Gestiona la carga y caché de recursos."""
    
    def __init__(self):
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.images: Dict[str, pygame.Surface] = {}
        self._load_fonts()
        self._generate_placeholder_graphics()
    
    def _load_fonts(self):
        """Carga las fuentes del juego."""
        try:
            # Intentar cargar fuente personalizada
            self.fonts['small'] = pygame.font.Font(None, Config.FONT_SIZE_SMALL)
            self.fonts['normal'] = pygame.font.Font(None, Config.FONT_SIZE_NORMAL)
            self.fonts['large'] = pygame.font.Font(None, Config.FONT_SIZE_LARGE)
            self.fonts['title'] = pygame.font.Font(None, Config.FONT_SIZE_TITLE)
        except:
            # Fallback a fuente del sistema
            self.fonts['small'] = pygame.font.SysFont('arial', Config.FONT_SIZE_SMALL)
            self.fonts['normal'] = pygame.font.SysFont('arial', Config.FONT_SIZE_NORMAL)
            self.fonts['large'] = pygame.font.SysFont('arial', Config.FONT_SIZE_LARGE)
            self.fonts['title'] = pygame.font.SysFont('arial', Config.FONT_SIZE_TITLE, bold=True)
    
    def _generate_placeholder_graphics(self):
        """Genera gráficos placeholder para el juego."""
        
        # Jugador (diferentes clases)
        self.images['player_warrior'] = self._create_player_sprite((100, 80, 255), 'W')
        self.images['player_mage'] = self._create_player_sprite((255, 100, 150), 'M')
        self.images['player_archer'] = self._create_player_sprite((80, 200, 120), 'A')
        
        # Enemigos
        self.images['enemy_wolf'] = self._create_enemy_sprite((150, 100, 80), 'W')
        self.images['enemy_bandit'] = self._create_enemy_sprite((180, 80, 80), 'B')
        self.images['enemy_specter'] = self._create_enemy_sprite((150, 150, 200), 'S')
        self.images['enemy_boss'] = self._create_enemy_sprite((200, 50, 50), 'B', size=80)
        
        # Items
        self.images['item_potion'] = self._create_item_sprite((255, 100, 150))
        self.images['item_weapon'] = self._create_item_sprite((200, 200, 80))
        self.images['item_armor'] = self._create_item_sprite((100, 150, 200))
        
        # Terreno
        self.images['tile_grass'] = self._create_tile_sprite((80, 150, 80))
        self.images['tile_stone'] = self._create_tile_sprite((120, 120, 130))
        self.images['tile_water'] = self._create_tile_sprite((80, 120, 200))
    
    def _create_player_sprite(self, color: Tuple[int, int, int], letter: str, size: int = 50) -> pygame.Surface:
        """Crea un sprite de jugador placeholder."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Cuerpo
        pygame.draw.circle(surface, color, (size // 2, size // 2), size // 2)
        pygame.draw.circle(surface, (255, 255, 255), (size // 2, size // 2), size // 2, 3)
        
        # Letra de clase
        font = self.fonts['large']
        text = font.render(letter, True, (255, 255, 255))
        text_rect = text.get_rect(center=(size // 2, size // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def _create_enemy_sprite(self, color: Tuple[int, int, int], letter: str, size: int = 50) -> pygame.Surface:
        """Crea un sprite de enemigo placeholder."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Forma hostil
        points = [
            (size // 2, 0),
            (size, size // 3),
            (size * 2 // 3, size),
            (size // 3, size),
            (0, size // 3)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        # Letra
        font = self.fonts['normal']
        text = font.render(letter, True, (255, 255, 255))
        text_rect = text.get_rect(center=(size // 2, size // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def _create_item_sprite(self, color: Tuple[int, int, int], size: int = 30) -> pygame.Surface:
        """Crea un sprite de item placeholder."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surface, color, (0, 0, size, size), border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), (0, 0, size, size), 2, border_radius=5)
        return surface
    
    def _create_tile_sprite(self, color: Tuple[int, int, int], size: int = 64) -> pygame.Surface:
        """Crea un sprite de tile placeholder."""
        surface = pygame.Surface((size, size))
        surface.fill(color)
        
        # Textura simple
        for i in range(4):
            x = random.randint(0, size)
            y = random.randint(0, size)
            darker = tuple(max(0, c - 20) for c in color)
            pygame.draw.circle(surface, darker, (x, y), random.randint(2, 8))
        
        return surface
    
    def get_font(self, size: str = 'normal') -> pygame.font.Font:
        """Obtiene una fuente."""
        return self.fonts.get(size, self.fonts['normal'])
    
    def get_image(self, name: str) -> pygame.Surface:
        """Obtiene una imagen."""
        return self.images.get(name, self.images.get('tile_grass'))


# ============================================================================
# MODELOS DE JUEGO (Game Models)
# ============================================================================

class Personaje(ABC):
    """Clase base abstracta para personajes."""
    
    def __init__(self, nombre: str, hp: int, atk: int, defensa: int, x: int, y: int):
        self.nombre = nombre
        self.hp = hp
        self.hp_max = hp
        self.atk = atk
        self.defensa = defensa
        self.nivel = 1
        self.experiencia = 0
        
        # Posición en el mundo
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(x, y, 50, 50)
        
        # Estado
        self.vivo = True
        self.velocidad = Config.PLAYER_SPEED
        
        # Animación
        self.sprite: Optional[pygame.Surface] = None
        self.animation_timer = 0
        self.hit_flash_timer = 0
    
    @abstractmethod
    def atacar(self, objetivo: 'Personaje') -> int:
        """Realiza un ataque."""
        pass
    
    @abstractmethod
    def subir_nivel(self):
        """Sube de nivel."""
        pass
    
    def recibir_dano(self, dano: int) -> int:
        """Recibe daño."""
        dano_real = max(1, dano - self.defensa // 2)
        self.hp = max(0, self.hp - dano_real)
        self.hit_flash_timer = 0.2  # Flash blanco al recibir daño
        
        if self.hp == 0 and self.vivo:
            self.vivo = False
            self.morir()
        
        return dano_real
    
    def curarse(self, cantidad: int):
        """Restaura HP."""
        self.hp = min(self.hp_max, self.hp + cantidad)
    
    def morir(self):
        """Maneja la muerte."""
        print(f"{self.nombre} ha sido derrotado!")
    
    def update(self, dt: float):
        """Actualiza el personaje."""
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt
        
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Dibuja el personaje."""
        if not self.vivo:
            return
        
        screen_rect = camera.apply(self.rect)
        
        # Flash blanco al recibir daño
        if self.hit_flash_timer > 0:
            flash_surface = pygame.Surface((self.rect.width, self.rect.height))
            flash_surface.fill((255, 255, 255))
            flash_surface.set_alpha(int(self.hit_flash_timer * 255))
            surface.blit(flash_surface, screen_rect)
        
        # Sprite
        if self.sprite:
            surface.blit(self.sprite, screen_rect)
        
        # Barra de vida
        self._draw_health_bar(surface, screen_rect)
    
    def _draw_health_bar(self, surface: pygame.Surface, screen_rect: pygame.Rect):
        """Dibuja la barra de vida encima del personaje."""
        bar_width = 50
        bar_height = 6
        bar_x = screen_rect.centerx - bar_width // 2
        bar_y = screen_rect.y - 10
        
        # Fondo
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Vida actual
        hp_ratio = self.hp / self.hp_max
        current_width = int(bar_width * hp_ratio)
        
        # Color según vida
        if hp_ratio > 0.6:
            color = Config.COLOR_SUCCESS
        elif hp_ratio > 0.3:
            color = Config.COLOR_WARNING
        else:
            color = Config.COLOR_DANGER
        
        pygame.draw.rect(surface, color, (bar_x, bar_y, current_width, bar_height))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)


class Jugador(Personaje):
    """Personaje controlado por el jugador."""
    
    CLASES = {
        "Guerrero": {"hp": 120, "atk": 15, "defensa": 10, "sprite": "player_warrior"},
        "Mago": {"hp": 80, "atk": 20, "defensa": 5, "sprite": "player_mage"},
        "Arquero": {"hp": 100, "atk": 18, "defensa": 7, "sprite": "player_archer"}
    }
    
    def __init__(self, nombre: str, clase: str, x: int, y: int, asset_manager: AssetManager):
        stats = self.CLASES[clase]
        super().__init__(nombre, stats["hp"], stats["atk"], stats["defensa"], x, y)
        
        self.clase = clase
        self.oro = 100
        self.inventario: List['Objeto'] = []
        self.misiones: List['Mision'] = []
        self.sprite = asset_manager.get_image(stats["sprite"])
    
    def atacar(self, objetivo: Personaje) -> int:
        """Ataca a un objetivo."""
        dano = self.atk
        if random.random() < 0.1:  # Crítico
            dano *= 2
        return objetivo.recibir_dano(dano)
    
    def subir_nivel(self):
        """Sube de nivel."""
        self.nivel += 1
        self.hp_max += 10
        self.hp = self.hp_max
        self.atk += 2
        self.defensa += 1
    
    def mover(self, dx: float, dy: float, dt: float):
        """Mueve al jugador."""
        self.x += dx * self.velocidad * dt
        self.y += dy * self.velocidad * dt


class Enemigo(Personaje):
    """Enemigo del juego."""
    
    def __init__(self, nombre: str, hp: int, atk: int, defensa: int, 
                 tipo: str, recompensa: Dict, x: int, y: int, asset_manager: AssetManager):
        super().__init__(nombre, hp, atk, defensa, x, y)
        self.tipo = tipo
        self.recompensa = recompensa
        self.patron_ataque = "simple"
        
        # Sprite según tipo
        sprite_map = {
            "Lobo Salvaje": "enemy_wolf",
            "Bandido": "enemy_bandit",
            "Espectro": "enemy_specter",
            "Señor de las Sombras": "enemy_boss"
        }
        self.sprite = asset_manager.get_image(sprite_map.get(nombre, "enemy_wolf"))
        
        # IA simple
        self.wander_timer = 0
        self.wander_direction = (0, 0)
    
    def atacar(self, objetivo: Personaje) -> int:
        """Ataca a un objetivo."""
        dano = self.atk
        if random.random() < 0.1:
            dano *= 2
        return objetivo.recibir_dano(dano)
    
    def subir_nivel(self):
        """Los enemigos no suben de nivel."""
        pass
    
    def update(self, dt: float, jugador: Optional[Jugador] = None):
        """Actualiza el enemigo (IA básica)."""
        super().update(dt)
        
        if not self.vivo:
            return
        
        # IA: Vagar aleatoriamente
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_timer = random.uniform(1, 3)
            angle = random.uniform(0, math.pi * 2)
            self.wander_direction = (math.cos(angle), math.sin(angle))
        
        # Moverse
        speed = 50  # Más lento que el jugador
        self.x += self.wander_direction[0] * speed * dt
        self.y += self.wander_direction[1] * speed * dt
    
    def soltar_recompensa(self, jugador: Jugador):
        """Otorga recompensa al jugador."""
        jugador.experiencia += self.recompensa["experiencia"]
        jugador.oro += self.recompensa["oro"]


# ============================================================================
# OBJETOS Y MISIONES
# ============================================================================

class Objeto:
    """Objeto del inventario."""
    
    def __init__(self, nombre: str, descripcion: str, tipo: str, 
                 valor: int, modificador: int, asset_manager: AssetManager):
        self.nombre = nombre
        self.descripcion = descripcion
        self.tipo = tipo
        self.valor = valor
        self.modificador = modificador
        
        # Sprite
        sprite_map = {
            "consumible": "item_potion",
            "arma": "item_weapon",
            "armadura": "item_armor"
        }
        self.sprite = asset_manager.get_image(sprite_map.get(tipo, "item_potion"))
    
    def usar(self, personaje: Personaje) -> bool:
        """Usa el objeto."""
        if self.tipo == "consumible":
            if "vida" in self.nombre.lower() or "poción" in self.nombre.lower():
                personaje.curarse(self.modificador)
                return True
        return False


class Mision:
    """Misión del juego."""
    
    def __init__(self, nombre: str, descripcion: str, requisitos: Dict, recompensa: Dict):
        self.nombre = nombre
        self.descripcion = descripcion
        self.requisitos = requisitos
        self.recompensa = recompensa
        self.completada = False
        self.progreso = {
            "enemigos": {e: 0 for e in requisitos.get("enemigos", {})},
            "objetos": {o: 0 for o in requisitos.get("objetos", {})}
        }
    
    def actualizar_progreso(self, tipo: str, objetivo: str):
        """Actualiza el progreso."""
        if tipo in self.progreso and objetivo in self.progreso[tipo]:
            self.progreso[tipo][objetivo] += 1
            self._verificar_completada()
    
    def _verificar_completada(self):
        """Verifica si la misión está completa."""
        for tipo, req in self.requisitos.items():
            for objetivo, cantidad in req.items():
                if self.progreso[tipo].get(objetivo, 0) < cantidad:
                    return
        self.completada = True


# ============================================================================
# UI COMPONENTS
# ============================================================================

class Button:
    """Botón UI clickeable."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 asset_manager: AssetManager, color: Tuple[int, int, int] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color or Config.COLOR_PRIMARY
        self.hover_color = tuple(min(255, c + 30) for c in self.color)
        self.font = asset_manager.get_font('normal')
        self.is_hovered = False
    
    def update(self, mouse_pos: Tuple[int, int]):
        """Actualiza el estado hover."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface: pygame.Surface):
        """Dibuja el botón."""
        color = self.hover_color if self.is_hovered else self.color
        
        # Fondo
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, Config.COLOR_TEXT, self.rect, 2, border_radius=8)
        
        # Texto
        text_surface = self.font.render(self.text, True, Config.COLOR_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Verifica si fue clickeado."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.is_hovered
        return False


class Panel:
    """Panel UI contenedor."""
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.visible = True
    
    def draw(self, surface: pygame.Surface, asset_manager: AssetManager):
        """Dibuja el panel."""
        if not self.visible:
            return
        
        # Fondo con borde
        pygame.draw.rect(surface, Config.COLOR_PANEL, self.rect, border_radius=10)
        pygame.draw.rect(surface, Config.COLOR_PRIMARY, self.rect, 3, border_radius=10)
        
        # Título
        if self.title:
            font = asset_manager.get_font('large')
            text = font.render(self.title, True, Config.COLOR_TEXT)
            text_rect = text.get_rect(midtop=(self.rect.centerx, self.rect.y + 15))
            surface.blit(text, text_rect)


class HUD:
    """Heads-Up Display del juego."""
    
    def __init__(self, asset_manager: AssetManager):
        self.asset_manager = asset_manager
        self.font = asset_manager.get_font('normal')
        self.font_small = asset_manager.get_font('small')
    
    def draw(self, surface: pygame.Surface, jugador: Jugador):
        """Dibuja el HUD."""
        padding = 20
        
        # Panel de estadísticas (esquina superior izquierda)
        stats_panel = pygame.Rect(padding, padding, 250, 120)
        pygame.draw.rect(surface, Config.COLOR_PANEL, stats_panel, border_radius=10)
        pygame.draw.rect(surface, Config.COLOR_PRIMARY, stats_panel, 2, border_radius=10)
        
        # Nombre y nivel
        y_offset = stats_panel.y + 15
        text = self.font.render(f"{jugador.nombre} - Nivel {jugador.nivel}", True, Config.COLOR_TEXT)
        surface.blit(text, (stats_panel.x + 15, y_offset))
        
        # Barra de vida
        y_offset += 30
        self._draw_stat_bar(surface, stats_panel.x + 15, y_offset, 220, 20,
                           jugador.hp, jugador.hp_max, "HP", Config.COLOR_SUCCESS)
        
        # Estadísticas
        y_offset += 35
        stats_text = f"ATK: {jugador.atk}  DEF: {jugador.defensa}  ORO: {jugador.oro}"
        text = self.font_small.render(stats_text, True, Config.COLOR_TEXT_DIM)
        surface.blit(text, (stats_panel.x + 15, y_offset))
        
        # Experiencia (barra inferior)
        exp_needed = jugador.nivel * 100
        exp_bar_y = Config.SCREEN_HEIGHT - 40
        self._draw_stat_bar(surface, padding, exp_bar_y, 300, 20,
                           jugador.experiencia, exp_needed, "EXP", Config.COLOR_WARNING)
    
    def _draw_stat_bar(self, surface: pygame.Surface, x: int, y: int, width: int, height: int,
                      current: int, maximum: int, label: str, color: Tuple[int, int, int]):
        """Dibuja una barra de estadística."""
        # Fondo
        pygame.draw.rect(surface, (40, 40, 50), (x, y, width, height), border_radius=5)
        
        # Progreso
        ratio = min(1.0, current / maximum) if maximum > 0 else 0
        fill_width = int(width * ratio)
        pygame.draw.rect(surface, color, (x, y, fill_width, height), border_radius=5)
        
        # Borde
        pygame.draw.rect(surface, Config.COLOR_TEXT, (x, y, width, height), 2, border_radius=5)
        
        # Texto
        text = self.font_small.render(f"{label}: {current}/{maximum}", True, Config.COLOR_TEXT)
        text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(text, text_rect)


# ============================================================================
# GESTIÓN DE ESTADOS (State Management)
# ============================================================================

class GameState(Enum):
    """Estados del juego."""
    MENU_PRINCIPAL = "menu"
    CREACION_PERSONAJE = "creacion"
    JUGANDO = "jugando"
    COMBATE = "combate"
    INVENTARIO = "inventario"
    PAUSA = "pausa"
    GAME_OVER = "gameover"
    VICTORIA = "victoria"


class State(ABC):
    """Clase base para estados del juego."""
    
    def __init__(self, game: 'Game'):
        self.game = game
    
    @abstractmethod
    def enter(self):
        """Se llama al entrar al estado."""
        pass
    
    @abstractmethod
    def exit(self):
        """Se llama al salir del estado."""
        pass
    
    @abstractmethod
    def update(self, dt: float):
        """Actualiza el estado."""
        pass
    
    @abstractmethod
    def draw(self, surface: pygame.Surface):
        """Dibuja el estado."""
        pass
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos."""
        pass


class MenuState(State):
    """Estado del menú principal."""
    
    def enter(self):
        """Inicializa el menú."""
        center_x = Config.SCREEN_WIDTH // 2
        button_width = 300
        button_x = center_x - button_width // 2
        
        self.buttons = [
            Button(button_x, 300, button_width, Config.BUTTON_HEIGHT,
                  "Nuevo Juego", self.game.asset_manager),
            Button(button_x, 370, button_width, Config.BUTTON_HEIGHT,
                  "Cargar Partida", self.game.asset_manager),
            Button(button_x, 440, button_width, Config.BUTTON_HEIGHT,
                  "Salir", self.game.asset_manager, Config.COLOR_DANGER)
        ]
        
        self.title_offset = 0
        self.title_direction = 1
    
    def exit(self):
        """Limpia el menú."""
        pass
    
    def update(self, dt: float):
        """Actualiza el menú."""
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
        
        # Animación del título
        self.title_offset += 30 * dt * self.title_direction
        if abs(self.title_offset) > 10:
            self.title_direction *= -1
    
    def draw(self, surface: pygame.Surface):
        """Dibuja el menú."""
        surface.fill(Config.COLOR_BG)
        
        # Título animado
        font_title = self.game.asset_manager.get_font('title')
        title = font_title.render("SHADOW LEGENDS", True, Config.COLOR_PRIMARY)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, 150 + self.title_offset))
        surface.blit(title, title_rect)
        
        # Subtítulo
        font_large = self.game.asset_manager.get_font('large')
        subtitle = font_large.render("RPG ADVENTURE", True, Config.COLOR_SECONDARY)
        subtitle_rect = subtitle.get_rect(center=(Config.SCREEN_WIDTH // 2, 200))
        surface.blit(subtitle, subtitle_rect)
        
        # Botones
        for button in self.buttons:
            button.draw(surface)
    
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos del menú."""
        if self.buttons[0].is_clicked(event):  # Nuevo Juego
            self.game.change_state(GameState.CREACION_PERSONAJE)
        elif self.buttons[1].is_clicked(event):  # Cargar
            # TODO: Implementar carga
            pass
        elif self.buttons[2].is_clicked(event):  # Salir
            self.game.running = False


class CreacionPersonajeState(State):
    """Estado de creación de personaje."""
    
    def enter(self):
        """Inicializa la creación."""
        self.nombre = ""
        self.clase_seleccionada = None
        self.input_active = True
        
        # Botones de clases
        center_x = Config.SCREEN_WIDTH // 2
        button_width = 250
        start_y = 300
        spacing = 80
        
        self.class_buttons = []
        for i, clase in enumerate(Jugador.CLASES.keys()):
            x = center_x - button_width // 2
            y = start_y + i * spacing
            self.class_buttons.append(
                Button(x, y, button_width, Config.BUTTON_HEIGHT,
                      clase, self.game.asset_manager)
            )
        
        # Botón confirmar
        self.confirm_button = Button(
            center_x - 150, Config.SCREEN_HEIGHT - 100, 300, Config.BUTTON_HEIGHT,
            "Confirmar", self.game.asset_manager, Config.COLOR_SUCCESS
        )
    
    def exit(self):
        """Sale de la creación."""
        pass
    
    def update(self, dt: float):
        """Actualiza la creación."""
        mouse_pos = pygame.mouse.get_pos()
        for button in self.class_buttons:
            button.update(mouse_pos)
        self.confirm_button.update(mouse_pos)
    
    def draw(self, surface: pygame.Surface):
        """Dibuja la creación."""
        surface.fill(Config.COLOR_BG)
        
        font_large = self.game.asset_manager.get_font('large')
        font_normal = self.game.asset_manager.get_font('normal')
        
        # Título
        title = font_large.render("CREACIÓN DE PERSONAJE", True, Config.COLOR_PRIMARY)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, 50))
        surface.blit(title, title_rect)
        
        # Input de nombre
        name_label = font_normal.render("Nombre:", True, Config.COLOR_TEXT)
        surface.blit(name_label, (Config.SCREEN_WIDTH // 2 - 200, 150))
        
        name_rect = pygame.Rect(Config.SCREEN_WIDTH // 2 - 150, 180, 300, 40)
        pygame.draw.rect(surface, Config.COLOR_PANEL, name_rect, border_radius=5)
        pygame.draw.rect(surface, Config.COLOR_PRIMARY if self.input_active else Config.COLOR_TEXT_DIM,
                        name_rect, 2, border_radius=5)
        
        name_text = font_normal.render(self.nombre + ("_" if self.input_active else ""),
                                       True, Config.COLOR_TEXT)
        surface.blit(name_text, (name_rect.x + 10, name_rect.y + 10))
        
        # Label de clase
        class_label = font_normal.render("Selecciona tu clase:", True, Config.COLOR_TEXT)
        surface.blit(class_label, (Config.SCREEN_WIDTH // 2 - 100, 250))
        
        # Botones de clase
        for i, button in enumerate(self.class_buttons):
            button.draw(surface)
            
            # Highlight si está seleccionada
            if self.clase_seleccionada == list(Jugador.CLASES.keys())[i]:
                pygame.draw.rect(surface, Config.COLOR_SUCCESS, button.rect, 4, border_radius=8)
        
        # Botón confirmar (solo si hay nombre y clase)
        if self.nombre and self.clase_seleccionada:
            self.confirm_button.draw(surface)
    
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos de creación."""
        # Input de texto
        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_BACKSPACE:
                self.nombre = self.nombre[:-1]
            elif event.key == pygame.K_RETURN:
                self.input_active = False
            elif len(self.nombre) < 15 and event.unicode.isprintable():
                self.nombre += event.unicode
        
        # Selección de clase
        for i, button in enumerate(self.class_buttons):
            if button.is_clicked(event):
                self.clase_seleccionada = list(Jugador.CLASES.keys())[i]
        
        # Confirmar
        if self.confirm_button.is_clicked(event):
            if self.nombre and self.clase_seleccionada:
                # Crear jugador
                self.game.jugador = Jugador(
                    self.nombre,
                    self.clase_seleccionada,
                    Config.SCREEN_WIDTH // 2,
                    Config.SCREEN_HEIGHT // 2,
                    self.game.asset_manager
                )
                
                # Dar pociones iniciales
                for _ in range(2):
                    pocion = Objeto("Poción de Vida", "Restaura 20 HP", "consumible",
                                   50, 20, self.game.asset_manager)
                    self.game.jugador.inventario.append(pocion)
                
                # Ir al juego
                self.game.change_state(GameState.JUGANDO)


class JugandoState(State):
    """Estado principal de juego (exploración)."""
    
    def enter(self):
        """Inicializa el juego."""
        # Solo inicializar una vez
        if not hasattr(self, 'camera'):
            self.camera = Camera(Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
            self.hud = HUD(self.game.asset_manager)
            self.particles = ParticleSystem()
            
            # Generar mundo
            self.enemigos: List[Enemigo] = []
            self._generar_enemigos()
            
            # Teclas presionadas
            self.keys = {
                'up': False,
                'down': False,
                'left': False,
                'right': False
            }
        
        # Limpiar estados de teclas al volver
        for key in self.keys:
            self.keys[key] = False
    
    def _generar_enemigos(self):
        """Genera enemigos en posiciones aleatorias."""
        enemigos_data = [
            ("Lobo Salvaje", 40, 10, 2, "bestia", {"oro": 20, "experiencia": 50}),
            ("Bandido", 60, 15, 5, "humano", {"oro": 40, "experiencia": 80}),
        ]
        
        for _ in range(5):  # 5 enemigos
            data = random.choice(enemigos_data)
            x = random.randint(100, 1500)
            y = random.randint(100, 1500)
            enemigo = Enemigo(*data, x, y, self.game.asset_manager)
            self.enemigos.append(enemigo)
    
    def exit(self):
        """Sale del estado de juego."""
        pass
    
    def update(self, dt: float):
        """Actualiza el juego."""
        jugador = self.game.jugador
        
        # Validación de seguridad
        if not jugador:
            return
        
        # Movimiento del jugador
        dx = 0
        dy = 0
        if self.keys['up']:
            dy = -1
        if self.keys['down']:
            dy = 1
        if self.keys['left']:
            dx = -1
        if self.keys['right']:
            dx = 1
        
        # Normalizar diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        
        jugador.mover(dx, dy, dt)
        jugador.update(dt)  # ¡IMPORTANTE! Actualizar el jugador
        
        # Actualizar enemigos
        for enemigo in self.enemigos[:]:
            if not enemigo.vivo:
                self.enemigos.remove(enemigo)
                continue
            
            enemigo.update(dt, jugador)
            
            # Colisión con jugador (iniciar combate)
            if jugador.rect.colliderect(enemigo.rect):
                self.game.enemigo_actual = enemigo
                self.game.change_state(GameState.COMBATE)
                return
        
        # Actualizar cámara
        self.camera.update(jugador.rect)
        
        # Actualizar partículas
        self.particles.update(dt)
    
    def draw(self, surface: pygame.Surface):
        """Dibuja el juego."""
        surface.fill(Config.COLOR_BG)
        
        # Dibujar mundo (tiles)
        self._draw_world(surface)
        
        # Dibujar jugador
        self.game.jugador.draw(surface, self.camera)
        
        # Dibujar enemigos
        for enemigo in self.enemigos:
            enemigo.draw(surface, self.camera)
        
        # Partículas
        self.particles.draw(surface, self.camera)
        
        # HUD
        self.hud.draw(surface, self.game.jugador)
        
        # Instrucciones en pantalla (temporal para debugging)
        font_small = self.game.asset_manager.get_font('small')
        instrucciones = [
            "Controles:",
            "WASD o Flechas - Mover",
            "I - Inventario",
            "ESC - Pausa"
        ]
        y_offset = Config.SCREEN_HEIGHT - 100
        for texto in instrucciones:
            text_surface = font_small.render(texto, True, Config.COLOR_TEXT_DIM)
            surface.blit(text_surface, (Config.SCREEN_WIDTH - 200, y_offset))
            y_offset += 20
    
    def _draw_world(self, surface: pygame.Surface):
        """Dibuja el mundo de tiles."""
        tile_size = 64
        tile = self.game.asset_manager.get_image('tile_grass')
        
        # Calcular qué tiles son visibles
        start_x = int(self.camera.camera.x // tile_size)
        end_x = int((self.camera.camera.x + Config.SCREEN_WIDTH) // tile_size) + 1
        start_y = int(self.camera.camera.y // tile_size)
        end_y = int((self.camera.camera.y + Config.SCREEN_HEIGHT) // tile_size) + 1
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                world_x = x * tile_size
                world_y = y * tile_size
                screen_pos = self.camera.apply_pos((world_x, world_y))
                surface.blit(tile, screen_pos)
    
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos del juego."""
        # Teclas
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.keys['up'] = True
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.keys['down'] = True
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self.keys['left'] = True
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.keys['right'] = True
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.PAUSA)
            elif event.key == pygame.K_i:
                self.game.change_state(GameState.INVENTARIO)
        
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.keys['up'] = False
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.keys['down'] = False
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self.keys['left'] = False
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.keys['right'] = False


class CombateState(State):
    """Estado de combate por turnos."""
    
    def enter(self):
        """Inicializa el combate."""
        self.turno_jugador = True
        self.animando = False
        self.animation_timer = Timer(0.5)
        self.mensaje = ""
        self.resultado = None  # "victoria" o "derrota"
        
        # Botones de combate
        button_width = 200
        button_height = 50
        spacing = 20
        start_x = Config.SCREEN_WIDTH // 2 - button_width - spacing
        start_y = Config.SCREEN_HEIGHT - 150
        
        self.attack_button = Button(start_x, start_y, button_width, button_height,
                                    "Atacar", self.game.asset_manager, Config.COLOR_DANGER)
        self.item_button = Button(start_x + button_width + spacing, start_y,
                                  button_width, button_height,
                                  "Usar Objeto", self.game.asset_manager, Config.COLOR_SUCCESS)
    
    def exit(self):
        """Sale del combate."""
        self.game.enemigo_actual = None
    
    def update(self, dt: float):
        """Actualiza el combate."""
        if self.animando:
            if self.animation_timer.update():
                self.animando = False
                
                # Verificar fin de combate
                if not self.game.jugador.vivo:
                    self.resultado = "derrota"
                elif not self.game.enemigo_actual.vivo:
                    self.resultado = "victoria"
                    self.game.enemigo_actual.soltar_recompensa(self.game.jugador)
                    
                    # Subir nivel si es necesario
                    if self.game.jugador.experiencia >= self.game.jugador.nivel * 100:
                        self.game.jugador.subir_nivel()
                        self.game.jugador.experiencia = 0
                
                # Turno del enemigo si sigue vivo
                elif self.turno_jugador and self.game.enemigo_actual.vivo:
                    self.turno_jugador = False
                    self._turno_enemigo()
                else:
                    self.turno_jugador = True
            return
        
        # Actualizar botones
        if self.turno_jugador and not self.resultado:
            mouse_pos = pygame.mouse.get_pos()
            self.attack_button.update(mouse_pos)
            self.item_button.update(mouse_pos)
    
    def _turno_enemigo(self):
        """Ejecuta el turno del enemigo."""
        dano = self.game.enemigo_actual.atacar(self.game.jugador)
        self.mensaje = f"{self.game.enemigo_actual.nombre} ataca causando {dano} de daño!"
        self.animando = True
        self.animation_timer.start()
    
    def draw(self, surface: pygame.Surface):
        """Dibuja el combate."""
        surface.fill(Config.COLOR_BG)
        
        # Panel de combate
        panel = Panel(100, 50, Config.SCREEN_WIDTH - 200, Config.SCREEN_HEIGHT - 200,
                     "COMBATE")
        panel.draw(surface, self.game.asset_manager)
        
        # Dibujar jugador y enemigo
        jugador = self.game.jugador
        enemigo = self.game.enemigo_actual
        
        # Jugador (izquierda)
        jugador_x = 250
        jugador_y = Config.SCREEN_HEIGHT // 2
        surface.blit(jugador.sprite, (jugador_x, jugador_y - 25))
        
        # Stats jugador
        font = self.game.asset_manager.get_font('normal')
        stats = font.render(f"{jugador.nombre} - HP: {jugador.hp}/{jugador.hp_max}",
                           True, Config.COLOR_TEXT)
        surface.blit(stats, (jugador_x, jugador_y + 40))
        
        # Enemigo (derecha)
        enemigo_x = Config.SCREEN_WIDTH - 300
        enemigo_y = Config.SCREEN_HEIGHT // 2
        if enemigo.vivo:
            surface.blit(enemigo.sprite, (enemigo_x, enemigo_y - 25))
            
            # Stats enemigo
            stats = font.render(f"{enemigo.nombre} - HP: {enemigo.hp}/{enemigo.hp_max}",
                               True, Config.COLOR_TEXT)
            surface.blit(stats, (enemigo_x - 50, enemigo_y + 40))
        
        # Mensaje de combate
        if self.mensaje:
            msg = self.game.asset_manager.get_font('large').render(self.mensaje, True, Config.COLOR_WARNING)
            msg_rect = msg.get_rect(center=(Config.SCREEN_WIDTH // 2, 150))
            surface.blit(msg, msg_rect)
        
        # Resultado
        if self.resultado:
            font_title = self.game.asset_manager.get_font('title')
            if self.resultado == "victoria":
                text = font_title.render("¡VICTORIA!", True, Config.COLOR_SUCCESS)
            else:
                text = font_title.render("DERROTA", True, Config.COLOR_DANGER)
            
            text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2))
            surface.blit(text, text_rect)
            
            # Botón continuar
            continue_button = Button(Config.SCREEN_WIDTH // 2 - 100, Config.SCREEN_HEIGHT - 100,
                                    200, 50, "Continuar", self.game.asset_manager)
            continue_button.draw(surface)
        
        # Botones (solo en turno del jugador)
        elif self.turno_jugador and not self.animando:
            self.attack_button.draw(surface)
            self.item_button.draw(surface)
    
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos del combate."""
        if self.resultado:
            # Cualquier click continúa
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.resultado == "victoria":
                    self.game.change_state(GameState.JUGANDO)
                else:
                    self.game.change_state(GameState.GAME_OVER)
            return
        
        if not self.turno_jugador or self.animando:
            return
        
        # Atacar
        if self.attack_button.is_clicked(event):
            dano = self.game.jugador.atacar(self.game.enemigo_actual)
            critico = " (¡CRÍTICO!)" if dano >= self.game.jugador.atk * 1.5 else ""
            self.mensaje = f"¡Atacas causando {dano} de daño{critico}!"
            self.animando = True
            self.animation_timer.start()
        
        # Usar objeto
        elif self.item_button.is_clicked(event):
            if self.game.jugador.inventario:
                # Usar primera poción disponible
                for obj in self.game.jugador.inventario:
                    if obj.tipo == "consumible":
                        obj.usar(self.game.jugador)
                        self.game.jugador.inventario.remove(obj)
                        self.mensaje = f"Usas {obj.nombre}. HP +{obj.modificador}"
                        self.animando = True
                        self.animation_timer.start()
                        break
            else:
                self.mensaje = "¡No tienes objetos!"


class InventarioState(State):
    """Estado del inventario."""
    
    def enter(self):
        """Inicializa el inventario."""
        self.selected_index = 0
    
    def exit(self):
        """Sale del inventario."""
        pass
    
    def update(self, dt: float):
        """Actualiza el inventario."""
        pass
    
    def draw(self, surface: pygame.Surface):
        """Dibuja el inventario."""
        surface.fill(Config.COLOR_BG)
        
        # Panel
        panel = Panel(200, 100, Config.SCREEN_WIDTH - 400, Config.SCREEN_HEIGHT - 200,
                     "INVENTARIO")
        panel.draw(surface, self.game.asset_manager)
        
        # Listar objetos
        font = self.game.asset_manager.get_font('normal')
        y_offset = 180
        
        if not self.game.jugador.inventario:
            text = font.render("Inventario vacío", True, Config.COLOR_TEXT_DIM)
            surface.blit(text, (Config.SCREEN_WIDTH // 2 - 100, Config.SCREEN_HEIGHT // 2))
        else:
            for i, obj in enumerate(self.game.jugador.inventario):
                color = Config.COLOR_PRIMARY if i == self.selected_index else Config.COLOR_TEXT
                text = font.render(f"{i+1}. {obj.nombre} - {obj.descripcion}", True, color)
                surface.blit(text, (250, y_offset))
                y_offset += 40
        
        # Instrucciones
        instructions = font.render("ESC para cerrar", True, Config.COLOR_TEXT_DIM)
        surface.blit(instructions, (250, Config.SCREEN_HEIGHT - 150))
    
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos del inventario."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.JUGANDO)


class PausaState(State):
    """Estado de pausa."""
    
    def enter(self):
        """Inicializa la pausa."""
        center_x = Config.SCREEN_WIDTH // 2
        button_width = 300
        
        self.buttons = [
            Button(center_x - button_width // 2, 300, button_width, Config.BUTTON_HEIGHT,
                  "Continuar", self.game.asset_manager),
            Button(center_x - button_width // 2, 370, button_width, Config.BUTTON_HEIGHT,
                  "Guardar Partida", self.game.asset_manager),
            Button(center_x - button_width // 2, 440, button_width, Config.BUTTON_HEIGHT,
                  "Menú Principal", self.game.asset_manager, Config.COLOR_DANGER)
        ]
    
    def exit(self):
        """Sale de la pausa."""
        pass
    
    def update(self, dt: float):
        """Actualiza la pausa."""
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
    
    def draw(self, surface: pygame.Surface):
        """Dibuja la pausa."""
        surface.fill(Config.COLOR_BG)
        
        # Título
        font = self.game.asset_manager.get_font('title')
        title = font.render("PAUSA", True, Config.COLOR_PRIMARY)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(title, title_rect)
        
        # Botones
        for button in self.buttons:
            button.draw(surface)
    
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos de la pausa."""
        if self.buttons[0].is_clicked(event):  # Continuar
            self.game.change_state(GameState.JUGANDO)
        elif self.buttons[1].is_clicked(event):  # Guardar
            # TODO: Implementar guardado
            pass
        elif self.buttons[2].is_clicked(event):  # Menú
            self.game.change_state(GameState.MENU_PRINCIPAL)
        
        # ESC también continúa
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_state(GameState.JUGANDO)


class GameOverState(State):
    """Estado de game over."""
    
    def enter(self):
        """Inicializa game over."""
        self.button = Button(Config.SCREEN_WIDTH // 2 - 150, 400, 300, Config.BUTTON_HEIGHT,
                           "Menú Principal", self.game.asset_manager)
    
    def exit(self):
        """Sale de game over."""
        pass
    
    def update(self, dt: float):
        """Actualiza game over."""
        self.button.update(pygame.mouse.get_pos())
    
    def draw(self, surface: pygame.Surface):
        """Dibuja game over."""
        surface.fill((20, 0, 0))  # Tono rojizo
        
        font = self.game.asset_manager.get_font('title')
        title = font.render("GAME OVER", True, Config.COLOR_DANGER)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, 200))
        surface.blit(title, title_rect)
        
        self.button.draw(surface)
    
    def handle_event(self, event: pygame.event.Event):
        """Maneja eventos de game over."""
        if self.button.is_clicked(event):
            self.game.change_state(GameState.MENU_PRINCIPAL)


# ============================================================================
# CLASE PRINCIPAL DEL JUEGO
# ============================================================================

class Game:
    """Clase principal que gestiona todo el juego."""
    
    def __init__(self):
        # Pygame setup
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption(Config.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Asset manager
        self.asset_manager = AssetManager()
        
        # Estado
        self.states: Dict[GameState, State] = {}
        self.current_state: Optional[State] = None
        self._init_states()
        
        # Datos del juego
        self.jugador: Optional[Jugador] = None
        self.enemigo_actual: Optional[Enemigo] = None
    
    def _init_states(self):
        """Inicializa todos los estados."""
        self.states = {
            GameState.MENU_PRINCIPAL: MenuState(self),
            GameState.CREACION_PERSONAJE: CreacionPersonajeState(self),
            GameState.JUGANDO: JugandoState(self),
            GameState.COMBATE: CombateState(self),
            GameState.INVENTARIO: InventarioState(self),
            GameState.PAUSA: PausaState(self),
            GameState.GAME_OVER: GameOverState(self),
        }
        
        # Comenzar en el menú
        self.change_state(GameState.MENU_PRINCIPAL)
    
    def change_state(self, new_state: GameState):
        """Cambia al nuevo estado."""
        if self.current_state:
            self.current_state.exit()
        
        self.current_state = self.states[new_state]
        self.current_state.enter()
    
    def run(self):
        """Loop principal del juego."""
        while self.running:
            # Delta time (importante para movimiento fluido)
            dt = self.clock.tick(Config.FPS) / 1000.0
            
            # Eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_state.handle_event(event)
            
            # Actualizar
            self.current_state.update(dt)
            
            # Dibujar
            self.current_state.draw(self.screen)
            
            # FPS counter (debug)
            fps = self.asset_manager.get_font('small').render(
                f"FPS: {int(self.clock.get_fps())}", True, Config.COLOR_TEXT_DIM
            )
            self.screen.blit(fps, (10, 10))
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()
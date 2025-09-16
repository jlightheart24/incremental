# Kingdom Hearts-Inspired Game Architecture (Python + Pygame)

This document defines the **UML architecture** for the game. It captures inheritance, composition, and associations in a pygame-aware model, with static battle presentation, XP/leveling, prestige, and save data.

## Legend

- `A <|-- B` : **Inheritance** — B is a subclass of A  
- `A *-- B` : **Composition** — A owns B, B’s lifecycle bound to A  
- `A o-- B` : **Aggregation** — A has B, but B can exist independently  
- `A --> B` : **Association/Dependency** — A depends on or uses B  

---
---

## Consolidated Class Diagram (pygame-aware)

```mermaid
classDiagram
  direction LR

  %% === Inheritance Legend ===
  %% A <|-- B  : B inherits A
  %% A *-- B   : Composition (A owns B, lifecycle-bound)
  %% A o-- B   : Aggregation (A has B, not lifecycle-bound)
  %% A --> B   : Association/Dependency

  class Game { +screen: Surface\n+clock: Clock\n+scenes: dict\n+run() }
  class Scene { <<abstract>>\n+update(dt)\n+handle_event(evt)\n+draw(surface) }
  class BattleScene { +party: Party\n+enemySlot: EnemySlot\n+combat: CombatSystem\n+render: RenderSystem\n+hud: BattleHUD\n+tick: TickController }
  Game --> Scene
  BattleScene ..|> Scene
  Game *-- BattleScene

  %% pygame-aware base
  class Sprite
  class Entity { <<abstract>>\n+id: str\n+pos: Vector2\n+health: Health }
  Entity ..|> Sprite
  class Character
  class Enemy
  Character ..|> Entity
  Enemy ..|> Entity

  %% Party
  class Party { +active: List~Character~ (size=3)\n+bench: List~Character~ (0..*) }
  class PartyManager { +switch_cooldown_s: 2.0 }
  class SwitchAction
  BattleScene *-- Party
  BattleScene o-- PartyManager
  PartyManager --> SwitchAction
  Party "3" --> "1" Character : active
  Party "0..*" --> "1" Character : bench

  %% Combat & Tick
  class CombatSystem
  class TickController { +tick_length_s: 0.2 }
  class EnemySlot { +current: Enemy }
  class DamageEvent
  BattleScene *-- CombatSystem
  BattleScene *-- TickController
  CombatSystem *-- EnemySlot
  CombatSystem --> DamageEvent
  CombatSystem --> Party

  %% Stats/HP/MP/Attacking
  class Stats { +max_hp\n+atk\n+defense\n+speed\n+mp_max }
  class Health { +current\n+max }
  class AttackProfile { +cooldown_s\n+mp_gain_on_attack=1 }
  class AttackState { +time_since_attack_s }
  class Mana { +current\n+max=10 }
  Character *-- Stats
  Entity *-- Health
  Character *-- Mana
  Character *-- AttackProfile
  Character *-- AttackState

  %% Spells & autocast
  class Spell
  class AutoCastRule
  Character o-- Spell : learns
  AutoCastRule --> Character

  %% XP / Leveling / Prestige
  class Experience { +current\n+level (1..99)\n+next_threshold }
  class LevelCurve
  class AcceleratingCurve
  class LevelEvents
  class Prestige
  Character *-- Experience
  Experience o-- LevelCurve
  LevelCurve <|.. AcceleratingCurve
  Experience --> LevelEvents
  Experience o-- Prestige

  %% XP strategy
  class XPStrategy
  class AutoAwardXP
  class XPEvent
  CombatSystem o-- XPStrategy
  XPStrategy <|.. AutoAwardXP
  XPStrategy --> XPEvent

  %% Rendering system
  class RenderSystem
  class LayeredUpdates
  class RenderLayer { <<enumeration>> BACKGROUND; ACTORS; FX; UI }
  BattleScene *-- RenderSystem
  RenderSystem *-- LayeredUpdates : actors
  RenderSystem *-- LayeredUpdates : fx
  RenderSystem *-- LayeredUpdates : ui
  RenderSystem --> RenderLayer

  %% HUD & Widgets
  class BattleHUD
  class PartyPanel
  class EnemyPanel
  class MemberHUD
  class CircularPortrait
  class ArcBarWidget
  class TailBars
  class LinearBarWidget
  class Label
  BattleScene *-- BattleHUD
  BattleHUD *-- PartyPanel
  BattleHUD *-- EnemyPanel
  PartyPanel *-- MemberHUD : slots (3)
  MemberHUD *-- CircularPortrait
  MemberHUD *-- ArcBarWidget : hpArc (inner)
  MemberHUD *-- ArcBarWidget : mpArc (outer)
  MemberHUD o-- TailBars
  TailBars *-- LinearBarWidget : hpTail
  TailBars *-- LinearBarWidget : mpTail
  EnemyPanel *-- CircularPortrait : portrait
  EnemyPanel *-- ArcBarWidget : hpArc
  EnemyPanel o-- LinearBarWidget : tailHP (optional)
```
---

## Sequence — Tick Attack / Auto‑Cast / XP
```mermaid
sequenceDiagram
  participant TC as TickController
  participant CS as CombatSystem
  participant P as Party(3 active)
  participant C as Character
  participant E as Enemy
  participant XS as XPStrategy(AutoAwardXP)

  TC->>CS: on_tick() every 0.2s
  loop for each active Character
    CS->>C: check AttackState.ready()
    alt Mana full
      C->>C: cast Spell (consume all MP)
    else Ready to attack
      C->>E: basic attack (gain +1 MP)
      CS-->>C: DamageEvent
    end
  end
  alt E HP <= 0
    CS->>XS: award(defeated=E, killer=C*)
    XS-->>C*: XPEvent(amount)
  end
```
---

## State — Enemy Lifecycle
```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Engaged: Player present
  Engaged --> Defeated: HP <= 0
  Defeated --> [*]
```
---

## Notes / Constraints
- **Party**: 3 active, bench unlimited. Benched do not act or gain XP.
- **Combat**: tick = 0.2s, attack cadence via `cooldown_s`. Damage = `max(1, ATK−DEF)`.
- **MP**: +1 per attack, max 10. When full, a Spell auto-casts and empties the bar.
- **Enemy**: single slot, portrait + circular HP arc. On defeat → replacement from `EnemyFactory`/`EncounterTable`.
- **XP**: only from enemy defeat drops, auto-awarded. Curve = accelerating quadratic, cap 99, prestige resets to level 1 with tokens and keeps spells.
- **Rendering**: pygame aware (`Entity ..|> Sprite`, RenderSystem with layered groups).
- **HUD**: Party on left, vertical; circular portraits with inner HP arc + outer MP arc + tail bars. Enemy on right with circular portrait + HP arc.
- **SaveData**: party composition, character snapshots (stats, xp, mana, spells), prestige, story flags. Inventory/depth later.
- **Inventory System**: add inventory mananagment with loadouts as well as leveling up equipment
- **Synthesis System** add sythesising different materials into potions and ether etc. as well as equipment
- **Combo System** quick time events on different abilities such as sonic blade and strike raid
- **World Select** Ability to go between worlds. Specific fourth party members on specific worlds. Multiple parties in different worlds???
- **AP system** AP collected over time ability loadout with AP
- **Drive system** add in drive and forms
- **Dive to the heart** add dive to the heart at the beginning of the game
- **Boss Batles** different functionality for boss battle. Add gimics to boss battles. bosses become able to idle after first victory.
- **Make a board** enemies on board move towards you
- **GUMMY SHIP** GUMMY SHIP
---
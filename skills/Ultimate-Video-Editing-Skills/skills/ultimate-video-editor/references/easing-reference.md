# Complete Easing & Timing Reference

## Directional Easing Rules
| Direction | Easing Family | Why |
|-----------|--------------|-----|
| **Entrance** | ease-out (decelerate) | Fast start → gentle landing. "I've arrived." |
| **Exit** | ease-in (accelerate) | Gentle start → fast departure. "I'm leaving." |
| **On-screen** | ease-in-out | Smooth both ends. Natural movement. |
| **Looping** | sine ease-in-out | Seamless, breathing, ambient. |
| **Rotation/progress** | linear | Constant speed is expected for these. |

## Industry Standard Curves
| Name | Cubic Bezier | Platform | Use Case |
|------|-------------|----------|----------|
| MD3 Standard | (0.2, 0, 0, 1) | Material Design 3 | Default on-screen movement |
| MD3 Emphasized | (0.05, 0.7, 0.1, 1) | Material Design 3 | Entrances, attention-grabbing |
| MD3 Accelerate | (0.3, 0, 1, 1) | Material Design 3 | Exits, dismissals |
| MD3 Decelerate | (0, 0, 0, 1) | Material Design 3 | Entering elements |
| Apple HIG | (0.25, 0.1, 0.25, 1) | iOS / macOS | Standard Apple animation |
| Apple Spring | stiffness:300 damping:20 | iOS / macOS | Interactive, responsive |
| Snappy UI | (0.2, 0, 0, 1) | Cross-platform | Fast, decisive interactions |
| Gentle float | (0.4, 0, 0.2, 1) | Cross-platform | Ambient, background motion |
| Bounce settle | (0.175, 0.885, 0.32, 1.275) | Cross-platform | Playful, overshoot landing |
| Elastic snap | (0.68, -0.55, 0.265, 1.55) | Cross-platform | Dramatic, attention-grabbing |

## Spring Parameters
| Feel | Stiffness | Damping | Use |
|------|-----------|---------|-----|
| Very stiff | 400+ | 25-30 | Snapping, rigid controls |
| Standard | 250-350 | 18-24 | Default UI interactions |
| Bouncy | 150-250 | 10-15 | Playful, fun interactions |
| Very bouncy | 100-200 | 5-10 | Game-like, extremely fun |

## Duration by Element Type
| Element | Duration | Notes |
|---------|----------|-------|
| Tooltip / micro-feedback | 80-120ms | Must feel instant |
| Button press / toggle | 120-180ms | Responsive |
| Icon transition | 150-250ms | Clear change |
| Card enter / exit | 200-350ms | Spatial awareness |
| Modal / dialog | 300-400ms | Focus shift |
| Page / scene transition | 400-600ms | Context switch |
| Dramatic reveal | 600-1200ms | Theatrical |
| Ambient / breathing | 2000-20000ms | Continuous life |

## Distance-Duration Scaling
| Distance | Multiplier |
|----------|-----------|
| 50px | 0.8x |
| 100px | 1.0x (base) |
| 200px | 1.3x |
| 300px | 1.5x |
| 400px | 1.6x |
| Full screen | 1.8-2.0x |

## Duration by Personality
| Personality | Quick | Standard | Slow |
|------------|-------|----------|------|
| Playful | 150ms | 250ms | 400ms |
| Premium | 350ms | 500ms | 800ms |
| Corporate | 200ms | 300ms | 450ms |
| Energetic | 100ms | 180ms | 300ms |

## Interactive Feedback Latency
| Interaction | Max Response Time |
|------------|-------------------|
| Hover | <100ms |
| Press/tap | <150ms |
| Release/settle | 200-300ms |
| Error shake | 300-400ms |
| Long press | 500-800ms |
| Drag start | <50ms |

## Enter vs Exit Rule
**Entrances = 100% (base)**. **Exits = 65-75% of entrance duration.**
Users care more about what appears than what disappears.

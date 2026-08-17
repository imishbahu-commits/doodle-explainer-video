# Choreography & Multi-Element Coordination

*Source: [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill)*

## Coordinated Entry Rules

### 1. Lead with the Hero
- Hero gets largest displacement and most attention-grabbing easing
- Supporting elements are subtler in every dimension

### 2. Spatial Origin Consistency
All elements enter from same direction or shared origin. Mixed directions = visual chaos.

### 3. Counter-Motion
| Hero Motion | Counter-Motion | Speed Ratio |
|-------------|---------------|-------------|
| Enters left | Background shifts right | 20-30% |
| Scales up | Shadow scales down | 10-20% |
| Rotates CW | Ambient drifts CCW | 15-25% |
| Lifts (Y up) | Shadow spreads + softens | 20-30% |

## Sequence Structure
| Phase | Duration Share | What Happens |
|-------|--------------|-------------|
| Setup | 20-30% | Elements enter, scene establishes |
| Action | 30-40% | Primary motion, hero moment |
| Resolution | 30-40% | Settle, secondary reactions, breathing |

Leave 100-200ms stillness after resolution before new motion.

## The 1/3 Rules

**Distance**: No motion travels >1/3 screen without intermediate keyframe. Break with direction changes, speed variations, or arc adjustments.

**Elements**: With 3+ animated elements, max 1/3 active simultaneously. Stagger so element 1 settles as element 3 starts.

## Stagger Patterns
| Pattern | Delay | Total Budget | Use Case |
|---------|-------|-------------|----------|
| Micro cascade | 20-40ms | <200ms | List items, grid cells |
| Standard | 50-100ms | <400ms | Cards, panels, nav |
| Dramatic | 100-200ms | <600ms | Hero sections, reveals |
| Wave | 30-60ms | <500ms | Data visualizations, bars |

**Critical**: Total stagger must stay under 500ms.

## Shared Motion Events
When multiple elements react to one trigger:
- All start within 50ms of each other
- Can arrive at different times (staggered landing)
- Same easing family; motion originates from trigger point

## Attention Direction
| Technique | Implementation |
|-----------|---------------|
| Leading motion | Animate target before context |
| Following motion | Settle on focal point |
| Ambient motion | Subtle continuous in periphery |
| Pointing motion | Directional toward CTA/focus |

## Depth Through Speed (Parallax)
| Layer | Displacement | Speed |
|-------|-------------|-------|
| Foreground | 1.0x | Fastest |
| Midground | 0.5x | Medium |
| Background | 0.2x | Slowest |

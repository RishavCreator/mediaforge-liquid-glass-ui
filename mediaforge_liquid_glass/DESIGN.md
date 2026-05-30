---
name: MediaForge Liquid Glass
colors:
  surface: '#131319'
  surface-dim: '#131319'
  surface-bright: '#39383f'
  surface-container-lowest: '#0e0e14'
  surface-container-low: '#1b1b21'
  surface-container: '#1f1f25'
  surface-container-high: '#2a2930'
  surface-container-highest: '#35343b'
  on-surface: '#e4e1ea'
  on-surface-variant: '#c9c4d8'
  inverse-surface: '#e4e1ea'
  inverse-on-surface: '#303036'
  outline: '#938ea1'
  outline-variant: '#484555'
  surface-tint: '#cabeff'
  primary: '#cabeff'
  on-primary: '#32009a'
  primary-container: '#947dff'
  on-primary-container: '#2b0088'
  inverse-primary: '#613de0'
  secondary: '#ffb2bb'
  on-secondary: '#670022'
  secondary-container: '#940336'
  on-secondary-container: '#ff9caa'
  tertiary: '#60dcb2'
  on-tertiary: '#003829'
  tertiary-container: '#0fa47e'
  on-tertiary-container: '#003123'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e6deff'
  primary-fixed-dim: '#cabeff'
  on-primary-fixed: '#1c0062'
  on-primary-fixed-variant: '#4918c8'
  secondary-fixed: '#ffd9dd'
  secondary-fixed-dim: '#ffb2bb'
  on-secondary-fixed: '#400012'
  on-secondary-fixed-variant: '#910033'
  tertiary-fixed: '#7ef9cd'
  tertiary-fixed-dim: '#60dcb2'
  on-tertiary-fixed: '#002116'
  on-tertiary-fixed-variant: '#00513c'
  background: '#131319'
  on-background: '#e4e1ea'
  surface-variant: '#35343b'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.02em
  data-display:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.2'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 32px
  gutter: 24px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style

The design system is built for **MediaForge**, a high-performance media conversion tool that balances professional utility with a futuristic, immersive aesthetic. The brand personality is sleek, authoritative, and technically advanced.

The visual style is **Liquid Glassmorphism**. It utilizes deep atmospheric backgrounds contrasted against translucent glass panels that appear to float in a multi-dimensional space. The interface should feel like a high-end physical console—tactile yet ethereal. We leverage fluid, organic gradients and high-fidelity depth to signify "active" processes, creating an emotional response of speed and precision.

## Colors

The palette is rooted in a deep space neutral to provide maximum contrast for the translucent glass layers and vibrant functional accents.

- **Background**: #0e0e14 (The base canvas).
- **Audio (Primary)**: Electric Purple (#7c5cfc) used for audio-specific tracks and progress.
- **Video (Secondary)**: Vibrant Pink (#fc5c7d) used for video rendering and encoding states.
- **Image (Tertiary)**: Teal (#4ecca3) used for image processing and optimization settings.
- **Surface**: The "Glass" effect is achieved through a combination of low-opacity white fills (3-8%) and high-density backdrop blurs. 
- **Accents**: Use high-saturation gradients between Primary and Secondary for multi-format processing states.

## Typography

This design system uses a dual-font strategy to balance elegance with technical precision. 

- **Geist** is used for headlines and high-level UI elements to maintain a modern, technical, and clean aesthetic.
- **Inter** handles all body copy and descriptions, ensuring maximum readability across varying glass background densities.
- **JetBrains Mono** is critical for technical metadata, logs, file paths, and conversion statistics, reinforcing the "performance tool" aspect of the system.

All type should maintain high contrast. On glass surfaces, use pure white (#FFFFFF) for primary text and a 60% opacity white for secondary/supporting text.

## Layout & Spacing

The design system employs a **fluid grid** with generous internal margins to allow the glass backgrounds to "breathe." 

- **Grid**: A 12-column system for desktop, shifting to a 4-column system for mobile.
- **Rhythm**: All spacing is based on an 8px scale.
- **Safe Areas**: Use a 32px outer margin for desktop to prevent glass edges from feeling cramped against the viewport.
- **Reflow**: On mobile, glass panels should lose their multi-layered shadows and rely on subtle 0.5px borders to maintain clarity without visual clutter.

## Elevation & Depth

Depth is the core differentiator of this design system. It is achieved through four specific layers:

1.  **Background Layer**: The solid #0e0e14 base, occasionally broken by soft, out-of-focus "liquid" blobs of color (#7c5cfc and #fc5c7d) at 10% opacity.
2.  **Surface Layer (Backdrop Blur)**: Panels use `backdrop-filter: blur(24px)`. This creates the "frosted" look.
3.  **Edge Definition**: Every glass panel must have a 0.5px solid white border at 12% opacity. Additionally, use a 1px inner-shadow (white, 10% opacity) at the top to simulate light catching the glass thickness.
4.  **Shadows**: Use multi-layered ambient shadows. A large, highly diffused shadow (40px blur, 30% alpha black) should be paired with a tighter, darker shadow (4px blur, 50% alpha black) to ground the elements.

## Shapes

The shape language is organic and highly rounded, contrasting the technical monospaced type. 

- **Panels**: Use a standard 24px (rounded-xl) corner radius to soften the technical feel.
- **Interactive Elements**: Buttons and inputs use a 12px (rounded-lg) radius.
- **Visual Continuity**: Ensure that nested elements have a smaller radius than their parent containers to maintain concentric harmony (e.g., a 24px container housing 16px cards).

## Components

### Buttons
Primary buttons should use a vibrant gradient (Electric Purple to Vibrant Pink). On hover, the gradient should shift position or increase in intensity (the "liquid" pulse effect). Ghost buttons use the 0.5px glass border and a subtle blur.

### Chips & Tags
Use JetBrains Mono for text within chips. Backgrounds should be low-opacity versions of the functional colors (e.g., 10% Teal for "Image Success").

### Input Fields
Inputs are dark translucent wells. On focus, the 0.5px border should transition to the Primary color (#7c5cfc) with a soft outer glow (glow-spread: 4px).

### Cards / Media Items
Media cards display a thumbnail with a 24px blur overlay on the bottom third to house the file name and conversion status. Use the "Liquid" gradients for progress bars, ensuring they appear to "fill" the glass container like a fluid.

### Lists
Lists use thin separator lines (white, 5% opacity). Hovering over a list item should trigger a subtle increase in the backdrop-blur value and a slight lightening of the background surface (from 3% to 7% white opacity).
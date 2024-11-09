# Style Guide for Stress Strain Analysis App

## Color Palette

Below are the primary, secondary, and accent colors used across the application. Each color includes a swatch for easy reference.

### Primary Colors
Used for key interface elements, such as buttons and headers, to create a cohesive look.

| Element            | Color Sample            | Hex Code    |
|--------------------|-------------------------|-------------|
| **Primary Background** | ![#123456](https://via.placeholder.com/20/123456/123456.png) | `#123456` |
| **Primary Text**       | ![#FFFFFF](https://via.placeholder.com/20/FFFFFF/FFFFFF.png) | `#FFFFFF` |
| **Primary Accent**     | ![#FF5733](https://via.placeholder.com/20/FF5733/FF5733.png) | `#FF5733` |

### Secondary Colors
Applied for backgrounds, cards, and supporting UI elements.

| Element                | Color Sample            | Hex Code    |
|------------------------|-------------------------|-------------|
| **Secondary Background** | ![#E6E6E6](https://via.placeholder.com/20/E6E6E6/E6E6E6.png) | `#E6E6E6` |
| **Secondary Text**       | ![#333333](https://via.placeholder.com/20/333333/333333.png) | `#333333` |

### Accent Colors
Used sparingly for interactive elements like active states, notifications, and hover effects.

| Element        | Color Sample            | Hex Code    |
|----------------|-------------------------|-------------|
| **Accent 1**   | ![#FFCC00](https://via.placeholder.com/20/FFCC00/FFCC00.png) | `#FFCC00` |
| **Accent 2**   | ![#009688](https://via.placeholder.com/20/009688/009688.png) | `#009688` |

> **Note**: These colors have been chosen for their readability and contrast ratio (4.5:1 or higher), ensuring accessibility across all text and background combinations. For further details on accessibility, see the [Accessibility](#accessibility) section.

---

## Typography

To ensure readability across operating systems, the app uses accessible fonts commonly available on most platforms.

### Font Choices
- **Primary Font**: **Arial**, **Roboto**, or **Helvetica** - These sans-serif fonts are highly readable and widely supported.
- **Fallback Font**: **sans-serif** - Ensures compatibility across systems if primary fonts aren’t available.

### Font Styles and Sizes
To maintain visual hierarchy and readability, font sizes and weights are standardized as follows:

| Element          | Font Example               | Size   | Weight    |
|------------------|----------------------------|--------|-----------|
| **H1**           | Arial, Roboto, or Helvetica | 24px   | Bold      |
| **H2**           | Arial, Roboto, or Helvetica | 20px   | Bold      |
| **H3**           | Arial, Roboto, or Helvetica | 18px   | Medium    |
| **Body Text**    | Arial, Roboto, or Helvetica | 16px   | Regular   |
| **Small Text**   | Arial, Roboto, or Helvetica | 14px   | Light     |

### Example CSS for Typography
```css
h1 {
    font-family: Arial, Roboto, Helvetica, sans-serif;
    font-size: 24px;
    font-weight: bold;
}

p {
    font-family: Arial, Roboto, Helvetica, sans-serif;
    font-size: 16px;
}
```

> **Note**: Use left-aligned text throughout the app for readability and accessibility, with line length kept to a maximum of 80 characters.

---

This style guide is designed to ensure a professional, accessible user experience with visually defined colors and easy-to-read fonts.

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#2563eb",
        secondary: "#64748b",
        accent: "#3b82f6",
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        info: "#06b6d4",
      },
      screens: {
        sxs: "256px",
        xs: "384px",
        sm: "512px", //previously 640px
        md: "768px",
        sd: "896px",
        lg: "1024px",
        "2lg": "1152px",
        xl: "1280px",
        "2xl": "1536px",
      },
      fontFamily: {
        reader: ["Source Serif Pro", "Georgia", "serif"],
        display: [
          "Source Serif Pro",
          "Georgia",
          "Cambria",
          "Times New Roman",
          "serif",
        ],
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "Cascadia Code",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
        brand: [
          "Poppins",
          "Montserrat",
          "SF Pro Display",
          "system-ui",
          "sans-serif",
          "Outfit",
        ],
        handwriting: ["Dancing Script", "Pacifico", "Caveat", "cursive"],
        serif: [
          "Source Serif Pro",
          "Merriweather",
          "Lora",
          "Georgia",
          "Cambria",
          "Times New Roman",
          "serif",
        ],
        sans: [
          "Synonym",
          "Inter",
          "SF Pro Text",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        elegant: ["Playfair Display", "Cormorant Garamond", "Georgia"],
        condensed: [
          "Roboto Condensed",
          "Oswald",
          "Arial Narrow",
          "sans-serif-condensed",
        ],
        code: [
          "JetBrains Mono",
          "Fira Code",
          "Cascadia Code",
          "Source Code Pro",
          "Monaco",
          "Consolas",
          "monospace",
        ],
        "exo-2": ["Exo 2"],
        orbitron: ["Orbitron"],
      },
    },
    extend: {
      boxShadow: {
        "balanced-sm":
          "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
        balanced:
          "0 2px 6px 0 rgba(0, 0, 0, 0.1), 0 1px 3px 0 rgba(0, 0, 0, 0.08)",
        "balanced-md":
          "0 4px 12px 0 rgba(0, 0, 0, 0.1), 0 2px 6px 0 rgba(0, 0, 0, 0.08)",
        "balanced-lg":
          "0 8px 24px 0 rgba(0, 0, 0, 0.1), 0 4px 12px 0 rgba(0, 0, 0, 0.08)",
        "balanced-xl":
          "0 12px 36px 0 rgba(0, 0, 0, 0.1), 0 6px 18px 0 rgba(0, 0, 0, 0.08)",
        "balanced-2xl":
          "0 24px 48px 0 rgba(0, 0, 0, 0.1), 0 12px 24px 0 rgba(0, 0, 0, 0.08)",

        // Even more balanced (centered)
        "centered-sm": "0 0 3px 0 rgba(0, 0, 0, 0.1)",
        centered: "0 0 6px 0 rgba(0, 0, 0, 0.1)",
        "centered-md": "0 0 12px 0 rgba(0, 0, 0, 0.1)",
        "centered-lg": "0 0 24px 0 rgba(0, 0, 0, 0.1)",
        "centered-xl": "0 0 36px 0 rgba(0, 0, 0, 0.15)",

        // Soft balanced shadows
        soft: "0 2px 8px rgba(0, 0, 0, 0.08)",
        "soft-md": "0 4px 16px rgba(0, 0, 0, 0.08)",
        "soft-lg": "0 8px 32px rgba(0, 0, 0, 0.1)",

        // For your message component specifically
        message: "0 2px 8px rgba(0, 0, 0, 0.1)",
        "message-hover": "0 4px 16px rgba(0, 0, 0, 0.12)",
      },
      zIndex: {
        1: "1",
        5: "5",
        10: "10",
        15: "15",
        20: "20",
        25: "25",
        30: "30",
        35: "35",
        40: "40",
        41: "41",
        45: "45",
        51: "51",
      },
    },
  },
  plugins: [],
};

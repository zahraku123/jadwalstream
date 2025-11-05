# Tailwind CSS Build Instructions

This project uses Tailwind CSS standalone CLI for production builds.

## Prerequisites

- Tailwind CSS CLI binary (`tailwindcss.exe`) is included in the project root
- OR install via npm: `npm install -D tailwindcss`

## Build Commands

### Production Build (Minified)
```bash
# Using standalone CLI
.\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css --minify

# OR using npm script
npm run build:css
```

### Development Build (Watch Mode)
```bash
# Using standalone CLI
.\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css --watch

# OR using npm script
npm run watch:css
```

## File Structure

- `static/css/input.css` - Source CSS file with Tailwind directives and custom styles
- `static/css/output.css` - Generated CSS file (production-ready, minified)
- `tailwind.config.js` - Tailwind configuration file
- `tailwindcss.exe` - Standalone Tailwind CSS CLI binary

## Important Notes

1. **Always rebuild CSS after making changes** to:
   - `static/css/input.css`
   - `tailwind.config.js`
   - Template files (if using new Tailwind classes)

2. **The `output.css` file is used in production** - it's already referenced in `templates/base.html`

3. **For development**, use watch mode to automatically rebuild on changes:
   ```bash
   npm run watch:css
   ```

4. **Before deploying to production**, run:
   ```bash
   npm run build:css
   ```

## Troubleshooting

If you see CDN warning in console:
- Make sure `output.css` is built and up-to-date
- Check that `base.html` references the local CSS file, not CDN
- Clear browser cache after rebuilding CSS

---
name: react-app-development-e2e
description: >
  Orchestrates the complete lifecycle of a React application development process, from initial scaffolding and component architecture to state management and production builds. Use this skill when the user says "create a new react app", "build a frontend dashboard", "scaffold a web project with vite", or "help me develop a react feature from scratch". This skill produces a structured React project directory and a production-ready build.
compatibility:
  runtime: Node 18+
  dependencies: vite, react, react-dom, lucide-react, tailwindcss
  env_vars: none
---

# React App Development End to End

This skill provides a standardized, industry-grade workflow for building React applications using Vite, ensuring high performance, clean architecture, and modern styling patterns.

---

## Prerequisites

Node.js and npm must be installed. The agent should verify the environment before starting.

```bash
node -v  # Expected: v18.0.0 or higher
npm -v   # Expected: v9.0.0 or higher
```

---

## Core Concepts

- **Bundling with Vite:** We use Vite instead of Create React App for significantly faster HMR (Hot Module Replacement) and optimized builds.
- **Component-Driven Design:** Applications are broken down into reusable `components`, layout-level `pages`, and logical `hooks`.
- **Functional Components & Hooks:** Strictly use functional components with standard hooks (`useState`, `useEffect`, `useMemo`) for logic.
- **Declarative Styling:** Utility-first CSS (Tailwind) is the preferred method for rapid UI development without writing custom CSS files.

---

## Step-by-Step Instructions

1. **Scaffold the Project** - Initialize the project using the Vite template for React.
   ```bash
   npm create vite@latest my-app -- --template react
   cd my-app
   npm install
   ```

2. **Initialize Styling** - Install and configure Tailwind CSS for modern UI styling.
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

3. **Define Directory Structure** - Create standard folders to maintain clean code separation.
   - `src/components`: For reusable UI atoms/molecules.
   - `src/pages`: For view-level components mapped to routes.
   - `src/hooks`: For custom logic extraction.
   - `src/assets`: For images and global styles.

4. **Implement Navigation** - If the app has multiple views, install and wrap the app in `react-router-dom`.

5. **State Management** - Use local state (`useState`) for simple UI logic or Context API for global state like authentication.

6. **Build for Production** - Generate an optimized static build in the `dist/` folder.
   ```bash
   npm run build
   ```

---

## Full Example

Example of a basic Counter Component with Tailwind styling inside the scaffolded project.

```jsx
// src/components/Counter.jsx
import React, { useState } from 'react';
import { Plus, Minus } from 'lucide-react';

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div className="p-6 max-w-sm mx-auto bg-white rounded-xl shadow-lg flex flex-col items-center gap-4">
      <h2 className="text-xl font-bold">Simple Counter</h2>
      <div className="flex items-center gap-6">
        <button 
          onClick={() => setCount(prev => prev - 1)}
          className="p-2 bg-red-100 text-red-600 rounded-full hover:bg-red-200"
        >
          <Minus size={24} />
        </button>
        <span className="text-3xl font-mono">{count}</span>
        <button 
          onClick={() => setCount(prev => prev + 1)}
          className="p-2 bg-green-100 text-green-600 rounded-full hover:bg-green-200"
        >
          <Plus size={24} />
        </button>
      </div>
    </div>
  );
}
```

---

## Error Handling & Edge Cases

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `npm install` fails | Network issues or cache corruption | Run `npm cache clean --force` and retry |
| White screen in browser | JS Error in root component | Check browser console; ensure `main.jsx` correctly targets the `root` ID |
| Tailwind styles not applying | `content` path missing in config | Update `tailwind.config.js` to include `./src/**/*.{js,ts,jsx,tsx}` |

---

## Output Format

The agent should provide a confirmation message containing:
1. The directory path of the created project.
2. The command to start the development server (`npm run dev`).
3. A summary of the components created.

---

## Test Cases

### Test Case 1 — Happy Path
**Prompt:** "Create a new react app called 'weather-dashboard' with tailwind setup."
**Expected behaviour:** Agent creates directory, runs vite init, installs dependencies, and configures tailwind.config.js.
**Pass criteria:** `weather-dashboard/package.json` exists and `tailwind.config.js` contains the correct glob patterns.

### Test Case 2 — Edge Case
**Prompt:** "Build a react app in a directory that already has files in it."
**Expected behaviour:** Agent warns the user that the directory is not empty and asks for confirmation or suggests a new folder name.
**Pass criteria:** Agent does not overwrite existing files without explicit user consent.

### Test Case 3 — Error Recovery
**Prompt:** "Start a react project but node is version 14."
**Expected behaviour:** Agent checks `node -v`, identifies it is below the requirement (18+), and instructs the user to update Node.js before proceeding.
**Pass criteria:** Execution stops gracefully with a clear upgrade instruction.
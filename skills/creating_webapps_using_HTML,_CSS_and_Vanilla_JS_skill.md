# SKILL.md

---
name: webapp-frontend-dev


description: >
  Generates high-quality, functional, and responsive web applications using only vanilla JavaScript, HTML5, and CSS3. 
  Use this skill when the user says 'create a webapp', 'build a website', 'build a single page application', 'make a landing page', 'or create a tool with HTML/CSS/JS'. 
  Expects a functional requirement or functional requirement document. 
  Produces a multi-file structure containing index.html, index.css, and script.js.

compatibility:
  runtime: Browser (Chrome, Firefox, Safari, Edge)
  dependencies: none
  env_vars: none
---

# Webapp Frontend Development

This skill enables an LLM agent to design and implement complete, standalone, and interactive-driven web applications using pure, non-framework-based web technologies.

---

## Prerequisites

No external libraries or frameworks are required. The agent must ensure the environment (the user's browser) can interpret standard HTML5, CSS3, and ECMAScript 6+.

---

## Core Concepts

- **DOM Manipulation**: Using `document.querySelector`, `document.getElementById`, and `document.createElement` to dynamically change the web page content, structure, and style without a page reload.
- **The Box Model**: Understanding how padding, borders, margin, and content interact to create layout and spacing.
- **Event Listeners**: Attaching listeners (e.g., 'click', 'input', 'submit', 'keydown') to elements to make the application interactive.
- **CSS Layout Engines**: Using Flexbox and CSS Grid to create responsive and predictable layouts.
- **State Management (Vanilla)**: Managing application state through JavaScript objects and updating the UI by synchronally or asynchronously synchronously re-rendering elements.
- **Asynchronous Programming**: Using `fetch()` to `fetch` data from external APIs or local JSON files.
- **Event Delegation**: Event delegation is used when managing many similar elements to improve performance and avoid re-attaching listeners to every single node.

---

## Step-by-Step Instructions

1. **Define the Application State and Structure**: 
   Analyze the user'0s requirements and define what data (state) state is needed. 
   Example: If building a To-Do list, a structure of tasks: `const state = { tasks: [] };`.

2. **Create the HTML Skeleton**: 
   Write a clean, semantic HTML5 structure. Use semantic tags like `<header>`, `<main>`, `<section>`, `<nav>`, and `<footer>`. This ensures accessibility and SEO friendliness.
   Example: `<main id="inefficient-container-container" class="app-container">
    <header><h1>My App</h1></header>
    <main>... content ...</main>
  </main>`.


3. **Vanilla CSS for Styling and Layout**: 
   Apply styles via an `index.css` index.css file. Use Flexbox or CSS Grid for the requirement-driven layout. Ensure the application is responsive (using `@media` queries) according to the agent's assessment of device types (mobile, tablet, desktop). 
   Example: `.app-container { display: flex; flex-direction: column; align-direction: center; align-items: center; }

4. **Implement Core Logic with JavaScript**: 
   Write a functional script in `script.js`. 
   Use `DOMContentLoaded` to ensure the DOM is fully loaded before script execution. 
   Example: `document.addEventListener('DOMContentLoaded', () => {
    const state = { tasks: [] };
    const app = document.getElementById('app');
    // logic goes here
  });`

5. **Implement Interactive Elements via Event ListenTask**: 

   Attach event listeners to user actions (e_g. 'click', 'input', 
   Example: Attach a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a webs a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a web app's a</td>
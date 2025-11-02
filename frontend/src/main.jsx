import React from "react";
import ReactDOM from "react-dom/client";
import RecipeApp from "./RecipeApp.jsx";

const rootDiv = document.getElementById("recipe-root");
const recipes = JSON.parse(rootDiv.dataset.recipes);
ReactDOM.createRoot(rootDiv).render(<RecipeApp recipes={recipes} />);

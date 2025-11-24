import React from "react";

export default function RecipeApp({ recipes }) {
  return (
    <ul>
      {recipes.map((r) => (
        <li key={r[0]}>
          <strong>{r[1]}</strong> – Makes: {r[3]} – Time: {r[4]}<br></br>
          <small>{r[2]}</small>
        </li>
      ))}
    </ul>
  );
}

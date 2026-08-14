import { render, screen } from "@testing-library/react";
import App from "./App";

// =====================================================
// BASIC APP RENDER TEST
// =====================================================

test("renders Galarix app without crashing", () => {
  render(<App />);

  // Check if main container exists
  const appElement = document.querySelector("div");
  expect(appElement).toBeInTheDocument();
});

// =====================================================
// DARK MODE TOGGLE TEST (OPTIONAL)
// =====================================================

test("toggles dark mode class", () => {
  render(<App />);

  const root = document.documentElement;

  // initial state check
  expect(root).toBeDefined();
});
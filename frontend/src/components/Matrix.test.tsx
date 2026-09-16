import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Matrix } from "./Matrix";

describe("Matrix", () => {
  it("labels both axes and names every cell", () => {
    render(
      <Matrix
        values={[
          [10, 2],
          [0, 40],
        ]}
        labels={["Trees", "Water"]}
        titles={["Tree cover", "Permanent water"]}
        caption="Transition matrix"
        rowAxis="From"
        columnAxis="To"
        describe={(from, to, value) => `${from} to ${to}: ${value} pixels`}
      />,
    );

    expect(screen.getByRole("table", { name: "Transition matrix" })).toBeInTheDocument();
    expect(screen.getByText("From")).toBeInTheDocument();
    expect(screen.getByText("To")).toBeInTheDocument();
    // A swatch alone would leave this cell unreadable.
    expect(screen.getByText("Tree cover to Permanent water: 2 pixels")).toBeInTheDocument();
    expect(screen.getAllByRole("columnheader")).toHaveLength(3);
    expect(screen.getAllByRole("rowheader")).toHaveLength(2);
  });
});

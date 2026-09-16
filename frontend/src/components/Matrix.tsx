interface MatrixProps {
  values: number[][];
  /** Short labels drawn on both axes, in class order. */
  labels: string[];
  /** Full class names, used for the accessible name of every cell. */
  titles: string[];
  caption: string;
  rowAxis: string;
  columnAxis: string;
  describe: (from: string, to: string, value: number) => string;
}

/**
 * A square class-by-class matrix with both axes labelled.
 *
 * The colour swatch alone cannot carry the axis: a reader would have to match
 * seven greens against a legend elsewhere on the page to know what a cell means.
 */
export function Matrix({ values, labels, titles, caption, rowAxis, columnAxis, describe }: MatrixProps) {
  const maximum = Math.max(...values.flat(), 1);
  return (
    <div className="matrix" role="table" aria-label={caption} style={{ "--matrix-size": labels.length } as React.CSSProperties}>
      <div className="matrix__row" role="row">
        <div className="matrix__corner" role="columnheader">
          <span className="matrix__axis matrix__axis--row">{rowAxis}</span>
          <span className="matrix__axis matrix__axis--column">{columnAxis}</span>
        </div>
        {labels.map((label, index) => (
          <div className="matrix__head matrix__head--column" role="columnheader" key={`column-${label}`}>
            <span className="matrix__head-label" title={titles[index]}>
              {label}
            </span>
            <span className={`class-swatch class-swatch--${index}`} aria-hidden="true" />
          </div>
        ))}
      </div>
      {values.map((row, rowIndex) => (
        <div className="matrix__row" role="row" key={`row-${labels[rowIndex]}`}>
          <div className="matrix__head matrix__head--row" role="rowheader">
            <span className={`class-swatch class-swatch--${rowIndex}`} aria-hidden="true" />
            <span className="matrix__head-label" title={titles[rowIndex]}>
              {labels[rowIndex]}
            </span>
          </div>
          {row.map((value, columnIndex) => (
            <div
              className="matrix__cell"
              role="cell"
              key={`${rowIndex}-${columnIndex}`}
              data-diagonal={rowIndex === columnIndex}
              style={{ "--intensity": Math.sqrt(value / maximum) } as React.CSSProperties}
              title={describe(titles[rowIndex], titles[columnIndex], value)}
            >
              <span className="visually-hidden">{describe(titles[rowIndex], titles[columnIndex], value)}</span>
              <span aria-hidden="true">{value > maximum * 0.04 ? compactNumber(value) : ""}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export function compactNumber(value: number): string {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

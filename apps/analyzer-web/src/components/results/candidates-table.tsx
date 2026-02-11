interface CandidatesTableProps {
  columns: string[];
  rows: string[][];
  "data-testid"?: string;
}

export function CandidatesTable({ columns, rows, ...props }: CandidatesTableProps) {
  return (
    <div className="overflow-x-auto" data-testid={props["data-testid"]}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th
                key={col}
                className="text-left py-2 pr-4 text-text-secondary font-medium"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-border/50">
              {row.map((cell, j) => (
                <td key={j} className="py-1.5 pr-4 text-text-primary">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

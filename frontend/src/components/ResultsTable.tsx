import { Link } from "react-router-dom";
import type { Lender, Verification } from "../types/api";
import { Badge, Score, Timestamp } from "./ui";

export default function ResultsTable({
  results,
  lenders,
}: {
  results: Verification[];
  lenders: Lender[];
}) {
  const names = new Map(lenders.map((lender) => [lender.id, lender.name]));
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Lender / result</th>
            <th>Verification</th>
            <th>Confidence</th>
            <th>Analysis</th>
            <th>Review</th>
            <th>Checked</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr key={result.id}>
              <td>
                <Link
                  className="table-name"
                  to={`/lenders/${result.lender_id}?result=${result.id}`}
                >
                  {names.get(result.lender_id) ||
                    result.lender_name ||
                    `Lender ${result.lender_id}`}
                </Link>
                <small>Result #{result.id}</small>
              </td>
              <td>
                <Badge value={result.status} />
              </td>
              <td>
                <Score value={result.confidence_score} />
              </td>
              <td>
                <Badge value={result.ai_status} />
              </td>
              <td>
                <Badge value={result.review_status} />
              </td>
              <td>
                <Timestamp value={result.checked_at} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

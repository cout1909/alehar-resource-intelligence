import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { ErrorState } from "./ui";
import type { Verification } from "../types/api";

export interface ReviewSelection {
  result: Verification;
  action: "approve" | "reject";
}
export default function ReviewDialog({
  selection,
  onClose,
  onDone,
}: {
  selection: ReviewSelection;
  onClose: () => void;
  onDone: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      await api.review(selection.result.id, selection.action, note);
      onDone();
    } catch (reason) {
      setError((reason as Error).message);
      setBusy(false);
    }
  };
  return (
    <dialog
      ref={dialog}
      className="review-dialog"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="eyebrow">
        HUMAN REVIEW · RESULT #{selection.result.id}
      </div>
      <h2>
        {selection.action === "approve"
          ? "Approve this finding?"
          : "Reject this finding?"}
      </h2>
      <p>
        This records your decision about the verification finding. It does not
        change lender data or certify financial accuracy.
      </p>
      <label htmlFor="review-note">
        Reviewer note <span className="muted">(optional)</span>
      </label>
      <textarea
        id="review-note"
        rows={4}
        maxLength={2000}
        value={note}
        disabled={busy}
        onChange={(event) => setNote(event.target.value)}
        placeholder="Add context for future reviewers…"
      />
      {error && <ErrorState message={error} />}
      <div className="dialog-actions">
        <button className="button secondary" disabled={busy} onClick={onClose}>
          Cancel
        </button>
        <button
          className={`button ${selection.action === "reject" ? "danger" : ""}`}
          disabled={busy}
          onClick={submit}
        >
          {busy ? "Saving decision…" : `Confirm ${selection.action}`}
        </button>
      </div>
    </dialog>
  );
}

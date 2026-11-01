export default function ErrorState({ message }) {
  return (
    <div className="card error">
      {message || "Unable to load this view."}
    </div>
  );
}

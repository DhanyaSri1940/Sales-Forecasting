export default function Header({ kicker = "Workspace", title, subtitle, extra }) {
  return (
    <div className="header">
      <div>
        <p className="kicker">{kicker}</p>
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {extra}
    </div>
  );
}

export default function FilterToolbar({ fields, trailing }) {
  return (
    <div className="toolbar">
      {fields.map((field) => (
        <label key={field.key} className="filter-field">
          <span>{field.label}</span>
          <select value={field.value} onChange={field.onChange}>
            <option value="">{field.placeholder}</option>
            {field.options.map((option) => {
              const value = typeof option === "object" ? option.value : option;
              const label = typeof option === "object" ? option.label : option;
              return <option key={value} value={value}>{label}</option>;
            })}
          </select>
        </label>
      ))}
      {trailing}
    </div>
  );
}

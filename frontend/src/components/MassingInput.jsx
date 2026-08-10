import "./MassingInput.css";

export function MassingInput ({ onSubmit, setPoints, constraint, setConstraint, error, setError}) {
  const onChangePoints = (e) => {
    setError({...error, points: ""});
    const number = /\s*[0-9]+(\.[0-9]+)?\s*/;
    const pair = RegExp("\\s*\\[" + number.source + "," + number.source + "\\]\\s*");
    const coordRegex = RegExp("^" + "\s*\\[" + pair.source + "(," + pair.source + ")*" +"\\]\\s*$", "g");
    if (!coordRegex.test(e.target.value)) {
      setError({...error, points: "invalid input: check the formatting"});
      return;
    }
    setPoints(JSON.parse(e.target.value));
  };
  
  const onChangeConstraint = (name) => (e) => {
    setConstraint((constraint) => ({...constraint, [name]: Number(e.target.value)}));
  };

  
  return (
    <form onSubmit={onSubmit} className="form-column">
      <div className="form-row">
        <label className="form-label">Polygon points</label>
        <input className="form-input" type="text" onChange={onChangePoints}/>
        <label className="form-error">{error["points"]}</label>
      </div>
      {Object.keys(constraint).map(name =>
        <div className="form-row">
          <label className="form-label">{name}</label>
          <input className="form-input" type="number" key={name} onChange={onChangeConstraint(name)}/>
        </div>
      )}
      <button type="submit" className="form-row">Calculate Massing</button>
    </form>
  );
}

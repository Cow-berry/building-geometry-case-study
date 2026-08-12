import { useEffect, useState } from "react";
import { getHealth } from "./api.js";
import { MassingInput } from "./components/MassingInput.jsx";
import { MassingVisualization } from "./components/MassingVisualization.jsx";
import { createMassing, getAllMassings, ensureDB, purgeDB } from "./api.js";

export default function App() {
  const initConstraint = {
    setback: null,
    max_height: null,
    max_floor_count: null,
    floor_height: null,
    site_coverage_ratio: null,
    max_footprint_area: null,
    gfa_target: null,
    far_target: null};
  
  const [health, setHealth] = useState("checking…");
  const [constraint, setConstraint] = useState(initConstraint);
  const [error, setError] = useState({...initConstraint, points: null, massing: null});
  const [points, setPoints] = useState([]);
  const [allMassings, setAllMassings] = useState(null);
  const [currentId, setCurrentId] = useState(null);

  const updateAllMassing = async (id) => {
    let newAllMassings = await getAllMassings();
    
    newAllMassings = Object.fromEntries(newAllMassings.map(massing => [massing.id, massing]));
    for (const id in newAllMassings) {
      const massing = newAllMassings[id];
      const parentId = massing["parentid"];
      massing["children"] = [];
      massing["parentMassing"] = parentId === null ? null : newAllMassings[parentId];
      console.log(parentId, massing, newAllMassings);
    }
    for (const id in newAllMassings) {
      const massing = newAllMassings[id];
      const parent = massing["parentMassing"];
      if (parent !== null) {
        parent["children"].push(massing);
      }
    }

    console.log(newAllMassings);
    
    setAllMassings(newAllMassings);
    if (id !== null) {
      setCurrentId(id);
    } else {
      const entries = Object.entries(newAllMassings);
      if (entries.length == 0) {
        setCurrentId(null);
      } else {
        setCurrentId(entries[entries.length - 1][0]);
      }
    }
  };
  
  const onSubmit = async (e) => {
    e.preventDefault();
    await ensureDB();
    const result = await createMassing(points, constraint, currentId);

    if (result[0] === null) {
      setError({...error, massing: result[1]});
      return;
    }

    const [massing, id] = result;
    await updateAllMassing(id);
  };

  const onPurgeDatabase = async (e) => {
    // e.preventDefault();
    if (!confirm("Do you want to delete all saved massings?")) return;
    await purgeDB();
    await updateAllMassing(null);
  };

  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data.status))
      .catch((err) => setHealth(`unreachable (${err.message})`));
    updateAllMassing(null);
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem", lineHeight: 1.5 }}>
      <h1>Building Geometry Case Study</h1>
      <p>
        Backend health: <strong>{health}</strong>
      </p>
      <MassingInput
        onSubmit={onSubmit}
        setPoints={setPoints}
        constraint={constraint}
        setConstraint={setConstraint}
        error={error}
        setError={setError}/>
      <section
        style={{
          marginTop: "1.5rem",
          border: "2px dashed #bbb",
          borderRadius: 8,
          padding: "2rem",
          color: "#666",
        }}
      >
        <MassingVisualization
          points={points}
          allMassings={allMassings}
          currentId={currentId}
          setCurrentId={setCurrentId}
          setPoints={setPoints}
          constraint={constraint}
          setConstraint={setConstraint}
        />
      </section>
      <form><button type="submit" onClick={onPurgeDatabase}>DELETE ALL DECISION</button></form>
    </main>
  );
}

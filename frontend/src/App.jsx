import { useEffect, useState } from "react";
import { getHealth } from "./api.js";
import { MassingInput } from "./components/MassingInput.jsx";
import { MassingVisualization } from "./components/MassingVisualization.jsx";
import { createMassing, getAllMassings, ensureDB } from "./api.js";

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
  const [allMassings, setAllMassings] = useState([]);
  const [currentId, setCurrentId] = useState(-1);
  
  const onSubmit = async (e) => {
    e.preventDefault();
    await ensureDB();
    const result = await createMassing(points, constraint, null);

    if (result[0] === null) {
      setError({...error, massing: result[1]});
      return;
    }

    const [massing, id] = result;
    setCurrentId(id);

    const allMassings = await getAllMassings();
    setAllMassings(allMassings);
    console.log("All massings: ", allMassings);
   };

  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data.status))
      .catch((err) => setHealth(`unreachable (${err.message})`));
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
        />
        {/* TODO(candidate): build the visualization here.
            Render the site polygon, the buildable footprint, the resulting massing,
            and the metrics. Let the user create options, branch them, and navigate
            the decision tree. Pick whatever rendering approach you can justify
            (2D canvas/SVG, 3D via three.js, …). Sample sites live in ../data/sites/. */}
        Visualization goes here.
      </section>
    </main>
  );
}

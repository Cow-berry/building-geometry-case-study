import "./MassingVisualization.css";
import { useState, useEffect } from "react";
import { drawFootprint, drawBuilding } from "./visualization.js";
import { DecisionTree } from "./DecisionTree.jsx";


export function getCurrentMassing(allMassings, currentId) {
  if (currentId === null || allMassings === null) return null;
  return allMassings[currentId];
}

import "./MassingVisualization.css";

export function MassingVisualization ({ points, allMassings, currentId, setCurrentId, setPoints, constraint, setConstraint }) {
  const [rotation, setRotation] = useState(Math.PI);

  useEffect(() => {
    const massing = getCurrentMassing(allMassings, currentId);
    if (massing === null) return;
    drawFootprint("polygon", points, massing.result.footprint_points);
    drawBuilding("building", massing, rotation);
  }, [allMassings, currentId, rotation]);
  
  

  useEffect(() => {
    let footprint = null;
    const massing = getCurrentMassing(allMassings, currentId);
    if (massing !== null && massing.polygon.points === points) {
      const {id: _, ...massingConstraint} = massing.constraint;
      if (Object.keys(massingConstraint).every((key) => massingConstraint[key] === constraint[key])) {
        footprint = massing.result.footprint_points;
      }
    }
    drawFootprint("polygon", points, footprint);
  }, [points]);
  
  
  return (
    <div className="canvas-row">
      <div className="canvas-column">
        <input type="range" min={0} max={2*Math.PI} step="any" onChange={(e) => setRotation(e.target.value)} className="slider"/>
        <canvas id ="building" width="200" height="400"> </canvas>
      </div>
      <div className="canvas-column">
        <canvas id ="polygon"> </canvas>
        <table>
          <tbody>
          {currentId !== null && allMassings !== null && Object.entries(allMassings[currentId].result).map(([k, v], i) => k !== "footprint_points" &&
            <tr>
              <td>{k}</td>
              <td>{v.toFixed(2)}</td>
            </tr>
          )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

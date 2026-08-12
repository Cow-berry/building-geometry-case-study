import "./DecisionTree.css";
import { useEffect } from "react";
import { drawFootprint } from "./visualization.js";
import { getCurrentMassing } from "./MassingVisualization.jsx";


function getItem(object, indexPath, precision) {
  for (let index of indexPath.split('.')) {
    object = object[index];
  }
  return object.toFixed(precision);
}


function getParents(object) {
  let parents = [object];
  while (object.parentMassing !== null) {
    parents.push(object.parentMassing);
    object = object.parentMassing;
  }
  parents.reverse();
  return parents;
}



function DecisionTable({decisions, canvasId, onRowClick, currentId, title}) {
  const P = 2;
  
  const tableConfig = [
    ["id", "id", "", 0],
    ["result.footprint_area", "footprint", "m²", P],
    ["result.setback", "setback", "m", P],
    ["result.site_coverage_ratio", "coverage", "%", P],
    ["result.gfa", "GFA", "m²", P],
    ["result.height", "height", "m", P],
    ["result.floor_count", "floors", "", 0],
    ["children.length", "children", "", 0],
  ];
  
  return (
    <table>
      <thead>
        <tr>
          <th colSpan={100} className="title" >{title}</th>
        </tr>
        <tr>
          {tableConfig.map((item) =>
            <th>{item[1]}</th>
          )}
          <th>polygon</th>
        </tr>
      </thead>
      <tbody>
        {decisions.map((massing) =>
          <tr onClick={onRowClick(massing.id)} className={massing.id === currentId ? "current" : ""}>
            {tableConfig.map((item) =>
              <td>{getItem(massing, item[0], item[3])} {item[2]}</td>
            )}
            <td>
              <canvas className="table-canvas" id={`${canvasId}-${massing.id}`} width="25" height="25"/>
            </td>
          </tr>
        )}
      </tbody>
    </table>);
}


export function DecisionTree({ allMassings, currentId, setCurrentId, setPoints, setConstraint }) {
  const decisionSetup = [
    [() => getParents(allMassings[currentId]), "parents"],
    [() => allMassings[currentId].children, "children"],
  ];
  useEffect(() => {
    decisionSetup.map(([decisions, name]) => {
      allMassings !== null && decisions().map((massing) => {
        drawFootprint(`${name}-${massing.id}`, massing.polygon.points, massing.result.footprint_points);
      });      
    }, []);
  }, [allMassings, currentId]);

  const onRowClick = (id) => () => {
    setCurrentId(id);
  };

  return (
    <div>
      <DecisionTable
        canvasId="parents"
        onRowClick={onRowClick}
        currentId={currentId}
        decisions={allMassings && currentId ? getParents(allMassings[currentId]) : []}
        title="Current massing and it's predessessors"
      />
      <DecisionTable
        canvasId="children"
        onRowClick={onRowClick}
        currentId={currentId}
        decisions={allMassings && currentId ? allMassings[currentId].children : []}
        title="Direct children of the current massing"
      />
    </div>
  );
}

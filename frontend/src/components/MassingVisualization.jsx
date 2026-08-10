import "./MassingVisualization.css";
import { useState, useEffect } from "react";

function getAdjust(canvas, points) {
  let minX = 0, minY = 0, maxX = 0, maxY = 0;
  if (points.legth > 0) {
    [minX, minY] = points[0];
    [maxX, maxY] = points[0];
  }
  
  points.map(([x, y]) => {
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  });

  const scaleX = maxX - minX == 0 ? 1 : canvas.width/(maxX-minX);
  const scaleY = maxY - minY == 0 ? 1 : canvas.height/(maxY-minY);
  const scale = Math.min(scaleX, scaleY);
  return ([x, y]) => [(x - minX) * scale, canvas.height - (y - minY) * scale];
}

function drawPolygon(ctx, points, adjust) {
  if (points.length < 3) return;
  if (adjust !== null) points = points.map(adjust);
  ctx.beginPath();
  [...points, points[0]].map((coord) => {
    const [x, y] = coord;
    ctx.lineTo(x, y);
  });
  ctx.fill();
  ctx.stroke();
}

function drawFootprint(canvasName, points, footprint) {
  const canvas = document.getElementById(canvasName);
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (points.length < 3) return;
  
  const adjust = getAdjust(canvas, points);

  ctx.strokeStyle = "#000000";
  ctx.fillStyle = "#ff686b";
  drawPolygon(ctx, points, adjust);
    
  if (footprint === null || footprint.length < 3) return; 
  ctx.fillStyle = "#a5ffd6";
  drawPolygon(ctx, footprint, adjust);
}

function rotatePolygon(points, rotation) {
  if (points.length < 3) return points;
  let cx=0;
  let cy=0;
  for (let point of points) {
    const [x, y] = point;
    cx += x;
    cy += y;
  }
  cx /= points.length;
  cy /= points.length;


  const cr = Math.cos(rotation);
  const sr = Math.sin(rotation);

  points = points.map(([x,y]) => [cx-x, cy-y]);
  points = points.map(([x,y]) => [x*cr - y*sr, x*sr + y*cr]);
  points = points.map(([x,y]) => [cx-x, cy-y]);
  return points;
}

function drawBuilding(canvasName, massing, rotation) {
  const canvas = document.getElementById(canvasName);
  const ctx = canvas.getContext("2d");
  ctx.globalAlpha = 0.5;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#a5ffd6";
  ctx.strokeStyle = "#000000";

  

  const footprint = rotatePolygon(massing.result.footprint_points, rotation);
  let points = [
    ...footprint.map(([x, y]) => [x, 0, y]),
    ...footprint.map(([x, y]) => [x, massing.result.height, y])];

  points = points.map(([x, y, z]) => [(x-z)/Math.sqrt(2), (-x+2*y-z)/Math.sqrt(6)]);
  const adjust = getAdjust(canvas, points);
  points = points.map(adjust);

  const middle = points.length / 2;

  let low = points.splice(0, middle);
  let high = points;
  drawPolygon(ctx, low, null);
  drawPolygon(ctx, high, null);

  low = [...low, low[0]];
  high = [...high, high[0]];
  for (let i = 0; i < low.length-1; i++) {
    drawPolygon(ctx, [low[i], high[i], high[i+1], low[i+1]], null);
  }

}

function getCurrentMassing(allMassings, currentId) {
  if (currentId === null || allMassings === null) return null;
  allMassings = allMassings.filter((massing) => massing.id == currentId);
  if (allMassings.length === 0) return null;
  return allMassings[0];
}

export function MassingVisualization ({points, allMassings, currentId}) {
  const [rotation, setRotation] = useState(Math.PI);

  useEffect(() => {
    const massing = getCurrentMassing(allMassings, currentId);
    if (massing === null) return;
    drawFootprint("polygon", points, massing.result.footprint_points);
    drawBuilding("building", massing, rotation);
  }, [allMassings, currentId, rotation]);
  
  
  useEffect(() => {
    drawFootprint("polygon", points, null);
  }, [points]);

  

  
  
  return (
    <div className="canvas-row">
      <canvas id ="polygon"> </canvas>
      <canvas id ="building"> </canvas>
      <input type="range" min={0} max={2*Math.PI} step="any" onChange={(e) => setRotation(e.target.value)} className="slider"/>
    </div>
  );
}
